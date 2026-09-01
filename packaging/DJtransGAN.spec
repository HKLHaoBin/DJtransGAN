# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller onedir build for DJtransGAN Mix Studio."""

from __future__ import annotations

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None
ROOT = Path(SPECPATH).resolve().parent

datas = [
    (str(ROOT / "VERSION"), "."),
    (str(ROOT / "web" / "dist"), "web/dist"),
    (str(ROOT / "tools" / "rubberband"), "tools/rubberband"),
]

code_dir = ROOT / "code"
if code_dir.is_dir():
    datas.append((str(code_dir), "code"))

demo_dir = ROOT / "demo-site"
if demo_dir.is_dir():
    datas.append((str(demo_dir), "demo-site"))

binaries: list = []
hiddenimports: list = [
    "server",
    "server.main",
    "server.desktop",
    "server.engine",
    "server.jobs",
    "server.paths",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "multipart",
    "sklearn",
    "sklearn.utils._cython_blas",
]

for pkg in (
    "djtransgan",
    "librosa",
    "resampy",
    "soundfile",
    "nnAudio",
    "openunmix",
    "torchaudio",
    "sklearn",
    "pyrubberband",
    "pyloudnorm",
    "asteroid_filterbanks",
):
    try:
        hiddenimports += collect_submodules(pkg)
    except Exception:
        pass

for pkg in ("librosa", "nnAudio", "openunmix", "sklearn"):
    try:
        pkg_datas, pkg_bins, pkg_hidden = collect_all(pkg)
        datas += pkg_datas
        binaries += pkg_bins
        hiddenimports += pkg_hidden
    except Exception:
        pass

try:
    datas += collect_data_files("librosa")
except Exception:
    pass

a = Analysis(
    [str(ROOT / "server" / "desktop.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["IPython", "jupyter", "notebook", "matplotlib.tests", "tkinter"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DJtransGAN",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DJtransGAN",
)
