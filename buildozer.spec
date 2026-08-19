[app]

# (str) Title of your application
title = РБМК

# (str) Package name
package.name = rbmksimulator

# (str) Package domain (needed for android packaging)
package.domain = org.viktorkol

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (include all py, png, jpg, wav, mp3, ttf)
source.include_exts = py,png,jpg,jpeg,ttf,otf,wav,mp3,ogg

# (list) Application requirements
# Зафиксирован python3==3.11.5 для стабильной сборки
requirements = python3==3.11.5,kivy,pygame-menu,sdl2

# (str) Application versioning
version = 0.1

# (list) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (str) Icon of the application
icon.filename = Icon.png

# (str) Supported platforms
# (int) Target Android API
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (int) Android NDK API
android.ndk_api = 21

# (str) Android NDK version
android.ndk = 25b

# (bool) Use --private data storage (VirtualEnv inside APK)
android.private_storage = True

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (list) Android architecture to build for
android.archs = arm64-v8a

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

# (str) Explicit Python version for Android
android.python_version = 3.11

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = disable)
warn_on_root = 1
