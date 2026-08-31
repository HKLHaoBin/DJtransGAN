"""Async job queue for Mix Studio (one mix at a time)."""

from __future__ import annotations

import json
import threading
import traceback
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from server.engine import run_mix
from server.paths import JOBS_DIR

MAX_UPLOAD_BYTES = 80 * 1024 * 1024
ALLOWED_SUFFIXES = {".wav", ".flac", ".ogg", ".mp3", ".m4a", ".aac"}


@dataclass
class Job:
    id: str
    status: str = "queued"  # queued | running | done | error
    step: int = 0
    total: int = 7
    message: str = "Queued"
    error: Optional[str] = None
    meta: dict = field(default_factory=dict)
    post_cue: list = field(default_factory=list)
    created_paths: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "step": self.step,
            "total": self.total,
            "message": self.message,
            "error": self.error,
            "meta": self.meta,
            "post_cue": self.post_cue,
            "has_short": (Path(self.created_paths.get("short_path", "")).is_file()
                          if self.created_paths else False),
            "has_full": (Path(self.created_paths.get("full_path", "")).is_file()
                         if self.created_paths else False),
            "has_params": (Path(self.created_paths.get("params_path", "")).is_file()
                           if self.created_paths else False),
        }


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._queue: list[str] = []
        self._lock = threading.Lock()
        self._worker: Optional[threading.Thread] = None
        self._running_id: Optional[str] = None

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            hit = self._jobs.get(job_id)
        if hit is not None:
            return hit
        return self._hydrate_from_disk(job_id)

    def job_dir(self, job_id: str) -> Path:
        return JOBS_DIR / job_id

    def _hydrate_from_disk(self, job_id: str) -> Optional[Job]:
        """Rebuild a finished job from results/web-jobs/{id}/ after process restart."""
        if not job_id or "/" in job_id or "\\" in job_id or ".." in job_id:
            return None
        jdir = self.job_dir(job_id)
        short = jdir / "short.wav"
        full = jdir / "full.wav"
        params = jdir / "params.json"
        if not (short.is_file() and full.is_file()):
            return None
        job = Job(id=job_id, status="done", step=7, total=7, message="Done (from disk)")
        job.created_paths = {
            "short_path": str(short),
            "full_path": str(full),
            "params_path": str(params) if params.is_file() else "",
        }
        if params.is_file():
            try:
                data = json.loads(params.read_text(encoding="utf-8"))
                job.meta = data.get("meta") or {}
                job.post_cue = data.get("post_cue") or []
            except Exception:
                pass
        with self._lock:
            self._jobs[job_id] = job
        return job

    def latest_done_id(self) -> Optional[str]:
        items = self.list_done()
        return items[0]["id"] if items else None

    def list_done(self) -> list[dict]:
        """Finished mixes on disk, newest first."""
        if not JOBS_DIR.is_dir():
            return []
        items: list[dict] = []
        for child in JOBS_DIR.iterdir():
            if not child.is_dir():
                continue
            short = child / "short.wav"
            full = child / "full.wav"
            params = child / "params.json"
            if not (short.is_file() and full.is_file()):
                continue
            entry: dict = {
                "id": child.name,
                "status": "done",
                "mtime": short.stat().st_mtime,
                "short_bytes": short.stat().st_size,
                "full_bytes": full.stat().st_size,
                "has_short": True,
                "has_full": True,
                "has_params": params.is_file(),
                "sources": {},
                "meta": {},
                "post_cue": [],
            }
            if params.is_file():
                try:
                    data = json.loads(params.read_text(encoding="utf-8"))
                    entry["meta"] = data.get("meta") or {}
                    entry["post_cue"] = data.get("post_cue") or []
                    entry["sources"] = data.get("sources") or {}
                except Exception:
                    pass
            items.append(entry)
        items.sort(key=lambda x: x["mtime"], reverse=True)
        return items

    def enqueue(
        self,
        prev_bytes: bytes,
        next_bytes: bytes,
        prev_name: str,
        next_name: str,
        prev_cue: float,
        next_cue: float,
        *,
        match_bpm: bool = False,
        align_cue: bool = True,
    ) -> Job:
        if len(prev_bytes) > MAX_UPLOAD_BYTES or len(next_bytes) > MAX_UPLOAD_BYTES:
            raise ValueError(f"file too large (max {MAX_UPLOAD_BYTES // (1024*1024)} MB)")

        prev_suf = Path(prev_name).suffix.lower() or ".wav"
        next_suf = Path(next_name).suffix.lower() or ".wav"
        if prev_suf not in ALLOWED_SUFFIXES or next_suf not in ALLOWED_SUFFIXES:
            raise ValueError(f"unsupported audio type (allowed: {sorted(ALLOWED_SUFFIXES)})")

        job_id = uuid.uuid4().hex[:12]
        jdir = self.job_dir(job_id)
        jdir.mkdir(parents=True, exist_ok=True)
        prev_path = jdir / f"prev{prev_suf}"
        next_path = jdir / f"next{next_suf}"
        prev_path.write_bytes(prev_bytes)
        next_path.write_bytes(next_bytes)

        job = Job(id=job_id, message="Queued")
        job.created_paths = {
            "prev_path": str(prev_path),
            "next_path": str(next_path),
            "prev_cue": prev_cue,
            "next_cue": next_cue,
            "match_bpm": bool(match_bpm),
            "align_cue": bool(align_cue),
        }
        with self._lock:
            self._jobs[job_id] = job
            self._queue.append(job_id)
            self._ensure_worker()
        return job

    def _ensure_worker(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._worker = threading.Thread(target=self._loop, name="mix-worker", daemon=True)
        self._worker.start()

    def _loop(self) -> None:
        while True:
            with self._lock:
                if not self._queue:
                    self._running_id = None
                    return
                job_id = self._queue.pop(0)
                job = self._jobs[job_id]
                self._running_id = job_id
                job.status = "running"
                job.message = "Starting ..."

            try:
                self._run_one(job)
            except Exception as exc:  # noqa: BLE001 — surface to client
                job.status = "error"
                job.error = f"{exc}\n{traceback.format_exc()}"
                job.message = "Failed"

    def _run_one(self, job: Job) -> None:
        paths = job.created_paths
        out_dir = self.job_dir(job.id)

        def on_progress(step: int, total: int, message: str) -> None:
            job.step = step
            job.total = total
            job.message = message

        result = run_mix(
            paths["prev_path"],
            paths["next_path"],
            float(paths["prev_cue"]),
            float(paths["next_cue"]),
            out_dir,
            on_progress=on_progress,
            match_bpm=bool(paths.get("match_bpm", False)),
            align_cue=bool(paths.get("align_cue", True)),
        )
        job.created_paths.update(result)
        job.meta = result.get("meta") or {}
        job.post_cue = result.get("post_cue") or []
        job.status = "done"
        job.message = "Done"
        job.step = job.total


manager = JobManager()
