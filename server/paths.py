"""Workspace paths and environment bootstrap for the Mix Studio server."""

from __future__ import annotations

import server.compat  # noqa: F401  # madmom Py3.10 shim before djtransgan imports

import os
import shutil
import sys
from pathlib import Path


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    """Read-only app resources (repo root in dev; PyInstaller bundle when frozen)."""
    if _is_frozen():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def data_root() -> Path:
    """Writable user data (results, pretrained weights)."""
    if _is_frozen():
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            return Path(base) / "DJtransGAN"
        return Path.home() / "DJtransGAN"
    return resource_root()


def read_version() -> str:
    for candidate in (
        resource_root() / "VERSION",
        Path(__file__).resolve().parent.parent / "VERSION",
    ):
        if candidate.is_file():
            text = candidate.read_text(encoding="utf-8").strip()
            if text:
                return text
    return "0.1.0"


ROOT = resource_root()
DATA_ROOT = data_root()
CODE_DIR = ROOT / "code"
DEMO_SITE = ROOT / "demo-site"
WEB_DIST = ROOT / "web" / "dist"
RESULTS_DIR = DATA_ROOT / "results"
JOBS_DIR = RESULTS_DIR / "web-jobs"
RUBBERBAND_DIR = ROOT / "tools" / "rubberband"
PRETRAINED_DIR = DATA_ROOT / "pretrained"
DEFAULT_WEIGHTS = PRETRAINED_DIR / "djtransgan_minmax.pt"


def ensure_runtime_env() -> None:
    """Put `code/` on sys.path and rubberband.exe on PATH (Windows-safe)."""
    global ROOT, DATA_ROOT, CODE_DIR, DEMO_SITE, WEB_DIST
    global RESULTS_DIR, JOBS_DIR, RUBBERBAND_DIR, PRETRAINED_DIR, DEFAULT_WEIGHTS

    ROOT = resource_root()
    DATA_ROOT = data_root()
    CODE_DIR = ROOT / "code"
    DEMO_SITE = ROOT / "demo-site"
    WEB_DIST = ROOT / "web" / "dist"
    RESULTS_DIR = DATA_ROOT / "results"
    JOBS_DIR = RESULTS_DIR / "web-jobs"
    RUBBERBAND_DIR = ROOT / "tools" / "rubberband"
    PRETRAINED_DIR = DATA_ROOT / "pretrained"
    DEFAULT_WEIGHTS = PRETRAINED_DIR / "djtransgan_minmax.pt"

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
