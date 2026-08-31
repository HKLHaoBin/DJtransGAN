"""FastAPI Mix Studio — wraps DJtransGAN inference for the Vue frontend."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from server.engine import generator_status, load_generator
from server.jobs import ALLOWED_SUFFIXES, MAX_UPLOAD_BYTES, manager
from server.paths import DEMO_SITE, ensure_runtime_env, rubberband_available, rubberband_path

ensure_runtime_env()

app = FastAPI(title="DJtransGAN Mix Studio", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_GROUPS = [
    {"id": "A", "index": 1, "category": "nv-nv", "label": "non-vocal → non-vocal"},
    {"id": "B", "index": 2, "category": "nv-nv", "label": "non-vocal → non-vocal"},
    {"id": "C", "index": 3, "category": "nv-v", "label": "non-vocal → vocal"},
    {"id": "D", "index": 4, "category": "nv-v", "label": "non-vocal → vocal"},
    {"id": "E", "index": 5, "category": "v-nv", "label": "vocal → non-vocal"},
    {"id": "F", "index": 6, "category": "v-nv", "label": "vocal → non-vocal"},
    {"id": "G", "index": 7, "category": "v-v", "label": "vocal → vocal"},
    {"id": "H", "index": 8, "category": "v-v", "label": "vocal → vocal"},
]
DEMO_TRACKS = ["prev", "next", "sum", "linear", "rule", "gan", "human"]


@app.on_event("startup")
def _startup() -> None:
    ensure_runtime_env()

    def _load() -> None:
        try:
            load_generator(download=True)
            print("[Mix Studio] generator ready")
        except Exception as exc:  # noqa: BLE001
            print(f"[Mix Studio] model load deferred/failed: {exc}")

    threading.Thread(target=_load, name="model-loader", daemon=True).start()


@app.get("/api/health")
def health():
    ensure_runtime_env()
    g = generator_status()
    rb = rubberband_available()
    return {
        "ok": bool(g.get("loaded")) and rb,
        "model": g,
        "rubberband": {
            "available": rb,
            "path": rubberband_path(),
        },
        "limits": {
            "max_upload_mb": MAX_UPLOAD_BYTES // (1024 * 1024),
            "allowed_suffixes": sorted(ALLOWED_SUFFIXES),
        },
    }


@app.get("/api/demo/groups")
def demo_groups():
    return {
        "groups": DEMO_GROUPS,
        "tracks": DEMO_TRACKS,
        "track_labels": {
            "prev": "Prev",
            "next": "Next",
            "sum": "Sum",
            "linear": "Linear",
            "rule": "Rule",
            "gan": "GAN",
            "human": "Human",
        },
    }


@app.get("/api/demo/audio/{index}/{name}")
def demo_audio(index: int, name: str):
    if index < 1 or index > 8:
        raise HTTPException(404, "group not found")
    stem = name.lower().removesuffix(".wav")
    if stem not in DEMO_TRACKS:
        raise HTTPException(404, "track not found")
    path = DEMO_SITE / "assets" / "audios" / str(index) / f"{stem}.wav"
    if not path.is_file():
        raise HTTPException(404, f"missing {path.name}")
    return FileResponse(path, media_type="audio/wav", filename=f"{index}_{stem}.wav")


@app.post("/api/jobs", status_code=202)
async def create_job(
    prev: UploadFile = File(...),
    next: UploadFile = File(...),
    prev_cue: float = Form(96.0),
    next_cue: float = Form(30.0),
    match_bpm: bool = Form(False),
    align_cue: bool = Form(True),
):
    prev_bytes = await prev.read()
    next_bytes = await next.read()
    try:
        job = manager.enqueue(
            prev_bytes,
            next_bytes,
            prev.filename or "prev.wav",
            next.filename or "next.wav",
            float(prev_cue),
            float(next_cue),
            match_bpm=bool(match_bpm),
            align_cue=bool(align_cue),
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return JSONResponse(status_code=202, content=job.to_dict())


@app.get("/api/jobs")
def list_jobs():
    return {"jobs": manager.list_done()}


@app.get("/api/jobs/latest")
def latest_job():
    job_id = manager.latest_done_id()
    if not job_id:
        raise HTTPException(404, "no finished jobs on disk")
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job.to_dict()


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job.to_dict()


@app.get("/api/jobs/{job_id}/audio/{kind}")
def get_job_audio(job_id: str, kind: str):
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    if job.status != "done":
        raise HTTPException(409, f"job not ready ({job.status})")
    key = {"short": "short_path", "full": "full_path"}.get(kind)
    if not key:
        raise HTTPException(404, "kind must be short or full")
    path = Path(job.created_paths.get(key, ""))
    if not path.is_file():
        raise HTTPException(404, "audio missing")
    return FileResponse(path, media_type="audio/wav", filename=path.name)


@app.get("/api/jobs/{job_id}/params")
def get_job_params(job_id: str):
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    if job.status != "done":
        raise HTTPException(409, f"job not ready ({job.status})")
    path = Path(job.created_paths.get("params_path", ""))
    if not path.is_file():
        raise HTTPException(404, "params missing")
    return json.loads(path.read_text(encoding="utf-8"))
