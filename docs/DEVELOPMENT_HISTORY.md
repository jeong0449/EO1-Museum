# EO1-Museum Development History

_From a Browser-Based Revival to a Native Digital Museum Display_

**Written: October 30, 2026 · Covers development through v0.4**

EO1-Museum did not begin as an Android application. It began with a much simpler idea: **could an abandoned Electric Objects EO1 be brought back to life using its existing Android system and a web browser?**

The project gradually evolved from that browser-only experiment into a native Android application, and later into a small ecosystem for discovering, curating, transferring, and displaying open-access artworks. This document records that development path, including the experiments that worked, the approaches that were abandoned, and the reasons the architecture changed along the way.

---

## 1. Starting Point: An Art Frame Without Its Service

The Electric Objects EO1 was designed as a network-connected digital art display. Its distinctive 23-inch portrait screen and simple physical design remained perfectly usable, but the original ecosystem depended heavily on the manufacturer's online service.

After that service disappeared, the hardware was still functional but its intended content-delivery mechanism was no longer available.

The initial goal of EO1-Museum was therefore deliberately conservative:

> **Use as much of the original EO1 hardware and Android environment as possible, while replacing only the discontinued online service.**

There was no initial intention to replace Android, rebuild the kernel, or develop a new native application. The first question was simply whether the EO1 could display independently controlled web content.

---

## 2. Regaining Access to the EO1

An important starting point was Darius Kazemi's 2015 article, *Hack Your EO1*. It showed that the EO1 could be accessed as an Android device by connecting a keyboard and mouse through its micro-USB port with an OTG adapter or hub.

The Android browser could be opened with:

```text
Win + B
```

This seemingly small discovery was fundamental. It meant that the EO1 was not limited to the interface provided by Electric Objects. Its underlying Android environment remained accessible.

At this stage, the strategy was not to modify the operating system but simply to find a path from the existing Android installation to locally controlled content.

---

## 3. The Browser-Only Idea

The first EO1-Museum architecture was conceived almost entirely around the web browser.

The PC would do the computational work:

- discover and download artworks,
- process images for the EO1's 1080 × 1920 portrait display,
- generate a web gallery,
- and serve that gallery over the local network.

The EO1 would do only one thing: display that web gallery.

The architecture was therefore extremely simple:

```text
Open-access artwork
        ↓
PC-side discovery and processing
        ↓
Local HTTP server
        ↓
Wi-Fi
        ↓
EO1 web browser
        ↓
Fullscreen artwork display
```

This approach had several advantages. It required very little modification of the EO1, kept artwork management on the much more convenient PC, and made experimentation with HTML, JavaScript, image transitions, and gallery behavior easy.

Most importantly, it demonstrated that the EO1 could be made useful again without the original Electric Objects infrastructure.

---

## 4. Why Firefox Became Important

The built-in Android browser was sufficient for gaining access to the device and downloading files, but EO1-Museum needed a browser suitable for continuous unattended display.

Firefox 68.11.0 for ARM became the practical solution.

Firefox offered two particularly useful properties for the project:

- reliable fullscreen web-gallery presentation;
- persistence of the configured home page.

The EO1-Museum PC gallery URL could therefore be configured as the Firefox home page. Once Firefox started, the EO1 could return directly to the locally served gallery without requiring manual navigation.

This was important because the goal was not simply to prove that an image could be displayed. The EO1 needed to behave again like an appliance: power it on and let it display art.

Firefox was therefore not merely an installation tool. For the first stable EO1-Museum architecture, **Firefox was the gallery runtime itself**.

---

## 5. MetBoot: Making the Browser Architecture Unattended

The next problem was startup.

A digital art frame should not require a keyboard and mouse every time it is powered on. To solve this, a small Android helper called **MetBoot** was created.

Its job was deliberately narrow:

```text
Android boot
     ↓
BOOT_COMPLETED
     ↓
MetBoot
     ↓
Firefox
     ↓
Configured EO1-Museum home page
```

MetBoot did not manage artworks and did not run the gallery server. It simply launched Firefox after Android finished booting.

Together, Firefox and MetBoot produced the first genuinely practical EO1-Museum system:

```text
PC
 ├── artwork discovery
 ├── image processing
 └── HTTP gallery server
             │
             │ Wi-Fi
             ▼
EO1 Android
     ↓
MetBoot
     ↓
Firefox
     ↓
EO1-Museum web gallery
```

At this stage, **ADB was not required for normal setup or operation**. The project was still fundamentally a browser-based revival.

This was an important milestone: the EO1 could once again function as a dedicated art display without relying on the original Electric Objects service.

---

## 6. The Limits of the Browser-Based System

The browser solution worked surprisingly well, but its architecture had one fundamental limitation:

> **The EO1 still depended on another computer.**

The PC had to remain available to serve the gallery, and the EO1 required a working Wi-Fi connection to display it.

That was acceptable for the original experiment, but it raised a new question:

> Could the EO1 store the exhibition itself and display artwork without a PC or network connection?

The EO1 already had usable internal storage. If artwork could be placed there and displayed by a native application, the device could become a genuinely standalone digital art frame.

This changed the direction of the project.

The goal was no longer simply to restore the original EO1 experience through a browser. The next goal was to build a **native Local Gallery**.

---

## 7. ADB Becomes Necessary

Native Android development introduced a requirement that the browser-only system had avoided: **ADB**.

APK development, installation, debugging, filesystem inspection, and transferring test exhibitions were much easier through Android Debug Bridge.

But the EO1 presented an unusual physical problem.

Its micro-USB port was needed both for:

- USB OTG keyboard/mouse input, and
- connection to a development PC for USB ADB.

When the EO1 was first connected to a development PC, Android displayed the normal RSA authorization dialog. But once the micro-USB port was connected to the PC, the OTG mouse could no longer be used to click **OK**.

The device had no touchscreen.

This created a small but very real bootstrap problem.

---

## 8. ADBApprovalHelper

To solve the ADB authorization problem, **ADBApprovalHelper.apk** was created.

It uses an Android AccessibilityService to detect the USB debugging authorization dialog and automatically:

1. select **Always allow from this computer**, and
2. activate **OK**.

This utility belongs specifically to the native-development phase of EO1-Museum.

It is important to distinguish this from the earlier Firefox architecture:

```text
Browser-only EO1-Museum
    → ADB not required

Native EO1-Museum development
    → ADB required
    → RSA authorization problem
    → ADBApprovalHelper
```

Firefox, MetBoot, and ADBApprovalHelper were therefore not originally parts of a single installation chain. They arose at different stages of the project in response to different problems.

This distinction later became important when documenting the current installation procedure.

---

## 9. Experiments Beyond Android

Before committing fully to the native Android approach, several alternative paths were investigated.

### USB Mass Storage

Using a USB flash drive as removable artwork storage initially appeared attractive. The EO1 correctly detected standard USB mass-storage hardware at the USB level, but no block device appeared.

Inspection of the stock kernel configuration revealed the decisive limitation:

```text
# CONFIG_SCSI is not set
```

The Android kernel therefore lacked the SCSI layer required by ordinary USB mass-storage block devices.

Adding USB storage would have required kernel-level work that was disproportionate to the actual goal of displaying artwork.

The experiment was therefore abandoned.

### Linux USB Boot

Linux booting was also investigated, inspired in part by Charlie Harrington's work running Linux on the EO1.

Several Boundary Devices/i.MX6-related Linux images were tested, but the EO1 continued to boot its existing Android installation.

Further investigation would have required deeper bootloader or hardware work, potentially including UART access.

Because Linux was not necessary to achieve a standalone gallery, this path was deliberately deferred.

These experiments led to an important design decision:

> **EO1-Museum did not need to turn the EO1 into a general-purpose computer. The existing Android system was already sufficient.**

---

## 10. The Native Application and spalt/EO1

The transition to a native application became substantially more practical because of the **spalt/EO1** repository.

Rather than reconstructing an EO1 Android application entirely from scratch, EO1-Museum adopted the preserved EO1 source code as its starting point and progressively modified it for a new purpose.

This was a major turning point.

The project could now build on code that already understood important aspects of the EO1 hardware and Android environment while removing or replacing functionality tied to the original service.

**Special thanks are due to spalt for preserving and sharing the EO1 source code.** Its availability made the transition from a browser workaround to a native EO1 application substantially more practical.

---

## 11. Native Local Gallery

The first major native goal was deliberately modest:

> Display JPEG and PNG artwork stored in the EO1's internal storage as a fullscreen slideshow.

Artwork could be placed under the EO1-Museum storage area and displayed without contacting the PC.

Conceptually:

```text
PC
 │
 │ artwork transfer
 ▼
EO1 internal storage
 │
 ▼
EO1 Museum
 │
 ▼
Native fullscreen gallery
```

This changed the nature of the project.

For the first time, the EO1 could contain its own exhibition and continue displaying it after the PC and network were removed.

The application subsequently gained additional capabilities, including:

- image and MP4 playback,
- Bluetooth audio for video,
- mouse-accessible controls,
- cross-fade transitions,
- a clock overlay,
- media rescanning,
- and automatic operation as the Android HOME application.

The EO1 was becoming self-contained again.

---

## 12. The Web Architecture Returns — Inside the Native App

Moving to a native Local Gallery did not make the earlier web architecture useless.

The PC-based gallery remained convenient. HTML and JavaScript were still effective for displaying collections prepared on the PC, and network viewing made it possible to change exhibitions without first transferring them to the EO1.

Instead of choosing permanently between the web and native approaches, EO1-Museum combined them.

In v0.3, an Android WebView was incorporated into the native application as **PC Gallery**.

The architecture became:

```text
Android
   ↓
EO1 Museum
   ├── Local Gallery
   │      └── EO1 internal storage
   │
   └── PC Gallery
          └── PC HTTP server
```

This was an important architectural convergence.

Firefox and MetBoot were no longer required for normal operation because the native application could provide both modes itself.

The browser-based architecture had not really disappeared.

**It had been absorbed into the native application.**

---

## 13. From PC Gallery to Safe Sync

Once Local Gallery and PC Gallery existed inside the same application, another possibility became obvious.

PC Gallery already connected the EO1 to the computer containing the newly prepared exhibition. Why should that connection be limited to viewing the gallery remotely?

In v0.4, PC Gallery became the entry point for **Safe Sync**.

When synchronization is explicitly enabled on the PC, the EO1 can transfer the prepared gallery over Wi-Fi into its internal storage.

The PC remains the master copy of the exhibition, while the EO1 receives a local copy for independent playback.

The current workflow is:

```text
Artwork discovery
        ↓
PC-side curation
        ↓
Gallery preparation
        ↓
PC Gallery
        ↓
Safe Sync
        ↓
EO1 internal storage
        ↓
Local Gallery
```

Synchronization is intentionally optional. The PC server determines whether synchronization is permitted for that session, and the EO1 verifies the identity of the server before accepting it.

Transfers are designed conservatively. Files are downloaded to temporary files before replacing the existing copies, storage limits are respected, and progress is shown directly on the EO1.

After synchronization, neither the PC nor the network is required for normal Local Gallery operation.

---

## 14. Artwork Discovery Becomes Part of the Project

While the Android side was evolving, the PC side of EO1-Museum also expanded.

The project originally concentrated on The Metropolitan Museum of Art Open Access collection. Structured museum metadata made it possible to discover works by artist, keyword, subject, culture, period, and other attributes.

Wikimedia Commons was later added as a broader discovery source.

The two sources serve somewhat different purposes:

```text
The Met
   ↓
Structured institutional discovery

Wikimedia Commons
   ↓
Broad cross-collection discovery
```

Commons also made another issue more obvious: automated discovery is not the same thing as curation.

An image may be legally reusable and technically high-resolution while still being a poor reproduction of an artwork. Persistent reject lists were therefore introduced so that machine-assisted discovery could be combined with human visual judgment.

The resulting philosophy is increasingly:

```text
machine discovery
      +
metadata and rights filtering
      +
human curation
      ↓
digital exhibition
```

This broader aspect of EO1-Museum can be thought of as a small experiment in **Fine Art Informatics**: using cultural data, metadata, computation, curation, and digital presentation as parts of one workflow.

---

## 15. How the Architecture Evolved

The development path can now be summarized in a few stages:

```text
Original EO1 service disappears
        ↓
Regain access to Android
        ↓
Browser-only experiment
        ↓
Firefox web gallery
        ↓
MetBoot unattended startup
        ↓
Stable PC-dependent EO1-Museum
        ↓
Need for standalone operation
        ↓
ADB + ADBApprovalHelper
        ↓
Native Android Local Gallery
        ↓
Native HOME application
        ↓
PC Gallery integrated through WebView
        ↓
Safe Sync
        ↓
Standalone Local Gallery with PC-assisted curation
```

Or, more compactly:

```text
Web
 ↓
Native
 ↓
Web + Native
 ↓
Synchronized Web + Native
```

This evolution was not planned from the beginning.

Each architecture solved the limitation exposed by the previous one.

---

## 16. What Was Preserved

An important principle throughout development has been to avoid modifying the EO1 more deeply than necessary.

EO1-Museum still uses the original Android installation. It does not require a replacement kernel, a Linux installation, or destructive modification of the internal system.

Several earlier components also remain valuable even when they are no longer required for normal operation:

- **Firefox 68.11.0** documents and preserves the first stable web-gallery approach.
- **MetBoot** preserves the solution used for unattended Firefox startup.
- **ADBApprovalHelper** remains useful for initial ADB authorization and maintenance.
- Linux and USB-storage experiments document alternative approaches and the reasons they were not pursued.

These are not simply obsolete files. Together they record how the project reached its current architecture.

---

## 17. Where EO1-Museum Stands Today

As of October 30, 2026, EO1-Museum is no longer merely a workaround for a discontinued online service.

It consists of several connected layers:

```text
Open cultural collections
        ↓
Artwork discovery
        ↓
Metadata and rights filtering
        ↓
Human curation
        ↓
PC gallery preparation
        ↓
PC Gallery
        ↓
Optional Safe Sync
        ↓
EO1 Local Gallery
        ↓
1080 × 1920 portrait display
```

The EO1 itself can operate independently after synchronization, while the PC remains the more capable environment for discovery, collection management, and exhibition preparation.

This division of labor suits the hardware well.

The PC handles complexity.

The EO1 displays art.

---

## 18. A Project Shaped by Earlier Work

EO1-Museum would not exist in its present form without earlier people who investigated and documented the EO1 after and even before the end of its commercial ecosystem.

**Darius Kazemi** demonstrated how the underlying Android environment could be accessed and explored.

**Christian Boyle** showed a practical Firefox-based route for bringing an EO1 back into service with locally controlled web content.

**spalt** preserved and shared EO1 Android source code that became the practical foundation for EO1-Museum's native application.

**Charlie Harrington** demonstrated that the EO1 hardware could also be approached as a small i.MX6 Linux computer, opening another possible direction even though EO1-Museum ultimately remained with Android.

Their work represents different answers to the same underlying question:

> What can this hardware become after the service it was designed for disappears?

EO1-Museum is one continuation of that exploration.

---

## 19. The Continuing Goal

The project began by trying to make an old digital frame display pictures again.

Its purpose has gradually become more specific.

The goal is not to transform the EO1 into a modern tablet, general-purpose Android device, or miniature PC. Modern hardware could perform those jobs much better.

The EO1 has something else worth preserving: a large, quiet, portrait-oriented display designed specifically for living with visual art.

EO1-Museum therefore tries to preserve that identity while replacing the infrastructure that disappeared around it.

The technical architecture has changed repeatedly:

**browser → native application → integrated PC Gallery → Safe Sync**

but the underlying objective has remained remarkably constant:

> **Give the EO1 a useful second life as a quiet, dedicated window into art.**
