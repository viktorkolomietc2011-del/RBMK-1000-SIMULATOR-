[app]

title = RBMK-1000
package.name = rbmk
package.domain = org.simulator

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav

icon.filename = Icon.png

version = 1.0
requirements = python3,kivy

orientation = landscape
fullscreen = 1

android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.api = 31
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 1
warn_on_root = 1
