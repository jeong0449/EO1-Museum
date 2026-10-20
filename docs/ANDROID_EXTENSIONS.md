# Extending the Original Android Environment on the Electric Objects EO1

> **Status: Experimental / Planning**
>
> EO1-Museum currently operates successfully using the original Android 4.4 environment, MetBoot, Firefox, and a local web server running on an external PC.
>
> Experiments on 20 October 2026 failed to reproduce previously reported Linux USB booting on the EO1. Rather than modifying the bootloader or internal eMMC, another development path is therefore being investigated: **preserving the original Android system while extending its capabilities**.
>
> Two experiments are of particular interest:
>
> 1. determining whether USB mass storage can be detected and used by Android, using wireless ADB for diagnosis; and
> 2. investigating the open-source `spalt/EO1` Android application as the basis for a native EO1-Museum application.
>
> Neither approach requires modification of the internal eMMC at this stage.

---

## 1. Why continue with Android?

The current EO1-Museum architecture is:

    Museum open-access collection
        ↓
    PC downloads and prepares artwork
        ↓
    PC local HTTP server
        ↓
    Wi-Fi
        ↓
    EO1 / Android 4.4
        ↓
    MetBoot
        ↓
    Firefox
        ↓
    EO1-Museum gallery

This arrangement already works reliably.

The Linux USB boot experiment was intended to investigate whether the PC and network dependency could eventually be eliminated. However, the tested Nitrogen6X Linux images did not boot on this EO1.

The original Android system therefore remains more than merely a fallback environment. It may itself provide a practical route toward a more independent EO1-Museum.

The main questions are:

- Can Android access a USB flash drive connected through OTG?
- Can artwork be stored locally rather than served from a PC?
- Can Firefox be replaced by a native Android image viewer?
- Can the EO1 boot directly into such an application?
- Can the existing EO1-specific hardware controls be retained?

Two experiments may help answer these questions.

---

## 2. Experiment A — USB mass storage under Android

The EO1 micro-USB port is known to support USB OTG.

The following USB devices have already been successfully used:

- keyboard;
- mouse;
- powered USB hub.

This confirms that the EO1 can operate as a USB host.

However, connecting a USB flash drive did not cause an obvious removable-storage device to appear in the Android **Settings → Storage** interface.

This does not necessarily mean that the Linux kernel failed to detect the device.

Several possibilities remain:

1. the USB mass-storage device is not detected at all;
2. the device is detected but Android does not automatically mount it;
3. a block device is created but not exposed through the Settings interface;
4. the device is mounted somewhere under `/mnt` or `/storage`;
5. the EO1 Android build lacks part of the normal removable-storage framework.

The next experiment should distinguish between these possibilities.

---

## 3. Why wireless ADB is useful

Normally, ADB is connected through the same micro-USB port that is needed for the OTG adapter.

This creates a problem:

    PC
     ↓
    USB ADB
     ↓
    EO1 micro-USB

and:

    USB flash drive
     ↓
    OTG adapter
     ↓
    EO1 micro-USB

cannot normally be used at the same time.

A possible solution is to move ADB communication from USB to Wi-Fi.

The proposed sequence is:

    PC
     ↓
    USB ADB
     ↓
    EO1

followed by:

    adb tcpip 5555

After determining the EO1 Wi-Fi address:

    adb shell ip addr show wlan0

ADB could then reconnect over the network:

    adb connect <EO1-IP>:5555

If successful, the physical USB connection to the PC could be removed.

The EO1 micro-USB port would then become available for:

    EO1
     ↓
    OTG adapter
     ↓
    powered USB hub
     ├── USB flash drive
     └── keyboard

while diagnostics continue from the PC over Wi-Fi.

---

## 4. Proposed USB-storage diagnostic procedure

Once wireless ADB is working, connect a FAT32-formatted USB flash drive through the OTG adapter or powered USB hub.

Then enter:

    adb shell

The first commands should be read-only diagnostics.

### Check mounted filesystems

    mount

Look for paths associated with USB or removable storage.

Possible locations may include:

    /storage
    /mnt
    /mnt/media_rw

The actual EO1 configuration must be determined experimentally rather than assumed.

### Check storage directories

    ls -l /storage
    ls -l /mnt

### Check block devices

    ls -l /dev/block

### Check kernel partition information

    cat /proc/partitions

If the USB drive has been detected as a conventional SCSI-style USB mass-storage device, entries resembling the following might appear:

    sda
    sda1

The exact device name must not be assumed in advance.

### Check recent kernel messages

If permitted by the Android build:

    dmesg | tail -n 100

Useful messages might reveal:

- USB device enumeration;
- mass-storage driver loading;
- SCSI device detection;
- partition recognition;
- filesystem detection;
- mount failures.

---

## 5. Interpreting the result

The experiment can produce several different outcomes.

### Case A — no USB device appears

If neither `/proc/partitions` nor `dmesg` shows the flash drive, USB mass-storage support may be missing from the kernel or disabled in the EO1 configuration.

In that case, using a USB flash drive as EO1-Museum storage would probably require kernel-level work and would not be an attractive development path.

### Case B — block device appears but is not mounted

For example:

    /dev/block/sda
    /dev/block/sda1

If this occurs, the EO1 kernel supports USB mass storage, but Android may lack automatic mounting support.

This would be an interesting result.

Manual mounting might eventually be possible if sufficient privileges are available, but no changes should be made until the device, filesystem, permissions, and root status have been understood.

### Case C — storage is already mounted

If the drive appears somewhere such as:

    /storage/...
    /mnt/...

then EO1-Museum may be able to access artwork directly from USB storage.

This would provide a possible architecture such as:

    USB flash drive
        ↓
    Android
        ↓
    native EO1-Museum
        ↓
    EO1 display

Such a configuration could potentially eliminate both the external PC and Wi-Fi after an exhibition has been prepared.

---

## 6. Do not modify Android storage configuration yet

The initial experiment should be diagnostic only.

At this stage, avoid modifying:

- `fstab`;
- `vold`;
- Android init scripts;
- internal partitions;
- bootloader configuration;
- internal eMMC filesystems.

The first objective is simply:

> Determine whether the EO1 kernel can see a USB mass-storage device.

This information alone will determine whether further USB-storage experiments are worthwhile.

---

## 7. Experiment B — the `spalt/EO1` Android project

A second and potentially more promising direction is the open-source Android project:

    https://github.com/spalt/EO1

The source code was examined as part of the EO1-Museum investigation.

Unlike MetBoot, which merely launches Firefox, this application was designed specifically to operate directly on the EO1.

Several features make it particularly interesting.

---

## 8. It can operate as the Android Home application

The application's `AndroidManifest.xml` contains both a normal launcher intent and an Android Home intent.

Conceptually:

    MAIN
      +
    HOME
      +
    DEFAULT

This means Android can potentially treat the application as its **Home/Launcher application**.

That is fundamentally different from the current MetBoot architecture.

Current EO1-Museum:

    Android
      ↓
    MetBoot
      ↓
    Firefox
      ↓
    HTML / JavaScript
      ↓
    artwork

A native application based on `spalt/EO1` could instead become:

    Android
      ↓
    EO1-Museum
      ↓
    artwork

This could eliminate the browser completely.

---

## 9. Native image display

The `spalt/EO1` application uses native Android display components including:

    ImageView
    VideoView

Images are loaded using Picasso.

The relevant architecture is essentially:

    image URL
       ↓
    Picasso
       ↓
    ImageView
       ↓
    EO1 display

This is particularly attractive for EO1-Museum because several current browser-related problems could disappear:

- Firefox user-interface remnants;
- browser borders;
- browser caching behavior;
- HTML startup delays;
- dependence on an old Firefox release;
- browser-specific fullscreen limitations.

A native Android application could control the entire 1080 × 1920 display directly.

---

## 10. EO1-specific hardware support already exists

The `spalt/EO1` source contains code specifically intended for the EO1 hardware.

This includes support for:

- ambient-light sensing;
- automatic screen brightness;
- manual brightness control;
- quiet hours;
- EO1 hardware button input;
- keyboard input;
- automatic slideshow progression.

The source also recognizes a top-button key event and can turn the display on or off by changing brightness and image visibility.

This is valuable because a new EO1-Museum application would not necessarily need to rediscover all of the EO1 hardware behavior from scratch.

---

## 11. Local Android storage is already used

The application requests:

    READ_EXTERNAL_STORAGE

It also contains code that accesses the Android public Downloads directory and reads:

    config.txt

Conceptually:

    Android Downloads
        ↓
    config.txt
        ↓
    EO1 application settings

This demonstrates that the application was designed to read files from Android-accessible external/public storage.

It does **not**, however, demonstrate that the EO1 Android system can mount a USB flash drive.

That is why the wireless ADB USB-storage experiment remains useful.

The two investigations complement each other:

    wireless ADB experiment
        ↓
    Can Android see USB storage?

and:

    spalt/EO1 investigation
        ↓
    Can a native EO1 application use local artwork?

---

## 12. The Flickr dependency

The original `spalt/EO1` application was designed around Flickr.

Its basic flow is:

    Flickr API
        ↓
    photo search/list
        ↓
    Flickr image URL
        ↓
    Picasso
        ↓
    ImageView

The Flickr-specific portion is relatively separable from the EO1-specific display logic.

This suggests that EO1-Museum could replace the Flickr layer while retaining much of the existing application structure.

For example:

    EO1-Museum metadata
        ↓
    artwork file or URL
        ↓
    Picasso / ImageView
        ↓
    EO1 display

The artwork source could initially remain the existing PC HTTP server.

This would minimize changes during the first experiment.

---

## 13. Proposed first native EO1-Museum experiment

The first goal should **not** be to rewrite the application immediately.

A safer sequence is:

### Stage 1 — build the original project

Obtain all required Android Studio project files and dependencies and determine whether the original `spalt/EO1` application can still be compiled.

Because the application uses older Android APIs and AndroidX components, dependency versions and Gradle configuration may require attention.

The target device remains:

    Android 4.4.x
    API level 19

Compatibility with the EO1 must therefore take priority over modernizing the code.

### Stage 2 — install without replacing the working setup

Install the resulting APK while preserving:

- original Android;
- MetBoot;
- Firefox;
- current EO1-Museum.

The existing working environment should remain recoverable.

### Stage 3 — test Home/Launcher behavior

Determine whether Android offers the application as a Home application.

If it does, test:

    power ON
       ↓
    Android boot
       ↓
    native EO1 application

Also determine how easily the launcher selection can be reversed.

### Stage 4 — verify EO1 hardware behavior

Test:

- portrait display;
- fullscreen rendering;
- top button;
- keyboard;
- ambient-light sensor;
- brightness control;
- quiet hours;
- slideshow timing.

Only after these functions are understood should the application be modified substantially.

---

## 14. First EO1-Museum modification

The simplest useful modification would be to remove the Flickr dependency from the slideshow while changing as little else as possible.

Instead of:

    Flickr
      ↓
    image URL

use:

    existing EO1-Museum HTTP server
      ↓
    image URL

For example:

    http://<PC-IP>:8000/display/0001.jpg
    http://<PC-IP>:8000/display/0002.jpg
    ...

The existing PC-side workflow could remain unchanged:

    GET_MET_ART_KEYWORD.py
        ↓
    original/
        ↓
    make_gallery.py
        ↓
    display/

Only the EO1 display layer would change:

    BEFORE

    PC HTTP server
        ↓
    Firefox
        ↓
    index.html
        ↓
    images.js
        ↓
    artwork

    AFTER

    PC HTTP server
        ↓
    native EO1-Museum Android app
        ↓
    ImageView
        ↓
    artwork

This would provide a clean comparison between the browser-based and native approaches.

---

## 15. Possible second stage — local artwork

If Android can access suitable local storage, the architecture could later become:

    local artwork
        ↓
    native EO1-Museum
        ↓
    ImageView

Possible storage locations might include:

- Android internal/public storage;
- application-specific storage;
- USB flash storage, if supported.

At that point the external PC might be required only when preparing or updating an exhibition.

A prepared exhibition could conceptually contain:

    exhibition/
    ├── images/
    │   ├── 0001.jpg
    │   ├── 0002.jpg
    │   └── ...
    ├── metadata.json
    └── exhibition.json

The EO1 could then operate offline.

---

## 16. Artwork metadata

A native application would also make it easier to integrate artwork metadata directly into the display.

For example:

    {
      "title": "Peonies",
      "artist": "Édouard Manet",
      "date": "1864–65",
      "medium": "Oil on canvas",
      "museum": "The Metropolitan Museum of Art",
      "rights": "Public Domain"
    }

Possible display modes include:

- image only;
- temporary caption when the artwork changes;
- metadata displayed on key press;
- small permanent caption;
- separate information screen.

The default mode should probably remain visually quiet, preserving the EO1's original character as an art display rather than turning it into a conventional tablet interface.

---

## 17. Landscape artwork

A native application could also improve the presentation of wide landscape-oriented artwork.

Instead of fitting the entire image inside the 1080 × 1920 portrait screen, the image could be scaled to fill the screen height and then slowly panned horizontally.

For example:

    source artwork
    5000 × 3000
         ↓
    scale to 3200 × 1920
         ↓
    EO1 viewport = 1080 × 1920

The application could animate:

    left
      ↓
    center
      ↓
    right
      ↓
    center
      ↓
    left

This could make landscape paintings considerably more effective on the EO1 portrait display.

---

## 18. Existing network-control capability

The `spalt/EO1` project contains another interesting feature: a background service that listens for commands over the network.

The service opens a TCP server on:

    port 12345

The original protocol recognizes commands associated with:

- image;
- video;
- resume;
- tag;
- brightness;
- options.

This appears to have been intended to allow another device to control the EO1.

For EO1-Museum, the same general idea could eventually be reused.

For example, a phone or PC could send commands such as:

    next artwork
    previous artwork
    select exhibition
    pause
    resume
    brightness
    show metadata

The original protocol need not necessarily be preserved exactly, but the source demonstrates that remote control was already part of the application's design.

---

## 19. Possible future architecture

If both experiments are successful, a particularly attractive configuration would be:

    USB or local artwork storage
             ↓
    original Android 4.4
             ↓
    native EO1-Museum Home application
             ↓
    ImageView
             ↓
    EO1 portrait display

Optional Wi-Fi could provide:

    phone / PC
        ↓
    local network
        ↓
    EO1-Museum control

In this architecture:

- Android remains intact;
- Linux is unnecessary;
- Firefox is unnecessary;
- the external PC is unnecessary during normal display;
- Internet access is unnecessary;
- Wi-Fi becomes optional;
- the EO1 can still be remotely controlled when desired.

The physical device could therefore approach the original goal of the Linux experiment:

    power ON
       ↓
    EO1-Museum
       ↓
    artwork

but without replacing the factory operating system.

---

## 20. Alternative if USB storage is unavailable

Failure of the USB-storage experiment would not prevent development of the native application.

Several alternatives remain.

### Android internal storage

A moderate collection of resized EO1 artwork could potentially be stored in available Android storage, subject to actual free-space limitations.

### Network-hosted artwork

The existing PC HTTP server can continue to provide images.

This is the easiest development configuration.

### Small external network server

A spare Android phone or another small device could provide both:

- a Wi-Fi hotspot;
- a local HTTP server containing the exhibition.

The EO1 would then require no conventional PC.

This may be simpler than modifying the EO1 kernel or bootloader.

---

## 21. Relationship to the Linux USB experiment

The Linux and Android experiments should be regarded as two different routes toward the same goal.

### Linux route

    EO1
      ↓
    USB Linux
      ↓
    local EO1-Museum
      ↓
    standalone display

Advantages:

- complete control over the software environment;
- modern Linux tools;
- easy local server and scripting.

Current problem:

- USB Linux boot has not yet been reproduced on this EO1.

### Android route

    EO1
      ↓
    original Android
      ↓
    native EO1-Museum
      ↓
    standalone display

Advantages:

- Android already boots reliably;
- LCD and EO1 hardware already work;
- no bootloader modification;
- existing EO1-specific open-source code is available;
- lower risk to the working device.

The Android route therefore deserves to be investigated before undertaking deeper U-Boot or hardware reverse-engineering.

---

## 22. Proposed development order

A cautious sequence is:

    1. Enable and verify wireless ADB
            ↓
    2. Connect USB storage through OTG
            ↓
    3. Determine whether Android detects the USB block device
            ↓
    4. Record the result without modifying the system
            ↓
    5. Rebuild the original spalt/EO1 application
            ↓
    6. Install and test it on the EO1
            ↓
    7. Verify Home/Launcher and hardware behavior
            ↓
    8. Replace Flickr with EO1-Museum HTTP images
            ↓
    9. Replace network images with local images if practical
            ↓
    10. Add metadata, landscape panning, and exhibition controls

Each stage should leave the existing Android/MetBoot/Firefox configuration recoverable until the replacement has proved reliable.

---

## 23. Immediate next experiments

### Experiment 1 — wireless ADB

Goal:

> Maintain an ADB shell over Wi-Fi while the EO1 micro-USB port operates in USB-host mode.

Record:

- EO1 IP address;
- whether `adb connect` succeeds;
- whether the connection survives removal of the USB ADB cable;
- whether the shell remains usable after attaching the OTG adapter.

### Experiment 2 — USB mass storage

Goal:

> Determine whether the Android kernel recognizes a FAT32 USB flash drive.

Record:

    mount
    ls -l /storage
    ls -l /mnt
    ls -l /dev/block
    cat /proc/partitions
    dmesg | tail -n 100

No system configuration should be changed during this experiment.

### Experiment 3 — original `spalt/EO1`

Goal:

> Build and run the original application with the minimum possible source modification.

Record:

- Android Studio / Gradle version;
- dependency problems;
- generated APK;
- installation result;
- Home/Launcher selection;
- image display;
- button behavior;
- ambient-light behavior;
- slideshow operation;
- network-control behavior.

---

## 24. Current working hypothesis

At this stage, the most promising development route appears to be:

    original EO1 Android
            +
    EO1-specific code from spalt/EO1
            +
    EO1-Museum artwork/metadata pipeline
            ↓
    native EO1-Museum application

The USB-storage experiment will determine whether the artwork itself can also reside on removable local media.

Even if USB storage proves unavailable, replacing Firefox with a native Android application could still substantially simplify EO1-Museum and provide better control over fullscreen presentation, metadata, brightness, hardware buttons, slideshow behavior, and landscape artwork.

The important principle remains the same as in the Linux experiment:

> **Preserve the working EO1 first; extend it only through reversible experiments.**
