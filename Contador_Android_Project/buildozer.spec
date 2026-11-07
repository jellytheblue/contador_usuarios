[app]
title = Contador de usuarios
package.name = contadordeusuarios
package.domain = cl.felipebecker
source.dir = .
source.include_exts = py,kv,png,jpg,json,md
version = 1.0.0
requirements = python3==3.12.9,kivy==2.3.1
orientation = portrait
fullscreen = 0

# Android: app privada, sin permisos de almacenamiento ni red.
android.api = 35
android.minapi = 23
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True
icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/icon.png

[buildozer]
log_level = 2
warn_on_root = 1
