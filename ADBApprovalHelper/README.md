# ADB Approval Helper

Experimental helper for EO1 / Android 4.4.2 (API 19).

## Build
Open this folder in Android Studio, let Gradle sync, then use Build > Build Bundle(s) / APK(s) > Build APK(s).
Expected APK: app/build/outputs/apk/debug/app-debug.apk

## Test
1. Copy APK to EO1 Download using MTP.
2. Install it using the OTG mouse.
3. Launch ADB Approval Helper.
4. Open Accessibility Settings and enable ADB Approval Helper.
5. Disconnect OTG.
6. Connect EO1 directly to the PC by USB.
7. Wait for the Allow USB debugging dialog.
8. Run `adb devices` on the PC.

The service only acts when package com.android.systemui contains the exact text `Always allow from this computer`. It then attempts to check that option and click OK.

If successful: `adb -s 115343222 tcpip 5555`

Experimental: EO1 SystemUI may not expose these dialog controls to Accessibility. Failure should leave the dialog unchanged.
