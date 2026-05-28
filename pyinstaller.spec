# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import kivy_deps.angle
import kivy_deps.glew
import kivy_deps.sdl2
from PyInstaller.utils.hooks import collect_data_files

SPECPATH = os.path.abspath(SPECPATH)
sys.path.insert(0, os.path.join(SPECPATH, "src"))

def tree_datas(root, target_dir):
    """Собрать все файлы из root в target_dir с сохранением подпапок."""
    datas = []
    for dirpath, _, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        dest = os.path.join(target_dir, rel) if rel != '.' else target_dir
        for fn in filenames:
            src = os.path.join(dirpath, fn)
            datas.append((src, dest))
    return datas

# ---------- kivy_deps пакеты (сами .py файлы) ----------
angle_dir = os.path.dirname(kivy_deps.angle.__file__)
angle_pkg = tree_datas(angle_dir, 'kivy_deps/angle')

glew_dir = os.path.dirname(kivy_deps.glew.__file__)
glew_pkg = tree_datas(glew_dir, 'kivy_deps/glew')

sdl2_dir = os.path.dirname(kivy_deps.sdl2.__file__)
sdl2_pkg = tree_datas(sdl2_dir, 'kivy_deps/sdl2')

# ---------- DLL библиотеки (share) внутрь соответствующих пакетов ----------
share_prefix = sys.prefix  # обычно C:\hostedtoolcache\windows\Python\3.12.10\x64
angle_share = tree_datas(
    os.path.join(share_prefix, 'share', 'angle'),
    'kivy_deps/angle/share/angle'
)
glew_share = tree_datas(
    os.path.join(share_prefix, 'share', 'glew'),
    'kivy_deps/glew/share/glew'
)
sdl2_share = tree_datas(
    os.path.join(share_prefix, 'share', 'sdl2'),
    'kivy_deps/sdl2/share/sdl2'
)

a = Analysis(
    [os.path.join(SPECPATH, "main.py")],
    pathex=[SPECPATH, os.path.join(SPECPATH, "src")],
    binaries=[],
    datas=[
        (os.path.join(SPECPATH, "app", "main.kv"), "app"),
        (os.path.join(SPECPATH, "app", "screens", "unlock.kv"), os.path.join("app", "screens")),
        (os.path.join(SPECPATH, "app", "screens", "vault.kv"), os.path.join("app", "screens")),
        (os.path.join(SPECPATH, "app", "popups", "add_entry.kv"), os.path.join("app", "popups")),
        (os.path.join(SPECPATH, "app", "popups", "sync.kv"), os.path.join("app", "popups")),
        (os.path.join(SPECPATH, "app", "popups", "settings.kv"), os.path.join("app", "popups")),
        (os.path.join(SPECPATH, "images", "leaves.png"), "images"),
        (os.path.join(SPECPATH, "images", "leaves.ico"), "images"),
    ]
    + collect_data_files("cesar_len_pass_vault")
    + angle_pkg + glew_pkg + sdl2_pkg
    + angle_share + glew_share + sdl2_share,
    hiddenimports=[
        "cesar_len_pass_vault",
        "cesar_len_pass_vault.config",
        "cesar_len_pass_vault.models",
        "cesar_len_pass_vault.storage",
        "cesar_len_pass_vault.sync",
        "cesar_len_pass_vault.cipher_wrapper",
        "cesar_len_pass_vault.cipher_primary",
        "cesar_len_pass_vault.crypto_utils",
        "cesar_len_pass_vault.enums",
        "cesar_len_pass_vault.exceptions",
        "app",
        "app.screens.unlock",
        "app.screens.vault",
        "app.services.vault_ops",
        "app.widgets.toolbar",
        "app.popups",
        "app.popups.confirm_delete",
        "app.popups.entry_detail",
        "app.popups.add_entry",
        "app.popups.password_prompt",
        "app.popups.sync",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['kivy_deps.angle', 'kivy_deps.glew', 'kivy_deps.sdl2', 'gstreamer'],
    noarchive=False,
    optimize=0,
)

excluded_modules = ['kivy_deps.angle', 'kivy_deps.glew', 'kivy_deps.sdl2']
a.pure = [m for m in a.pure if m[0] not in excluded_modules]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
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
    icon=os.path.join(SPECPATH, "images", "leaves.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CesarVault',
)
