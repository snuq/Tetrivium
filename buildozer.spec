[app]

# (str) Title of your application
title = Tetrivium

# (str) Package name
package.name = Tetrivium

# (str) Package domain (needed for android/ios packaging)
package.domain = com.snuq

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,wav,ogg,mp3,ttf,txt,ini

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, GFX, histories, BuildWindows, BuildAndroid, Experiments

# (str) Application versioning (method 1)
version = 0.9

# (list) Application requirements
# comma seperated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==master,plyer

# (str) Presplash of the application
presplash.filename = %(source.dir)s/data/splash.png

# (str) Icon of the application
icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, portrait or all)
orientation = all


# (int) Target Android API, should be as high as possible.
#android.api = 27

# (int) Minimum API your APK will support.
#android.minapi = 21

# (int) Android SDK version to use
#android.sdk = 20

# (str) Android NDK version to use
#android.ndk = 19b

# (int) Android NDK API to use. This is the minimum API your app will support, it should usually match android.minapi.
#android.ndk_api = 21


# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = WRITE_EXTERNAL_STORAGE, VIBRATE, INTERNET

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86
android.arch = armeabi-v7a

#p4a.branch = release-2020.06.02

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
