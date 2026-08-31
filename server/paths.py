"""Workspace paths and environment bootstrap for the Mix Studio server."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = ROOT / "code"
DEMO_SITE = ROOT / "demo-site"
RESULTS_DIR = ROOT / "results"
JOBS_DIR = RESULTS_DIR / "web-jobs"
RUBBERBAND_DIR = ROOT / "tools" / "rubberband"
PRETRAINED_DIR = CODE_DIR / "pretrained"
DEFAULT_WEIGHTS = PRETRAINED_DIR / "djtransgan_minmax.pt"


def ensure_runtime_env() -> None:
    """Put `code/` on sys.path and rubberband.exe on PATH (Windows-safe)."""
    code = str(CODE_DIR)
    if code not in sys.path:
        sys.path.insert(0, code)

    rb = str(RUBBERBAND_DIR)
    path = os.environ.get("PATH", "")
    if rb and rb not in path.split(os.pathsep):
        os.environ["PATH"] = rb + os.pathsep + path

    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    PRETRAINED_DIR.mkdir(parents=True, exist_ok=True)


def rubberband_available() -> bool:
    return shutil.which("rubberband") is not None or (RUBBERBAND_DIR / "rubberband.exe").is_file()


def rubberband_path() -> str | None:
    which = shutil.which("rubberband")
    if which:
        return which
    exe = RUBBERBAND_DIR / "rubberband.exe"
    return str(exe) if exe.is_file() else None
