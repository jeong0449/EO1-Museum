# EO1-Museum Installation Guide

_Current native application — network installation and optional ADB path_

> **Important — experimental installation instructions**
>
> This guide has been **reconstructed retrospectively** from the development history of EO1-Museum and from the current working configuration of the author's EO1.
>
> EO1-Museum evolved incrementally through several architectures. The current native application was developed on an EO1 that had already been configured and modified during development. Therefore, the simplified installation procedure in **Part I has not been tested from beginning to end on a fresh or factory-reset EO1**.
>
> In particular, the current architecture indicates that **Firefox, MetBoot, ADB, and ADBApprovalHelper are not required for normal installation and operation**. The native EO1-Museum APK should be installable through the EO1's built-in browser, and artwork can subsequently be transferred over Wi-Fi using PC Gallery and Safe Sync. However, this complete no-ADB installation path has not yet been independently verified on an untouched device.
>
> **Proceed at your own risk. Do not factory-reset or otherwise modify a working EO1 solely to test these instructions.**
>
> The earlier Firefox + MetBoot procedure is retained separately in `legacy/INSTALL_LEGACY.md`.

## Which installation method should I use?

```text
Normal installation / ordinary use
    → Part I: Network installation and Safe Sync
    → No ADB intended

Direct USB installation or media transfer
Development / debugging / maintenance
    → Part II: ADB installation and maintenance

Historical Firefox + MetBoot setup
    → legacy/INSTALL_LEGACY.md
```

# Part I — Network Installation and Normal Operation

## 1. Requirements

### PC
- Windows PC
- Python 3
- EO1-Museum repository
- Wi-Fi or local network connection
- Current EO1-Museum APK

### EO1
- Electric Objects EO1
- Wi-Fi connection
- Micro-USB OTG adapter or hub
- USB keyboard and mouse for initial setup

### Not normally required
- Firefox 68.11.0
- MetBoot
- ADB
- ADBApprovalHelper

Firefox and MetBoot belong to the earlier browser-based architecture. ADB and ADBApprovalHelper are for direct USB installation, development, debugging, and maintenance; see Part II.

## 2. Prepare the EO1

Connect a USB keyboard and mouse through a micro-USB OTG adapter or hub.

Open the built-in Android browser with:

```text
Win + B
```

Connect the EO1 to the same local network as the PC. If Android blocks APK installation, enable **Unknown Sources** in the Android security settings.

## 3. Prepare the PC

Clone or download EO1-Museum and make sure Python 3 is available.

Start the included server:

```powershell
python server.py
```

Find the PC's local IPv4 address if necessary:

```powershell
ipconfig
```

Example:

```text
192.168.1.103
```

## 4. Install EO1-Museum through the built-in browser

> **Status:** retrospectively reconstructed; not yet verified as a complete fresh-install sequence on an untouched EO1.

Place or expose the EO1-Museum APK in a location served by `server.py`.

From the EO1's built-in browser, open the corresponding URL, for example:

```text
http://192.168.1.103:8000/EO1-Museum.apk
```

Replace the IP address and filename with the actual values.

Download the APK and follow Android's prompts to install it. Because EO1-Museum operates as a HOME application, select EO1-Museum as HOME and choose **Always** if offered.

The intended startup path is:

```text
EO1 power on
      ↓
Android
      ↓
EO1-Museum
      ↓
Local Gallery
```

Firefox and MetBoot are not part of this startup sequence.

## 5. Local Gallery

EO1-Museum starts in **Local Gallery** mode. Artwork stored in the EO1's internal gallery storage can be displayed without a PC or network connection.

Once an exhibition has been synchronized to the EO1, normal Local Gallery playback is independent of the PC.

## 6. Prepare artwork on the PC

The general workflow is:

```text
Open-access collections
        ↓
Discovery / download
        ↓
original/
        ↓
make_gallery.py
        ↓
display/ + images.js
```

`make_gallery.py` prepares images for the EO1's 1080 × 1920 portrait display.

## 7. PC Gallery

Start the server without synchronization:

```powershell
python server.py
```

Select **PC Gallery** on the EO1.

PC Gallery is displayed inside the native application using its embedded WebView, so Firefox is not required.

## 8. Safe Sync

To copy the prepared exhibition into EO1 internal storage:

```powershell
python server.py --sync
```

Then select **PC Gallery** on the EO1.

```text
PC Gallery selected
        ↓
EO1 contacts server.py
        ↓
Server identity checked
        ↓
SYNC=1
        ↓
Safe Sync
        ↓
EO1 internal storage
        ↓
Local Gallery
```

Safe Sync uses temporary downloads before replacing existing files and respects configured media-count and free-storage limits. Progress is displayed on the EO1.

After synchronization, Local Gallery can operate without the PC server.

## 9. Normal workflow

```text
PC
 ├── discover artwork
 ├── curate exhibition
 ├── prepare display files
 └── python server.py --sync
             │
             │ Wi-Fi
             ▼
EO1
 ├── PC Gallery
 ├── Safe Sync
 └── Local Gallery
             ↓
       independent playback
```

ADB is not intended to be necessary for this workflow.

# Part II — ADB Installation and Maintenance

Use this path when you want to:

- install or update EO1-Museum directly over USB;
- copy media directly to the EO1;
- inspect the filesystem;
- use `adb shell` or `logcat`;
- troubleshoot, develop, or test new versions.

Unlike the simplified Part I procedure, this path was used extensively during EO1-Museum development.

## 10. The EO1 ADB authorization problem

The EO1 has no touchscreen. When a new PC connects through USB ADB, Android normally displays an RSA authorization dialog.

The micro-USB port is also used for the OTG keyboard/mouse connection, so the mouse may no longer be available when the EO1 is connected to the development PC.

`ADBApprovalHelper.apk` was created for this bootstrap problem. Its AccessibilityService detects the USB debugging authorization dialog, selects **Always allow from this computer**, and activates **OK**.

ADBApprovalHelper is **not required for normal EO1-Museum operation**.

## 11. Install and enable ADBApprovalHelper

Before switching from the OTG keyboard/mouse setup to the development PC, install `ADBApprovalHelper.apk`.

One possible method is the same local HTTP approach used in Part I:

```text
PC server.py
      ↓
EO1 built-in browser
      ↓
ADBApprovalHelper.apk
```

After installation, enable its AccessibilityService in Android settings.

> Installing the APK alone does not necessarily enable its AccessibilityService.

## 12. Connect with ADB

Connect the EO1 directly to the PC by USB:

```powershell
adb devices
```

If more than one Android device is connected:

```powershell
adb -s <EO1_SERIAL> devices
```

The author's development unit uses serial:

```text
115343222
```

Do not assume another EO1 will have the same serial number.

## 13. Install or update EO1-Museum

Install:

```powershell
adb -s <EO1_SERIAL> install EO1-Museum.apk
```

Update while retaining application data:

```powershell
adb -s <EO1_SERIAL> install -r EO1-Museum.apk
```

Current package:

```text
com.dan.eo1
```

Check it:

```powershell
adb -s <EO1_SERIAL> shell pm list packages | findstr /i eo1
```

Launch it:

```powershell
adb -s <EO1_SERIAL> shell monkey -p com.dan.eo1 -c android.intent.category.LAUNCHER 1
```

## 14. Transfer media directly with ADB

Safe Sync is preferred for normal use, but ADB can copy media directly.

Current Local Gallery directory:

```text
/sdcard/EO1-Museum/images/
```

Inspect it:

```powershell
adb -s <EO1_SERIAL> shell ls -l /sdcard/EO1-Museum/images/
```

Copy media:

```powershell
adb -s <EO1_SERIAL> push artwork.jpg /sdcard/EO1-Museum/images/
adb -s <EO1_SERIAL> push artwork.mp4 /sdcard/EO1-Museum/images/
```

## 15. Useful maintenance commands

```powershell
adb devices
adb -s <EO1_SERIAL> shell
adb -s <EO1_SERIAL> shell pm list packages | findstr /i eo1
adb -s <EO1_SERIAL> shell ls -l /sdcard/EO1-Museum/images/
adb -s <EO1_SERIAL> install -r EO1-Museum.apk
adb -s <EO1_SERIAL> shell am force-stop com.dan.eo1
adb -s <EO1_SERIAL> shell monkey -p com.dan.eo1 -c android.intent.category.LAUNCHER 1
```

## 16. Wireless ADB

After an initial USB ADB connection:

```powershell
adb -s <EO1_SERIAL> tcpip 5555
adb connect <EO1_IP>:5555
```

Wireless ADB is a development convenience, not part of normal installation. On the tested EO1, it did not persist across reboot.

# Legacy Architecture

Firefox 68.11.0 and MetBoot belong to the first stable browser-based EO1-Museum architecture:

```text
Android
   ↓
MetBoot
   ↓
Firefox
   ↓
PC-hosted EO1-Museum gallery
```

The native application later absorbed PC Gallery into its own WebView and became the HOME application:

```text
Android
   ↓
EO1-Museum
   ↓
Local Gallery
```

The historical procedure remains in:

```text
legacy/INSTALL_LEGACY.md
```

# Installation Status Summary

| Component | Normal installation | ADB / development | Legacy browser setup |
|---|---|---|---|
| EO1-Museum APK | Required | Required | — |
| Built-in Android browser | Initial installation | Optional | Initial setup |
| PC `server.py` | APK delivery / PC Gallery / Safe Sync | Optional | Required |
| Firefox 68.11.0 | No | No | Required |
| MetBoot | No | No | Required |
| ADB | No | Yes | No |
| ADBApprovalHelper | No | Useful for initial authorization | No |
| USB keyboard/mouse | Initial setup | Useful | Initial setup |
| Wi-Fi | Installation / PC Gallery / Sync | Optional | Required |

# Final Note

EO1-Museum reached its current architecture through experimentation rather than through a single planned installation design.

The simplest current installation path in Part I is a **retrospective reconstruction of how a fresh EO1 should now be configured**, not a record of how the author's EO1 was originally built.

If you have a working EO1, preserve that working state.

If Part I works on an untouched EO1, please consider documenting the result so that this procedure can eventually move from **reconstructed** to **verified**.
