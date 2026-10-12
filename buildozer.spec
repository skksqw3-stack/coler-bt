[app]

title = Cooler Control
package.name = coolercontrol
package.domain = org.coolercontrol

source.dir = .
source.include_exts = py,kv,png,jpg,atlas,ttf
source.include_patterns = assets/*,*.py,*.kv

version = 1.0.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0,pyjnius,pyserial

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/assets/icon.png

android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_CONNECT,BLUETOOTH_SCAN,ACCESS_FINE_LOCATION
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.build_tools_version = 33.0.2
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = False
android.private_storage = True

android.sdk_path = /home/seyed/android-sdk
android.ndk_path = /home/seyed/android-ndk/ndk

[buildozer]
log_level = 2
warn_on_root = 1
