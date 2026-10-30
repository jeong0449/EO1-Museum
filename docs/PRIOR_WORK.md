# Inspiration and Prior Work

EO1-Museum would not have been possible without earlier work by people who explored the Electric Objects EO1, documented ways to regain control of the device, and preserved source code that could be adapted after the original service disappeared.

The project has evolved through several stages, from gaining basic access to the EO1, to a Firefox-based workaround, and eventually to a native Android application built by modifying existing EO1 source code.

## Hack Your EO1 — Darius Kazemi

Darius Kazemi's [Hack Your EO1](https://feeltrain.com/blog/hack-your-eo1/), published on the Feel Train blog in 2015, demonstrated that the EO1 could be treated as a general-purpose Android device rather than simply as a digital art frame tied to the original Electric Objects service.

The article explains how to connect a keyboard and mouse through the EO1's micro-USB port using an OTG adapter and USB hub, and how to launch the Android browser with `Win+B`. It also explores installing APKs and automatically launching applications at startup.

This provided an important starting point for EO1-Museum: the realization that the original user interface did not define the limits of the hardware, and that the underlying Android system could be accessed and repurposed directly.

## eo1-workaround — Christian Boyle

Christian Boyle's [eo1-workaround](https://github.com/christianboyle/eo1-workaround) provided a practical approach to reviving an EO1 after the original Electric Objects service was discontinued.

His work demonstrated how Firefox and locally controlled web content could be used to restore the EO1 as a functional image display without relying on the original online service. This approach directly influenced the first stable, browser-based version of EO1-Museum and helped establish the basic idea of serving independently controlled content to the EO1 over a local network.

The browser-based architecture that grew from this approach is described above, and its later evolution into the native EO1 Museum application is documented in [EO1-Museum Development History](docs/DEVELOPMENT_HISTORY.md).

## EO1 Android Source — spalt/EO1

The next major step became possible because of the [spalt/EO1](https://github.com/spalt/EO1) repository.

This repository provided EO1 Android application source code that could be built, studied, modified, and run on the actual hardware. Instead of creating a replacement Android application entirely from scratch, EO1-Museum adopted this code as the starting point for its native application and progressively modified and extended it for the revived EO1 environment.

This was a major turning point for the project.

The modified application first became a native Local Gallery capable of displaying images directly from the EO1's internal storage. It was subsequently extended to support MP4 playback, Bluetooth audio, mouse controls, cross-fade transitions, a clock overlay, media rescanning, and automatic startup as the Android HOME application.

In v0.3, PC Gallery functionality was brought into the application itself through an embedded WebView. This eliminated the need for Firefox and MetBoot during normal operation:

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

In v0.4, the native application was extended again so that images prepared in the PC Gallery can optionally be transferred over Wi-Fi into the EO1's internal storage using Safe Sync. The PC Gallery therefore became not only a remote display mode, but also a way to deliver a newly prepared collection to the Local Gallery.

The current development path can be summarized as:

```text
EO1 hardware access
        ↓
Firefox-based web gallery
        ↓
Native Android Local Gallery
        ↓
Local + PC Gallery integration
        ↓
PC-to-EO1 Safe Sync
```

The availability of the `spalt/EO1` source code was especially important in making the transition from a browser-based workaround to a native EO1 application possible. It provided a practical foundation that could be modified and extended rather than requiring the Android side of the project to be reconstructed from the ground up.

**Special thanks are due to spalt for preserving and sharing the EO1 source code.** That contribution made it possible for EO1-Museum to move well beyond the original browser-based revival and develop into the native application used today.

EO1-Museum also owes much to Darius Kazemi and Christian Boyle for documenting their experiments and practical solutions at different stages in the life of the EO1. Together, these earlier efforts provided the access methods, ideas, and source-code foundation on which the project has been built.

EO1-Museum continues that work with a somewhat different focus: preserving the distinctive portrait hardware of the EO1 and turning it into a self-contained digital museum display supported by open-access artwork discovery, PC-side curation, and a native Android gallery.

Many thanks to **Darius Kazemi, Christian Boyle, and spalt** for making their work publicly available and helping give these devices a useful second life.

## Running Linux on the EO1 — Charlie Harrington

In 2022, [Charlie Harrington](https://charlieharrington.com/run-linux-on-electric-objects-eo1-wall-computer/) demonstrated another approach to repurposing the EO1: booting Linux directly from a USB flash drive. After identifying the EO1 hardware as being closely related to a Boundary Devices i.MX6 platform, he used a Linux build for the Boundary Devices hardware and connected the USB drive, keyboard, and mouse through a powered USB hub and the EO1's micro-USB OTG port.

This approach bypasses the original Android environment without requiring it to be erased from the internal storage, effectively turning the EO1 into a small portrait-oriented ARM Linux computer. Harrington used the system to automatically download and display the New York Times front page and later explored remote administration over SSH.

This work suggests another possible direction for EO1-Museum: a future standalone Linux-based version that could run the gallery software directly on the EO1 without depending on a separate PC.
