[app]

# (str) Title of your application
title = РБМК

# (str) Package name
package.name = rbmkgame

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,wav,ogg,ttf,json

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,pygame-menu,sdl2,sdl2_image,sdl2_mixer,sdl2_ttf

# (str) Custom source folders for requirements
# Allows to use a custom version of a requirement
# requirements.source.kivy = ../kivy

# (str) Icon of your application
icon.filename = %(source.dir)s/Icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (list) Permissions
# android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

# (list) List of Java .jar files to add to the libs so that your Python code can use them
# android.add_jars = foo.jar,bar.jar

# (list) The Android architectures to build for
android.archs = arm64-v8a

# (bool) Enable Android auto backup feature (Android API >= 23)
android.allow_backup = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = disable, 1 = enable)
warn_on_root = 1
