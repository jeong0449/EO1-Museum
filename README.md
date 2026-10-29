# EO1-Museum

> **Note — EO1 Museum v0.4**
>
> EO1 Museum has reached **v0.4**, extending the native Android gallery with
> **Safe Sync between PC Gallery and the EO1's internal storage**.
> Images prepared on the PC can now be transferred over Wi-Fi directly to
> the Local Gallery, without using ADB or manually copying files.
>
> Sync is optional and controlled by the PC-side `server.py`. The EO1 checks
> the server identity before syncing, respects configurable limits on media
> count and free storage space, and displays sync progress directly on screen.
> Existing files are replaced safely using temporary downloads so that an
> interrupted transfer does not destroy the current Local Gallery.
>
> With v0.4, the workflow now connects artwork discovery and gallery
> preparation on the PC with independent playback on the EO1:
>
> `artwork discovery → gallery preparation → PC Gallery → Safe Sync → Local Gallery`
>
> The EO1 still starts in **Local Gallery** mode and remains fully usable
> without a PC or network connection after synchronization.

EO1-Museum brings an Electric Objects EO1 back to life as a digital museum display, using open-access collections from The Metropolitan Museum of Art and potentially other museums.

<p align="center">
  <img src="sample.jpg" width="350" alt="Édouard Manet, Peonies, displayed on the EO1">
</p>

<p align="center">
  <em>
    Édouard Manet, <strong>Peonies</strong>, 1864–65, oil on canvas,
    The Metropolitan Museum of Art — displayed on an Electric Objects EO1
    using EO1-Museum. The image shown here is being displayed through Firefox, the method used in earlier versions; starting with v0.3, EO1-Museum displays artwork directly through its own native Android application.
  </em>
</p>

The basic workflow is:

```text
Open-access museum collections
        ↓
Download and curate artworks on a PC
        ↓
Generate a local web gallery
        ↓
Serve the gallery over Wi-Fi
        ↓
Electric Objects EO1
        ↓
MetBoot launches Firefox automatically
        ↓
Firefox opens the local gallery
        ↓
Museum artworks are displayed on the EO1
```

Artwork collection, selection, image processing, and web serving are handled by a PC on the same local network.

## Installation

For detailed instructions on setting up the PC, preparing the EO1, installing Firefox and MetBoot, and running the museum gallery, see the [Installation Guide](INSTALL.md).

A prebuilt `MetBoot.apk` is included in the repository root for direct installation on the EO1. The complete Android Studio source code is also provided in the `MetBoot/` directory.

Once configured, the EO1 requires only power and a Wi-Fi connection for normal operation. When the EO1 boots, **MetBoot** automatically launches Firefox, which opens the EO1-Museum gallery served by the PC on the local network.

For normal operation, three Windows batch files are provided:

- `START_EO1.bat` — start the current exhibition and local web server.
- `UPDATE_MET.bat` — select a new exhibition while the server is already running.
- `GET_MET_AND_START.bat` — select a new exhibition and then start the server.

## Museum Collections

EO1-Museum currently uses the open-access collection of **The Metropolitan Museum of Art (The Met)** as its first artwork source. Artworks can be searched and selected using collection metadata, downloaded to the PC, processed for the EO1's 1080 × 1920 display, and presented as a local web gallery.

Searches can be based on artists, periods, cultures, subjects, and other metadata. For example:

```text
renoir
landscape
hokusai
joseon
renoir portrait
renoir, degas
```

See [Search Examples](SEARCH_EXAMPLES.md) for search syntax, additional examples, and approximate result counts.

The project is designed so that collections from other museums can be added in the future, extending EO1-Museum beyond The Met into a more general platform for exploring and displaying open-access museum collections.

In this sense, EO1-Museum can also be seen as a small experiment in what might be called **“Fine Art Informatics”** — using open museum data, metadata, computation, and digital displays to discover, curate, and experience works of art.

## Inspiration and Prior Work

EO1-Museum would not have been possible without earlier work by people who explored the Electric Objects EO1, documented ways to regain control of the device, and preserved source code that could be adapted after the original service disappeared.

The project has evolved through several stages, from gaining basic access to the EO1, to a Firefox-based workaround, and eventually to a native Android application built by modifying existing EO1 source code.

### Hack Your EO1 — Darius Kazemi

Darius Kazemi's [Hack Your EO1](https://feeltrain.com/blog/hack-your-eo1/), published on the Feel Train blog in 2015, demonstrated that the EO1 could be treated as a general-purpose Android device rather than simply as a digital art frame tied to the original Electric Objects service.

The article explains how to connect a keyboard and mouse through the EO1's micro-USB port using an OTG adapter and USB hub, and how to launch the Android browser with `Win+B`. It also explores installing APKs and automatically launching applications at startup.

This provided an important starting point for EO1-Museum: the realization that the original user interface did not define the limits of the hardware, and that the underlying Android system could be accessed and repurposed directly.

### eo1-workaround — Christian Boyle

Christian Boyle's [eo1-workaround](https://github.com/christianboyle/eo1-workaround) provided a practical way to bring an EO1 back to life after the original Electric Objects service was discontinued.

It builds on the same basic access method—USB OTG, keyboard and mouse, and the Android environment—but uses Firefox and locally controlled web content to turn the EO1 into an independent image display.

This approach directly influenced the first stable version of EO1-Museum. Firefox was particularly useful because it could display the gallery using the Fullscreen API, while a small Android helper, MetBoot, was used to launch Firefox automatically after boot.

The resulting early architecture was:

```text
Android
   ↓
MetBoot
   ↓
Firefox
   ↓
PC HTTP server
   ↓
EO1-Museum web gallery
```

This was the first configuration that allowed the EO1 to function again as a practical art display without depending on the original Electric Objects service.

### EO1 Android Source — spalt/EO1

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

### Running Linux on the EO1 — Charlie Harrington

In 2022, [Charlie Harrington](https://charlieharrington.com/run-linux-on-electric-objects-eo1-wall-computer/) demonstrated another approach to repurposing the EO1: booting Linux directly from a USB flash drive. After identifying the EO1 hardware as being closely related to a Boundary Devices i.MX6 platform, he used a Linux build for the Boundary Devices hardware and connected the USB drive, keyboard, and mouse through a powered USB hub and the EO1's micro-USB OTG port.

This approach bypasses the original Android environment without requiring it to be erased from the internal storage, effectively turning the EO1 into a small portrait-oriented ARM Linux computer. Harrington used the system to automatically download and display the New York Times front page and later explored remote administration over SSH.

This work suggests another possible direction for EO1-Museum: a future standalone Linux-based version that could run the gallery software directly on the EO1 without depending on a separate PC.

## Future Development

EO1-Museum has evolved from an experimental workaround into a largely self-contained digital museum display. With the native Android gallery, fullscreen Local and PC Gallery modes, cross-fade transitions, automatic HOME startup, and PC-to-EO1 Safe Sync now implemented, several goals originally listed here have already been achieved.

Future development will therefore focus less on restoring basic EO1 functionality and more on improving **content discovery, curation, presentation, and gallery management**.

- **Artwork information** — optionally display the title, artist, date, medium, source collection, and other metadata together with each artwork.
- **Landscape artwork presentation** — provide a better way to display wide landscape-oriented works on the portrait EO1 screen, for example by slowly panning the image horizontally instead of shrinking the entire work to fit.
- **Exhibition and curation tools** — further develop workflows for creating themed exhibitions based on artists, periods, movements, cultures, subjects, or other metadata. Current tools already support artist- and keyword-based discovery, but more flexible curation remains possible.
- **Additional open-access collections** — extend artwork discovery beyond the Metropolitan Museum of Art and Wikimedia Commons when suitable museums or cultural institutions provide reusable high-quality images and metadata.
- **Local and personal collections** — make it easier to combine museum artworks with personal photographs or manually curated image collections within the same gallery workflow.
- **Richer collection metadata** — preserve more information about downloaded artworks throughout the pipeline from discovery to `original/`, `display/`, and ultimately the EO1, rather than treating the final gallery primarily as a collection of image files.
- **Improved Safe Sync** — continue testing PC-to-EO1 synchronization under interrupted Wi-Fi connections, limited storage, large collections, and other failure conditions, and refine collection replacement or mirroring behavior where useful.
- **Gallery configuration** — move selected parameters, such as image display duration, transition time, PC server address, and synchronization limits, into convenient configuration mechanisms without making the application unnecessarily complex.

Experimental work on Linux USB boot and extending the original Android environment with USB storage remains documented in [Experimental Linux USB Boot](docs/01_LINUX_USB_BOOT.md) and [Extending the Original Android Environment](docs/02_ANDROID_EXTENSIONS.md). These approaches are no longer required for normal EO1-Museum operation, since the native Android application and Safe Sync architecture now provide the essential functionality without replacing the original operating system.

The goal remains the same: not to turn the EO1 into a modern tablet, but to preserve its distinctive portrait display and give it a useful second life as a quiet, dedicated window into art.
