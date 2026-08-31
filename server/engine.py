"""Reusable DJtransGAN inference engine (shared by CLI and FastAPI)."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np
import torch

from server.paths import (
    CODE_DIR,
    DEFAULT_WEIGHTS,
    PRETRAINED_DIR,
    ensure_runtime_env,
)

ProgressCb = Callable[[int, int, str], None]

_lock = threading.Lock()
_generator = None
_weights_path: Optional[Path] = None
_loaded = False
_load_error: Optional[str] = None

# Overall pipeline steps reported to the UI (preprocess 1-5 + mix + save).
PIPELINE_TOTAL = 7


def _noop_progress(step: int, total: int, message: str) -> None:
    pass


def _map_preprocess_progress(on_progress: ProgressCb) -> ProgressCb:
    """Map preprocess's local 1..5 onto the global 1..7 pipeline."""

    def wrapped(step: int, total: int, message: str) -> None:
        on_progress(step, PIPELINE_TOTAL, message)

    return wrapped


def ensure_pretrained(download: bool = True) -> Path:
    """Ensure default weights exist under code/pretrained/."""
    ensure_runtime_env()
    # download helpers write relative to cwd
    cwd = Path.cwd()
    try:
        os_chdir = __import__("os").chdir
        os_chdir(CODE_DIR)
        from djtransgan.utils import download_pretrained

        weights = DEFAULT_WEIGHTS
        if not weights.is_file() and download:
            download_pretrained()
        return weights
    finally:
        __import__("os").chdir(cwd)


def load_generator(weights_path: Optional[Path] = None, download: bool = True) -> Any:
    """Load the generator once per process. Thread-safe."""
    global _generator, _weights_path, _loaded, _load_error

    with _lock:
        if _loaded and _generator is not None:
            return _generator

        ensure_runtime_env()
        from djtransgan.config import settings
        from djtransgan.model import get_generator
        from djtransgan.utils import load_pt

        torch.manual_seed(settings.RANDOM_SEED)

        if weights_path:
            path = Path(weights_path)
            if not path.is_file():
                path = CODE_DIR / weights_path
        else:
            path = ensure_pretrained(download=download)
        if not path.is_file() and download:
            path = ensure_pretrained(download=True)
        if not path.is_file():
            _load_error = f"weights not found: {path}"
            raise FileNotFoundError(_load_error)

        try:
            generator = get_generator()
            state = load_pt(str(path))
            generator.load_state_dict(state)
            generator.eval()
            _generator = generator
            _weights_path = path
            _loaded = True
            _load_error = None
            return _generator
        except Exception as exc:  # noqa: BLE001
            _loaded = False
            _generator = None
            _load_error = str(exc)
            raise


def generator_status() -> dict:
    return {
        "loaded": _loaded and _generator is not None,
        "weights": str(_weights_path) if _weights_path else None,
        "error": _load_error,
    }


def _tensor_to_curve(tensor: torch.Tensor, max_points: int = 256) -> list[float]:
    """Collapse a mixer curve tensor to a 1-D list for charting."""
    data = tensor.detach().float().cpu().numpy()
    data = np.squeeze(data)
    if data.ndim == 0:
        return [float(data)]
    # Prefer the last axis as time / frequency samples.
    if data.ndim > 1:
        # average over batch/channel/band dims except the longest axis
        longest = int(np.argmax(data.shape))
        axes = tuple(i for i in range(data.ndim) if i != longest)
        if axes:
            data = data.mean(axis=axes)
    data = np.asarray(data, dtype=np.float64).reshape(-1)
    if data.size > max_points:
        idx = np.linspace(0, data.size - 1, max_points).astype(np.int64)
        data = data[idx]
    return [float(x) for x in data.tolist()]


def serialize_mix_out(mix_out: dict, n_time: float) -> dict:
    """Turn generator mix_out into JSON-serialisable fader/band curves."""
    from djtransgan.config import settings

    band_labels = [f"{settings.BAND_FREQS[i]}-{settings.BAND_FREQS[i+1]}Hz"
                   for i in range(len(settings.BAND_FREQS) - 1)]
    out: dict[str, Any] = {
        "n_time": float(n_time),
        "sample_rate": int(settings.SR),
        "band_freqs": list(settings.BAND_FREQS),
        "band_labels": band_labels,
        "tracks": {},
    }
    for track_key, track_dict in mix_out.items():
        if not isinstance(track_dict, dict):
            continue
        entry: dict[str, Any] = {}
        if "fader" in track_dict and track_dict["fader"] is not None:
            entry["fader"] = _tensor_to_curve(track_dict["fader"])
            entry["fader_time"] = [
                i * n_time / max(len(entry["fader"]) - 1, 1)
                for i in range(len(entry["fader"]))
            ]
        if "band" in track_dict and track_dict["band"] is not None:
            band = track_dict["band"].detach().float().cpu().numpy()
            band = np.squeeze(band)
            # Expect something like [bands, bins] or [batch, bands, ...]
            if band.ndim == 1:
                entry["band"] = [_tensor_to_curve(torch.from_numpy(band))]
            else:
                # take each row along the band axis (axis 0 after squeeze, or -2)
                if band.ndim >= 2:
                    # choose axis that looks like band count (~3-4)
                    band_axis = 0
                    for ax, size in enumerate(band.shape):
                        if 2 <= size <= 8:
                            band_axis = ax
                            break
                    curves = []
                    for i in range(band.shape[band_axis]):
                        sl = [slice(None)] * band.ndim
                        sl[band_axis] = i
                        curves.append(_tensor_to_curve(torch.from_numpy(np.asarray(band[tuple(sl)]))))
                    entry["band"] = curves
                else:
                    entry["band"] = [_tensor_to_curve(torch.from_numpy(band))]
        out["tracks"][track_key] = entry
    return out


def run_mix(
    prev_path: str | Path,
    next_path: str | Path,
    prev_cue: float,
    next_cue: float,
    out_dir: str | Path,
    *,
    weights_path: Optional[Path] = None,
    download: bool = True,
    on_progress: Optional[ProgressCb] = None,
    short_name: str = "short.wav",
    full_name: str = "full.wav",
    params_name: str = "params.json",
    match_bpm: bool = False,
    align_cue: bool = True,
) -> dict:
    """
    Run one mix. Writes short/full wav + params.json into out_dir.
    Returns metadata including paths and corrected cues / BPM.
    """
    ensure_runtime_env()
    progress = on_progress or _noop_progress

    from djtransgan.config import settings
    from djtransgan.process import preprocess, postprocess
    from djtransgan.utils import check_exist, get_filename, load_audio, out_audio, squeeze_dim

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generator = load_generator(weights_path=weights_path, download=download)

    progress(0, PIPELINE_TOTAL, "Loading audio ...")
    prev_audio = load_audio(str(prev_path))
    next_audio = load_audio(str(next_path))

    # preprocess reports steps 1-5
    with _lock:
        (pair_audio, timestamps), (pair_audio_for_g, cue_for_g), meta = preprocess(
            prev_audio,
            next_audio,
            float(prev_cue),
            float(next_cue),
            on_progress=_map_preprocess_progress(progress),
            match_bpm=match_bpm,
            align_cue=align_cue,
        )

        progress(6, PIPELINE_TOTAL, "Mixing with generator ...")
        mix_audio, mix_out = generator.infer(*pair_audio_for_g, cue_region=cue_for_g)
        post_mix_audio, post_cue = postprocess(mix_audio, pair_audio, timestamps, cue_for_g)

    progress(7, PIPELINE_TOTAL, "Saving audio ...")
    short_path = out_dir / short_name
    full_path = out_dir / full_name
    params_path = out_dir / params_name
    check_exist(str(short_path))
    out_audio(squeeze_dim(mix_audio).to(torch.float32), str(short_path))
    check_exist(str(full_path))
    out_audio(squeeze_dim(post_mix_audio).to(torch.float32), str(full_path))

    params = serialize_mix_out(mix_out, float(settings.N_TIME))
    if isinstance(post_cue, torch.Tensor):
        post_cue_list = [float(x) for x in squeeze_dim(post_cue).detach().cpu().tolist()]
    else:
        post_cue_list = [float(x) for x in np.atleast_1d(post_cue).tolist()]
    params["post_cue"] = post_cue_list
    params["meta"] = meta
    params["sources"] = {
        "prev": get_filename(str(prev_path)),
        "next": get_filename(str(next_path)),
        "prev_cue_in": float(prev_cue),
        "next_cue_in": float(next_cue),
        "match_bpm": bool(match_bpm),
        "align_cue": bool(align_cue),
    }
    params_path.write_text(json.dumps(params, ensure_ascii=False, indent=2), encoding="utf-8")

    progress(7, PIPELINE_TOTAL, "Done")
    return {
        "short_path": str(short_path),
        "full_path": str(full_path),
        "params_path": str(params_path),
        "meta": meta,
        "post_cue": post_cue_list,
    }
