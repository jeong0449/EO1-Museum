# EO1-Museum

EO1-Museum brings an Electric Objects EO1 back to life as a digital museum display, using open-access collections from The Metropolitan Museum of Art and potentially other museums.

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

This project was inspired by two earlier efforts to explore and repurpose the Electric Objects EO1.

### Hack Your EO1 — Darius Kazemi

Darius Kazemi's [Hack Your EO1](https://feeltrain.com/blog/hack-your-eo1/), published on the Feel Train blog in 2015, demonstrated that the EO1 could be treated as a general-purpose Android device rather than simply as a digital art frame.

The article explains how to connect a keyboard and mouse through the EO1's micro-USB port using an OTG adapter and USB hub, and how to launch the Android browser with `Win+B`. It also explores installing APKs and automatically launching applications at startup.

This was the starting point for understanding how to regain control of the EO1 independently of its original user interface.

### eo1-workaround — Christian Boyle

Christian Boyle's [eo1-workaround](https://github.com/christianboyle/eo1-workaround) was created after the original Electric Objects service was discontinued and provides a practical approach to bringing the EO1 back to life.

It builds on the same basic access method—USB OTG, keyboard and mouse, and the Android browser—but uses Firefox and web content to turn the EO1 into an independent image display. The use of Firefox, particularly for its Fullscreen API support, directly influenced the approach used in EO1-Museum.

EO1-Museum builds on ideas explored in these earlier projects, combining direct access to the EO1, a Firefox-based web display, automatic startup through MetBoot, and a local gallery system for curating and displaying open-access museum collections.

Many thanks to Darius Kazemi and Christian Boyle for documenting their work and helping make it possible to give these devices a second life.

### Running Linux on the EO1 — Charlie Harrington

In 2022, [Charlie Harrington](https://charlieharrington.com/run-linux-on-electric-objects-eo1-wall-computer/) demonstrated another approach to repurposing the EO1: booting Linux directly from a USB flash drive. After identifying the EO1 hardware as being closely related to a Boundary Devices i.MX6 platform, he used a Linux build for the Boundary Devices hardware and connected the USB drive, keyboard, and mouse through a powered USB hub and the EO1's micro-USB OTG port.

This approach bypasses the original Android environment without requiring it to be erased from the internal storage, effectively turning the EO1 into a small portrait-oriented ARM Linux computer. Harrington used the system to automatically download and display the New York Times front page and later explored remote administration over SSH.

This work suggests another possible direction for EO1-Museum: a future standalone Linux-based version that could run the gallery software directly on the EO1 without depending on a separate PC.

## Future Development

EO1-Museum is still a work in progress. The current version focuses on restoring the EO1 as a simple and reliable digital museum display, but several improvements are planned or being considered.

- **True fullscreen display** — remove the remaining Firefox browser interface and borders, possibly by extending MetBoot to provide a dedicated fullscreen WebView or launcher.
- **Artwork information** — optionally display the title, artist, date, medium, and other metadata together with each artwork.
- **Landscape artwork presentation** — provide a better way to display wide landscape-oriented works on the portrait EO1 screen, for example by slowly panning the image horizontally instead of shrinking the entire work to fit.
- **Improved transitions** — add simple fades or other unobtrusive transitions between artworks.
- **Exhibition modes** — make it easier to create themed exhibitions based on artists, periods, cultures, subjects, or other metadata.
- **Additional museum collections** — extend the downloader and gallery system to other museums that provide open-access images and metadata.
- **Local collections** — allow personal photographs or locally curated image collections to be mixed with museum artworks.
- **More independent operation** — reduce the amount of manual interaction required on the PC and make the EO1 behave more like a self-contained digital museum display.

The goal is not to turn the EO1 into a modern tablet, but to preserve its distinctive portrait display and give it a useful second life as a quiet, dedicated window into art.
