# Experimental Linux USB Boot on the Electric Objects EO1

> **Status: Experimental**
>
> Linux has previously been booted successfully on an Electric Objects EO1 from a USB flash drive. However, attempts to reproduce USB booting as part of the EO1-Museum project on **20 October 2026** were unsuccessful. Both a **Yocto Hardknott Nitrogen6X image** and an **Ubuntu Bionic XFCE ARMHF Nitrogen6X image** were tested, using direct USB OTG connection as well as a powered USB hub. In every case, the EO1 ignored the USB image and booted its original Android system normally.
>
> These results do not establish that USB Linux booting is impossible on the EO1, but they suggest that differences in bootloader configuration, image compatibility, or EO1 firmware may be involved. The detailed test record is provided in **Section 10.1**.
>
> The existing Android installation and internal eMMC were not modified during these experiments and should be preserved while the USB boot mechanism remains unresolved.

## 1. Why boot Linux on the EO1?

EO1-Museum currently uses the following architecture:

```text
Museum open-access collection
        ↓
PC downloads and prepares artwork
        ↓
PC runs local web server
        ↓
Wi-Fi network
        ↓
EO1 / Android
        ↓
MetBoot
        ↓
Firefox
        ↓
EO1-Museum gallery
```

This works well in a home or office environment, but it has one important limitation: the EO1 depends on both an external PC and a local network.

For installations such as museum exhibitions, conference booths, demonstrations, or other temporary displays, it would be useful for the EO1 to operate independently.

A possible future architecture is:

```text
EO1 power ON
        ↓
Linux boots from USB flash drive
        ↓
Local EO1-Museum software
        ↓
Local artwork collection
        ↓
Fullscreen display
```

In this configuration, the USB flash drive could potentially contain:

- the Linux operating system;
- EO1-Museum;
- artwork images;
- artwork metadata;
- a lightweight web server or image viewer;
- startup scripts.

The EO1 could then become a self-contained digital museum display requiring only electrical power.

---

## 2. EO1 hardware

A teardown of the Electric Objects EO1 identified the main processor as:

```text
Freescale MCIMX6D5EYM10AC
```

This is an **i.MX 6Dual** system-on-chip using two ARM Cortex-A9 CPU cores running at up to 1 GHz.

The i.MX 6 family was originally developed by Freescale Semiconductor. Freescale was subsequently acquired by NXP Semiconductors, and the i.MX product family continues under NXP.

Relevant EO1 hardware includes approximately:

```text
CPU       Freescale i.MX 6Dual
CPU core  Dual ARM Cortex-A9
Clock     1 GHz
RAM       approximately 1 GB
Storage   4 GB eMMC
Display   1920 × 1080 LCD mounted in portrait orientation
OS        Android 4.4.x in the original EO1 configuration
USB       micro-USB with USB OTG support
```

The USB OTG capability is particularly important because it allows the EO1 to act as a USB host.

With an OTG adapter and powered USB hub, devices such as the following can be attached:

```text
EO1 micro-USB
      │
      └── OTG adapter
             │
             └── powered USB hub
                    ├── keyboard
                    ├── mouse
                    └── USB flash drive
```

This basic arrangement has already been used by EO1 owners for both Android access and Linux boot experiments.

### Hardware references

- EO1 teardown:  
  https://www.5khz.com/2016/05/01/electric-objects-eo1-digital-art-display-teardown/

- NXP i.MX 6 family:  
  https://www.nxp.com/

---

## 3. Relationship to the Boundary Devices Nitrogen6X

The EO1 appears to be closely related to hardware designed by **Boundary Devices**, particularly the **Nitrogen6X** platform.

Several observations support this connection.

When an EO1 was connected through USB during an earlier teardown, the device identified itself as:

```text
NITROGEN6X
```

The EO1 also uses an i.MX 6 processor, the same processor family supported by the Nitrogen6X platform.

This relationship is important because Boundary Devices produced Linux and Android board-support software for its i.MX6 hardware.

Boundary Devices documentation and software are now hosted by **Ezurio**.

Current i.MX6 software information can be found here:

https://www.ezurio.com/documentation/i-mx6-builds

Nitrogen6X documentation:

https://bdwiki.ezurio.com/index.php/Nitrogen6x

The available operating-system families include:

- Yocto Linux
- Ubuntu
- Debian
- Buildroot
- Android

However, the EO1 is **not necessarily electrically identical to a retail Nitrogen6X board**.

Therefore:

> A Linux image supporting Nitrogen6X should be considered a strong candidate for EO1 experimentation, not a guarantee of complete hardware compatibility.

Display configuration, Wi-Fi, audio, GPIO, boot configuration, and other peripherals may differ.

---

## 4. Previous successful Linux boot

The most important precedent is Charlie Harrington's 2022 experiment:

**Run Linux on Electric Objects EO1 Wall Computer**

https://charlieharrington.com/run-linux-on-electric-objects-eo1-wall-computer/

Harrington identified Boundary Devices as the manufacturer of the EO1 board and downloaded one of its Linux builds.

His basic procedure was:

```text
Boundary Devices Linux image
        ↓
write image to USB thumb drive
        ↓
connect USB drive + keyboard + mouse to USB hub
        ↓
connect hub through micro-USB OTG adapter
        ↓
connect to EO1
        ↓
boot Linux
```

He successfully turned the EO1 into a portrait-oriented Linux computer.

He later used the Linux installation to:

- download the New York Times front page automatically;
- display the PDF fullscreen using Evince;
- launch the display automatically at boot using cron;
- prevent the display from sleeping;
- experiment with remote administration using SSH/Tailscale.

This provides direct evidence that **USB Linux boot on at least one EO1 is possible**.

However, Harrington's article does not clearly identify the exact downloadable image filename or release used in his experiment.

That detail therefore remains to be reproduced independently.

---

## 5. Candidate Linux distributions

Boundary Devices/Ezurio has provided several Linux environments for i.MX6/Nitrogen6X hardware.

### 5.1 Yocto Linux

Yocto is currently one of the most clearly documented options for a first USB boot experiment.

Ezurio provides prebuilt Nitrogen6X images.

One documented release is Yocto Hardknott:

https://www.ezurio.com/documentation/yocto-hardknott-release-for-i-mx6-platforms

The Nitrogen6X image listed there is:

```text
20210922-boundary-image-multimedia-full-nitrogen6x.wic.gz
```

The image uses a Linux 5.10 kernel.

Ezurio explicitly documents that the `.wic.gz` image can be written to:

- eMMC;
- SD card;
- USB stick.

Under Linux, the documented form is:

```bash
zcat *boundary-image*.wic.gz | sudo dd of=/dev/sdX bs=1M
```

where `/dev/sdX` must be replaced with the correct USB device.

**Warning:** specifying the wrong device with `dd` can destroy data on another disk.

Windows and Linux users can alternatively use **balenaEtcher** to write the image to a USB flash drive.

For the initial EO1 experiment, using balenaEtcher is probably safer and simpler than using `dd`.

---

### 5.2 Yocto Dunfell

Another documented Nitrogen6X image is Yocto Dunfell:

```text
20201102-boundary-image-multimedia-full-nitrogen6x.wic.gz
```

This release uses a Linux 5.4 kernel.

Documentation:

https://www.ezurio.com/documentation/yocto-dunfell-release-for-i-mx6-i-mx7-platforms

Like the Hardknott release, Ezurio explicitly documents writing the image to a USB stick.

---

### 5.3 Ubuntu

Boundary Devices has also supplied Ubuntu images for i.MX6/Nitrogen6X systems.

Older documented releases include:

- Ubuntu Bionic 18.04
- Ubuntu Xenial 16.04
- Ubuntu Trusty 14.04
- earlier Ubuntu/Linaro builds

See:

https://www.ezurio.com/documentation/i-mx6-builds

Ubuntu may eventually be attractive for EO1-Museum because a familiar Linux environment would make it relatively easy to use:

- Python;
- shell scripts;
- X11;
- lightweight web servers;
- browsers;
- SSH;
- common package-management tools.

Harrington describes the Linux system used in his EO1 experiment as an Ubuntu distribution, but the exact image/version used should not be assumed without further evidence.

---

### 5.4 Debian

Debian images and installation procedures have also been published for Nitrogen6X/i.MX6.

Examples include Debian Jessie, Stretch, and Buster-era environments.

Documentation:

https://www.ezurio.com/documentation/i-mx6-builds

Nitrogen6X wiki:

https://bdwiki.ezurio.com/index.php/Nitrogen6x

Debian may be useful if a relatively lightweight but conventional Linux distribution is preferred.

---

### 5.5 Buildroot

Buildroot is different from Ubuntu or Debian.

Rather than providing a conventional general-purpose desktop distribution, Buildroot can be used to create a small Linux system containing only the software required by the application.

Boundary Devices/Ezurio has long supported Buildroot on Nitrogen6X hardware.

For EO1-Museum this could eventually be particularly interesting.

A dedicated system might contain only:

```text
Linux kernel
    +
display support
    +
USB storage
    +
networking (optional)
    +
small web server
    +
browser/viewer
    +
EO1-Museum
```

The resulting appliance could potentially behave like:

```text
power ON
   ↓
boot
   ↓
start EO1-Museum
   ↓
fullscreen artwork
```

with no normal desktop environment exposed to the user.

This may ultimately be more appropriate for an exhibition appliance than a full Ubuntu installation.

For initial hardware testing, however, a prebuilt Nitrogen6X image is preferable.

---

## 6. Recommended first experiment

The first objective should **not** be to install Linux permanently.

The objective should simply be:

> Determine whether this particular EO1 can boot a known Nitrogen6X-compatible Linux image from USB.

A reasonable first candidate is:

```text
Yocto Hardknott
20210922-boundary-image-multimedia-full-nitrogen6x.wic.gz
```

Reasons:

1. it is explicitly intended for Nitrogen6X-class i.MX6 hardware;
2. a prebuilt image is available;
3. Ezurio documents USB-stick installation;
4. it uses a relatively modern 5.10 kernel;
5. no custom Linux build is required for the first experiment.

The first test should change **nothing** on the internal eMMC.

---

## 7. Required hardware

Suggested equipment:

```text
Electric Objects EO1
micro-USB OTG adapter
powered USB hub
USB keyboard
USB mouse
USB flash drive
PC for preparing the USB drive
```

A powered hub is strongly recommended.

The EO1's micro-USB port should not be expected to provide reliable power for several USB devices simultaneously.

For the first experiment, an inexpensive USB flash drive that contains no important data should be used.

A capacity of several GB or more should normally be sufficient, depending on the image selected.

---

## 8. Preparing the USB drive

### Windows

A straightforward method is to use balenaEtcher.

General procedure:

1. Download the appropriate Nitrogen6X image.
2. Keep the downloaded `.wic.gz` file compressed unless the flashing utility requires otherwise.
3. Insert the USB flash drive.
4. Start balenaEtcher.
5. Select the downloaded image.
6. Select the USB flash drive.
7. Verify the selected destination carefully.
8. Flash the image.
9. Allow verification to complete.
10. Safely remove the USB drive.

Do not copy the `.wic.gz` file onto a FAT32 USB drive as an ordinary file.

The image must be written as a **disk image**.

---

## 9. Proposed EO1 connection

For the first boot experiment:

```text
                    ┌── USB keyboard
                    │
EO1 ─ OTG ─ powered USB hub ── USB mouse
                    │
                    └── Linux USB flash drive
```

Then power-cycle the EO1.

Observe:

- whether Android starts normally;
- whether Linux begins booting;
- whether a boot menu appears;
- whether the display changes resolution;
- whether keyboard input works;
- whether the USB drive activity LED shows access;
- how long booting takes.

Do not assume failure immediately if the screen remains blank.

The kernel could potentially be booting with an incompatible display configuration.

A serial console may eventually be necessary for diagnosis.

---

## 10. Bootloader considerations

i.MX6 systems commonly use **U-Boot**.

The actual EO1 boot configuration has not yet been documented as part of EO1-Museum.

Important unanswered questions include:

- Which U-Boot version is installed?
- What is the EO1 boot order?
- Does it automatically search USB storage?
- Does it require a specific filesystem or partition layout?
- Does it search for particular filenames?
- Does it use Boundary Devices boot scripts?
- Does inserting a USB boot device automatically override eMMC Android?
- Is keyboard interaction with U-Boot possible?
- Is a serial console accessible?

Harrington's successful experiment strongly suggests that the factory EO1 boot environment can boot an appropriately prepared USB device.

However, the exact mechanism still needs to be documented.

### 10.1 Experiment log — 20 October 2026

The first EO1-Museum attempts to reproduce USB Linux booting were carried out on **20 October 2026**. The purpose was simply to determine whether the existing EO1 bootloader would select a prepared USB Linux image. The internal eMMC and the working Android/MetBoot installation were not modified.

Two Nitrogen6X-compatible Linux images were tested.

#### Test 1 — Yocto Hardknott

The first image tested was:

    20210922-boundary-image-multimedia-full-nitrogen6x.wic.gz

This is the Yocto Hardknott image described earlier in this document. The image was written to an **8 GB USB flash drive** using balenaEtcher, including the verification step.

The following configurations were tested:

    Yocto USB connected directly through OTG  → Android booted normally
    Yocto USB connected through powered hub   → Android booted normally

In both cases, the EO1 ignored the USB Linux image and proceeded to boot its original Android system. No Linux boot screen or boot menu appeared.

#### Test 2 — Ubuntu Bionic XFCE ARMHF

A second experiment used the following Ubuntu image:

    20220204-nitrogen6x-4.14.x_2.0.1_ga-bionic-en_US-xfce_armhf.img.gz

The image was written to a **32 GB USB flash drive**. After flashing, Windows Disk Management showed an image-created partition of approximately 3.5 GB, with the remaining space left unallocated. No attempt was made to resize or modify the partitions.

The following configurations were tested:

    Ubuntu USB connected directly through OTG       → Android booted normally
    Ubuntu USB + powered hub + keyboard              → Android booted normally
    Repeated Space/Enter key presses during startup  → no visible effect

Again, the EO1 continued to boot Android normally. No Linux boot screen or interactive bootloader prompt appeared.

#### Summary

The results of the experiment were therefore:

    Yocto USB direct              → Android
    Yocto USB + powered hub       → Android
    Ubuntu Bionic USB direct      → Android
    Ubuntu + powered hub+keyboard → Android
    boot-time keypress            → no visible effect

These results do **not** demonstrate that USB Linux booting is impossible on the EO1. Charlie Harrington's 2022 experiment remains direct evidence that at least one EO1 could boot Linux from a USB flash drive.

They do show, however, that simply flashing the tested Nitrogen6X images to USB was insufficient on this particular EO1.

One possible explanation is a mismatch between the EO1's factory U-Boot environment and the boot scripts or partition layout expected by these later Boundary Devices images. Differences in firmware or bootloader versions between EO1 units are also possible. These possibilities have not been verified.

Further diagnosis would probably require identifying the installed U-Boot version and boot environment, potentially through a serial/UART console. This would require substantially deeper hardware investigation and may involve opening the EO1 and locating or soldering to serial test points. For the present EO1-Museum project, this is considered beyond the desired scope.

Importantly, the internal eMMC was not modified during any of these tests. After each experiment, the EO1 continued to boot normally into the existing Android/MetBoot/Firefox environment.

For now, the working Android-based EO1-Museum configuration therefore remains the known-good platform, while Linux USB boot is retained as a documented experimental path rather than an immediate development target.

---

## 11. Protecting the internal eMMC

The EO1 contains approximately 4 GB of internal eMMC storage.

The original Android system resides there.

The current EO1-Museum configuration also depends on that Android environment:

```text
internal eMMC
     ↓
Android
     ↓
MetBoot
     ↓
Firefox
     ↓
EO1-Museum
```

Until USB Linux booting has been fully understood:

> **Do not flash, repartition, format, or otherwise modify the internal eMMC.**

The ideal experimental configuration is:

```text
eMMC
└── original Android + MetBoot
        preserved

USB flash drive
└── experimental Linux
```

This would potentially allow two modes:

```text
USB absent
    ↓
Android + MetBoot + Firefox
    ↓
current EO1-Museum

USB present
    ↓
Linux
    ↓
future standalone EO1-Museum
```

Whether the EO1 bootloader actually behaves this way remains to be tested.

---

## 12. Backing up the eMMC

If USB Linux boots successfully and the internal eMMC becomes visible as a Linux block device, making a complete backup should be considered before any further experimentation.

First identify storage devices carefully:

```bash
lsblk
```

and:

```bash
cat /proc/partitions
```

Do **not** assume a device name.

Depending on the system, internal eMMC devices commonly appear with names such as:

```text
/dev/mmcblk0
/dev/mmcblk1
```

but the actual EO1 configuration must be inspected.

A future full-device backup might conceptually use a command such as:

```bash
dd if=/dev/mmcblkX of=/path/to/usb/eo1-emmc-backup.img bs=4M status=progress
```

where `mmcblkX` must be replaced only after the internal eMMC has been positively identified.

This command is shown for documentation only.

Using the wrong source or destination device can destroy data.

The backup procedure should therefore be treated as a separate experiment after USB boot has been confirmed.

---

## 13. Goal: standalone EO1-Museum

Once Linux boot is reliable, the next objective would be to eliminate the external PC.

The USB filesystem could contain something like:

```text
/
├── Linux system
└── opt/
    └── eo1-museum/
        ├── index.html
        ├── images.js
        ├── display/
        │   ├── 0001.jpg
        │   ├── 0002.jpg
        │   └── ...
        ├── metadata/
        └── scripts/
```

At startup:

```text
Linux boot
    ↓
mount local storage
    ↓
start display service
    ↓
launch fullscreen viewer
    ↓
show exhibition
```

No Internet connection would be required.

No Wi-Fi connection would be required.

No external PC would be required.

This would be especially useful for:

- conference booths;
- exhibitions;
- museums;
- classrooms;
- public displays;
- temporary installations.

---

## 14. Does EO1-Museum still need a web server?

Not necessarily.

There are several possible architectures.

### Option A — local web server

```text
Linux
 ↓
Python/lightweight HTTP server
 ↓
localhost
 ↓
fullscreen browser
```

Advantages:

- minimal changes to the existing EO1-Museum code;
- existing HTML/JavaScript gallery can be reused;
- easy development and debugging.

For example:

```text
http://127.0.0.1:8000/
```

The browser and server would both run on the EO1.

This is probably the easiest path from the current project.

### Option B — local file display

The browser could potentially open:

```text
file:///opt/eo1-museum/index.html
```

This removes the web server entirely.

Browser security restrictions and JavaScript behavior would need to be tested.

### Option C — dedicated viewer

A lightweight Qt, SDL, framebuffer, or other native viewer could eventually replace the browser.

This might reduce memory usage and provide complete control over:

- fullscreen display;
- transitions;
- artwork metadata;
- image panning;
- portrait/landscape handling.

This would represent a larger redesign.

---

## 15. Landscape artwork

A standalone Linux implementation could also address one of the current EO1-Museum limitations.

The EO1 is physically portrait-oriented:

```text
1080 × 1920
```

A wide landscape artwork currently needs to be scaled down significantly to fit entirely within the screen.

Instead, the image could be scaled so that its **height** fills the 1920-pixel display.

For example:

```text
original artwork
5000 × 3000

scale height to 1920
        ↓
3200 × 1920
```

The EO1 could then act as a 1080-pixel-wide viewport into the larger image:

```text
[ 1080 px viewport ]
<-------------------- 3200 px artwork -------------------->
```

The display could slowly pan:

```text
left
  ↓
center
  ↓
right
  ↓
center
  ↓
left
```

This may provide a more interesting presentation of wide paintings than simply shrinking them to fit the portrait screen.

---

## 16. Artwork metadata

A future standalone EO1-Museum could keep both images and metadata locally.

For example:

```json
{
  "title": "Peonies",
  "artist": "Édouard Manet",
  "date": "1864–65",
  "medium": "Oil on canvas",
  "museum": "The Metropolitan Museum of Art",
  "rights": "Public Domain"
}
```

The display could optionally show this information:

- permanently;
- briefly when an artwork appears;
- as a caption;
- on keyboard input;
- on a timed overlay.

The metadata could also support offline exhibition selection.

---

## 17. Offline exhibitions

A fully standalone version should not require online museum APIs during an exhibition.

The exhibition should be prepared in advance.

For example:

```text
exhibitions/
├── impressionism/
├── japanese-art/
├── joseon/
├── landscapes/
└── flowers/
```

Each exhibition could contain:

```text
images
metadata
rights information
playlist/order
display settings
```

The exhibition computer could therefore be prepared before arriving at the venue.

At the booth:

```text
connect power
      ↓
EO1 boots
      ↓
exhibition starts
```

That is the desired final behavior.

---

## 18. Network should become optional

Linux support does not mean networking should be removed.

Instead, networking should become optional.

Possible modes:

### Offline mode

```text
USB artwork
    ↓
EO1
```

### Local-network mode

```text
PC
 ↓
Wi-Fi
 ↓
EO1
```

### Online mode

```text
museum API
 ↓
EO1 or PC
```

A robust exhibition appliance should continue displaying its local exhibition even if all network connections disappear.

---

## 19. Development stages

A cautious development sequence is recommended.

### Stage 1 — prove USB Linux boot

Goal:

```text
EO1 successfully boots Linux from USB
```

No changes to eMMC.

### Stage 2 — verify hardware

Check:

- LCD;
- USB;
- keyboard;
- mouse;
- internal eMMC visibility;
- networking;
- GPU/framebuffer;
- display rotation.

### Stage 3 — run a local image

Display one JPEG fullscreen.

### Stage 4 — run EO1-Museum locally

Copy a small EO1-Museum exhibition to the USB drive and display it using localhost.

### Stage 5 — automatic startup

Configure:

```text
power ON
 ↓
Linux
 ↓
EO1-Museum
```

with no keyboard or mouse.

### Stage 6 — offline exhibition

Disconnect:

- Wi-Fi;
- Ethernet;
- external PC.

Verify that the exhibition continues normally.

### Stage 7 — appliance optimization

Consider:

- Buildroot;
- read-only root filesystem;
- watchdog/recovery;
- graceful handling of power loss;
- automatic slideshow recovery;
- dedicated fullscreen viewer.

---

## 20. What should NOT be done yet

Until the basic USB boot experiment has succeeded, avoid:

- flashing the EO1 eMMC;
- replacing the factory bootloader;
- modifying U-Boot environment variables unnecessarily;
- repartitioning internal storage;
- upgrading firmware blindly;
- assuming every Nitrogen6X image is fully compatible;
- relying on network installation;
- dismantling a working Android/MetBoot installation.

The existing Android EO1-Museum configuration works.

It should remain the known-good recovery environment.

---

## 21. First experiment checklist

Before starting:

```text
[ ] Working EO1 confirmed
[ ] Current Android + MetBoot still boots normally
[ ] Powered USB hub available
[ ] OTG adapter available
[ ] USB keyboard available
[ ] USB mouse available
[ ] Spare USB flash drive available
[ ] No important data on USB flash drive
[ ] Nitrogen6X image downloaded
[ ] Image source verified
[ ] USB image flashed successfully
[ ] Internal eMMC will not be modified
```

First boot:

```text
[ ] USB drive inserted
[ ] Keyboard connected
[ ] Mouse connected
[ ] Powered hub powered
[ ] Hub connected to EO1 OTG port
[ ] EO1 power cycled
[ ] Boot behavior recorded
[ ] Display behavior recorded
[ ] Keyboard response recorded
[ ] USB activity recorded
```

If Linux boots:

```text
[ ] Record Linux distribution/version
[ ] uname -a
[ ] cat /proc/cpuinfo
[ ] lsblk
[ ] df -h
[ ] free -h
[ ] ip addr
[ ] lsusb
[ ] Record display resolution
[ ] Photograph successful boot
[ ] Do NOT modify eMMC yet
```

---

## 22. Useful diagnostic commands

After a successful Linux boot:

```bash
uname -a
```

Kernel information.

```bash
cat /proc/cpuinfo
```

CPU identification.

```bash
lsblk
```

Storage devices and partitions.

```bash
df -h
```

Mounted filesystem usage.

```bash
free -h
```

Available memory.

```bash
lsusb
```

USB devices.

```bash
ip addr
```

Network interfaces.

Depending on the graphical environment:

```bash
xrandr
```

may provide display information.

These outputs should be saved before making major changes.

---

## 23. Open questions

The following questions remain unanswered and should be documented experimentally.

### Boot

- Which exact Linux image did Harrington use?
- Does the EO1 automatically prefer USB over eMMC?
- What U-Boot configuration is present?
- Can U-Boot be interrupted with a keyboard?
- Is a serial console available?

### Display

- Does the Nitrogen6X image initialize the EO1 LCD correctly?
- Is the native framebuffer landscape or portrait?
- Is rotation required?
- Is GPU acceleration available?
- Can the display operate reliably for many hours?

### Storage

- Which Linux device corresponds to the internal eMMC?
- Can the original Android partitions be mounted read-only?
- Can a complete eMMC backup be created safely?

### USB

- Is the powered hub required for reliable USB storage?
- Can keyboard, mouse, and flash storage operate simultaneously?
- Are some USB flash drives more reliable than others?

### EO1-Museum

- Can the current HTML/JavaScript gallery run unchanged?
- Which lightweight browser works best?
- Can browser chrome be eliminated completely?
- Would a native viewer be better?
- How quickly can the system boot directly into an exhibition?

---

## 24. Sources and prior work

### Charlie Harrington — Linux on EO1

Charlie Harrington demonstrated booting Linux on an EO1 using a USB flash drive connected through a USB hub and micro-USB adapter.

https://charlieharrington.com/run-linux-on-electric-objects-eo1-wall-computer/

This is the most important precedent for the experiment described in this document.

### EO1 teardown — 5 kHz

A detailed teardown identified the Freescale i.MX6 processor, USB OTG capability, Android environment, and `NITROGEN6X` USB identity.

https://www.5khz.com/2016/05/01/electric-objects-eo1-digital-art-display-teardown/

### Ezurio / Boundary Devices — i.MX6 builds

Collection of Linux images historically supplied for Nitrogen6X and related i.MX6 hardware.

https://www.ezurio.com/documentation/i-mx6-builds

### Nitrogen6X wiki

Technical resources for the Boundary Devices Nitrogen6X platform.

https://bdwiki.ezurio.com/index.php/Nitrogen6x

### Yocto Hardknott for i.MX6

Provides a prebuilt Nitrogen6X image and documents writing the image to SD card or USB storage.

https://www.ezurio.com/documentation/yocto-hardknott-release-for-i-mx6-platforms

Example image:

```text
20210922-boundary-image-multimedia-full-nitrogen6x.wic.gz
```

### Yocto Dunfell for i.MX6/i.MX7

Another documented Nitrogen6X release with USB-stick flashing instructions.

https://www.ezurio.com/documentation/yocto-dunfell-release-for-i-mx6-i-mx7-platforms

---

## 25. Relationship to EO1-Museum

The current EO1-Museum project deliberately uses the original Android system rather than replacing it.

Current architecture:

```text
Android
 ↓
MetBoot
 ↓
Firefox
 ↓
PC-hosted EO1-Museum
```

This is simple, reversible, and already works.

Linux USB boot should therefore be treated as a **parallel experimental path**, not as a replacement for the working system.

If successful, it could eventually lead to:

```text
USB Linux
 ↓
standalone EO1-Museum
 ↓
no PC
 ↓
no Wi-Fi
 ↓
power only
```

Such a configuration would make the EO1 particularly suitable for exhibitions and unattended installations.

---

## 26. Project philosophy

The goal is not to install Linux merely because it is possible.

The goal is to preserve the useful qualities of the Electric Objects EO1 — its large portrait display, quiet operation, and purpose-built physical form — while removing its dependence on discontinued services and unnecessary external infrastructure.

The existing Android solution demonstrates that the EO1 can still serve as a networked digital museum display.

The Linux USB experiment asks a further question:

> **Can the EO1 become a completely self-contained digital museum appliance?**

That is the purpose of this experiment.
