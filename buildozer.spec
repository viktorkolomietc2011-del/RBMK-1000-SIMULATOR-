[app]

# (str) Title of your application
title = My Pygame App

# (str) Package name
package.name = mygame

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,wav,mp3,ogg

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# Сюда записываем все библиотеки, которые нужны для работы
requirements = python3,kivy,pygame-menu

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (bool) Automatically accept SDK license
# ВОТ ЭТА СТРОЧКА САМАЯ ГЛАВНАЯ!
android.accept_sdk_license = True

# (list) Permissions
# android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (str) Android NDK architecture to build for
android.archs = arm64-v8a, armeabi-v7a

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = false, 1 = true)
warn_on_root = 1
