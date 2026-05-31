[app]
title = CesarLen PassVault
android.release_artifact = apk
package.name = cesarlenpassvault
package.domain = org.umbrellaleaf5
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,atlas
version = 0.1.0

requirements = python3,kivy==2.3.1,yadisk,python-dotenv,git+https://github.com/UmbrellaLeaf5/cesar_len_key.git
orientation = portrait
fullscreen = 1
icon.filename = images/leaves.png

# Android permissions
android.permissions = INTERNET
android.api = 34
android.minapi = 26
android.archs = arm64-v8a
android.allow_backup = True

android.ndk = 25c
android.build_tools_version = 34.0.0
android.accept_sdk_license = True

# Build options
p4a.branch = master
android.logcat_filters = *:S python:D

[buildozer]
log_level = 1
warn_on_root = 1
