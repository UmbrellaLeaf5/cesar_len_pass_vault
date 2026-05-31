# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from PyInstaller.utils.hooks import collect_all


python_prefix = sys.prefix

datas = [
  ("images", "images/"),
  ("src", "src/"),
  ("app", "app/"),
  (os.path.join(python_prefix, "share", "angle"), "share/angle/"),
  (os.path.join(python_prefix, "share", "glew"), "share/glew/"),
  (os.path.join(python_prefix, "share", "sdl2"), "share/sdl2/"),
]

binaries = []
hiddenimports = [
  "cesar_len_pass_vault",
  "cesar_len_pass_vault.models",
  "cesar_len_pass_vault.storage",
  "cesar_len_pass_vault.sync",
  "app.screens",
  "app.popups",
  "app.services",
  "app.widgets",
]

tmp_ret = collect_all("yadisk")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
  ["main.py"],
  pathex=[],
  binaries=binaries,
  datas=datas,
  hiddenimports=hiddenimports,
  hookspath=[],
  hooksconfig={},
  runtime_hooks=[],
  excludes=[
    "kivy_deps.angle",
    "kivy_deps.glew",
    "kivy_deps.sdl2",
    "gstreamer",
    "enchant",
    "cv2",
    "picamera",
    "gi",
  ],
  noarchive=False,
  optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
  pyz,
  a.scripts,
  [],
  exclude_binaries=True,
  name="CesarLen PassVault",
  debug=False,
  bootloader_ignore_signals=False,
  strip=False,
  upx=True,
  console=False,
  disable_windowed_traceback=False,
  argv_emulation=False,
  target_arch=None,
  codesign_identity=None,
  entitlements_file=None,
  icon=["images/leaves.ico"],
)

coll = COLLECT(
  exe,
  a.binaries,
  a.datas,
  strip=False,
  upx=True,
  upx_exclude=[],
  name="CesarLen-PassVault",
)
