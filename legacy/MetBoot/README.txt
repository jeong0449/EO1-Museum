MetBoot for Electric Objects EO1
================================

Purpose
-------
- Minimum Android version: API 19 (Android 4.4)
- On BOOT_COMPLETED, launches Firefox package org.mozilla.firefox
- Tapping "Met Boot" manually also launches Firefox
- No AndroidX libraries are used.
- The museum URL is NOT hard-coded. Firefox uses its own saved homepage.

Build in Android Studio
-----------------------
1. File > Open
2. Select the MetBoot folder (the folder containing settings.gradle.kts)
3. Let Gradle Sync finish.
   - If Android Studio asks to install Android SDK Platform 35, allow it.
4. Build > Build App Bundle(s) / APK(s) > Build APK(s)
   (menu wording can vary slightly by Android Studio version)
5. APK output:
   app\build\outputs\apk\debug\app-debug.apk

EO1 test
--------
1. Install app-debug.apk on EO1.
2. Before rebooting, tap the "Met Boot" app once.
3. Firefox should launch.
4. Then reboot EO1 and test automatic Firefox launch.

Important
---------
Android 3.1+ only delivers BOOT_COMPLETED to an app after the user has
launched that app at least once after installation. Therefore step 2 above
is intentional.
