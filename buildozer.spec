[app]

# Название и пакет
title = RBMK-1000
package.name = rbmk
package.domain = org.simulator

# Исходники
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav

# Иконка приложения
icon.filename = Icon.png

# Версия и требования (исправлено: убрали точечную версию python)
version = 1.0
requirements = python3,kivy

# Экран (альбомная ориентация)
orientation = landscape
fullscreen = 1

# Настройки Android
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
# Чистый лог для быстрой отладки
log_level = 1
warn_on_root = 1
