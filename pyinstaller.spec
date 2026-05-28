# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

from kivy_deps import sdl2, glew


root = Path(__file__).parent

a = Analysis(
    [str(root / "app" / "main.py")],
    pathex=[],
    binaries=[],
    datas=[
        (str(root / "app"), "app"),
        (str(root / "src"), "src"),
        (str(root / "images"), "images"),
    ],
    hiddenimports=["kivy_deps.sdl2", "kivy_deps.glew", "kivy_deps.angle"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    [],
    name="CesarVault",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "images" / "leaves.ico"),
)
