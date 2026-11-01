# EO1-Museum

> **Current version — EO1-Museum v0.42**
>
> EO1-Museum revives the discontinued **Electric Objects EO1** as a standalone digital art display using a native Android application and PC-side tools.
>
> It displays curated museum artworks from open-access collections as well as **generative art rendered as video**. Artwork can be discovered and prepared on a PC, previewed over the network, synchronized to the EO1, and then displayed independently from its internal storage.
>
> **Generative Art Gallery:** https://jeong0449.github.io/EO1-Museum/art/

EO1-Museum brings an [Electric Objects EO1](https://www.kickstarter.com/projects/electricobjects/electric-objects-a-computer-made-for-art) back to life as a digital museum display. It combines a lightweight native Android application on the EO1 with PC-side tools for discovering, curating, preparing, and synchronizing artwork from open-access museum collections.

The project began with The Metropolitan Museum of Art collection and is designed to accommodate artworks from other open-access collections as well.

<p align="center">
  <img src="images/sample_2.jpg" width="350" alt="Claude Monet, The Apple Tree (Le Pommier), displayed on the EO1">
</p>

<p align="center">
  <em>Claude Monet, The Apple Tree (Le Pommier), 1879. Museum Barberini, Potsdam (Hasso Plattner Collection).</em>
</p>

## How It Works

EO1-Museum uses a PC for artwork discovery, curation, and gallery preparation. The prepared collection can either be viewed directly through **PC Gallery** or transferred over Wi-Fi using **Safe Sync** for independent playback from the EO1's internal storage.

    PC
     │
     ├── PC Gallery ──────────────► EO1
     │
     └── Safe Sync ───────────────► EO1
                                      │
                                Local Gallery
                                      │
                                      ▼
                             standalone playback

Once synchronized, Local Gallery does not require the PC or a network connection for normal playback.

Artwork files can also be copied directly to the EO1's internal storage using ADB for development or manual maintenance.

For the evolution from the original Firefox/MetBoot-based system to the current native application, see [Development History](docs/DEVELOPMENT_HISTORY.md).

## Installation

The current installation procedure is described in the root-level [Installation Guide](INSTALL.md).

The guide provides two installation and maintenance paths:

1. **Network installation and normal operation** — the intended path for ordinary use. The native EO1-Museum APK is installed without relying on Firefox or MetBoot, and exhibitions are subsequently transferred through PC Gallery and Safe Sync.

2. **ADB installation and maintenance** — for users who want to install or update the APK directly over USB, transfer media with `adb push`, inspect the EO1 filesystem, troubleshoot the application, or perform development work. `ADBApprovalHelper` is documented as part of this path.

> **Important:** The simplified network installation procedure was reconstructed retrospectively from the development history and the author's current working EO1. It has **not yet been tested from beginning to end on a fresh or factory-reset EO1**. See [INSTALL.md](INSTALL.md) for the full warning and installation details.

Firefox and MetBoot are **not required for normal operation of the current native application**.

### Legacy Browser-Based Installation

The earlier Firefox + MetBoot installation procedure is preserved separately in [Legacy Installation Guide](legacy/INSTALL_LEGACY.md).

In that architecture, the EO1 required a Wi-Fi connection to the PC-hosted gallery during normal operation:

```text
Android boot
     ↓
MetBoot
     ↓
Firefox 68.11.0
     ↓
PC-hosted EO1-Museum gallery
```

The associated Windows batch files—`START_EO1.bat`, `UPDATE_MET.bat`, and `GET_MET_AND_START.bat`—also belong to this earlier browser-based workflow.

These files and instructions are retained for **historical reference and reproducibility**, rather than as the recommended setup for the current EO1-Museum application.

For the full history of this architecture and its transition to the native application, see [EO1-Museum Development History](docs/DEVELOPMENT_HISTORY.md).

## Museum Collections

EO1-Museum currently supports two primary sources for discovering open-access artworks: **The Metropolitan Museum of Art (The Met)** and **Wikimedia Commons**. Future versions may expand beyond conventional museum collections to include **space imagery provided by NASA** and **open-access collections from Korean museums and cultural institutions**. These additions are intended to broaden EO1-Museum from a museum-art display into a more flexible platform for exploring and presenting openly accessible visual culture and scientific imagery.

**The Met** provides a well-structured institutional collection with rich metadata. EO1-Museum can search its open-access collection using artist names, keywords, subjects, periods, cultures, and other metadata, making it particularly useful for systematic and curated discovery.

**Wikimedia Commons** provides a much broader pool of public-domain and freely reusable artwork images gathered from museums and cultural institutions around the world. EO1-Museum uses artist-based discovery, image-resolution filtering, license checks, and local metadata caching to identify suitable works. Because the collection is broader and less uniform than a single museum database, the workflow also supports human curation through persistent reject lists.

The two sources therefore complement each other:

```text
The Met
   └── structured, museum-based discovery

Wikimedia Commons
   └── broad, cross-collection discovery
```
Discovered artworks are downloaded to the PC, curated locally, and processed for the EO1's 1080 × 1920 portrait display. The resulting gallery can be viewed directly through PC Gallery or transferred to the EO1's internal storage using Safe Sync for independent Local Gallery playback.

Detailed search syntax, command-line options, examples, caching behavior, and curation workflows are documented separately in [Search Examples](SEARCH_EXAMPLES.md).

The discovery system is intentionally extensible, so additional open-access collections can be added when suitable image and metadata sources are available.

In this sense, EO1-Museum can also be seen as a small experiment in what might be called **“Fine Art Informatics”** — using open cultural data, metadata, computation, human curation, and digital displays to discover, organize, and experience works of art.

### Generative Art

EO1-Museum also supports **generative art** created with HTML5 Canvas and JavaScript. Because the EO1's original hardware is not powerful enough to render these animations smoothly in real time, the works are rendered on a PC as portrait-format MP4 video and played back by the native EO1-Museum application.

The artworks, interactive browser versions, and a brief description of the rendering workflow are available in the [Generative Art Gallery](https://jeong0449.github.io/EO1-Museum/art/).

## Inspiration and Prior Work

EO1-Museum builds on earlier work by **Darius Kazemi**, **Christian Boyle**, **spalt**, and **Charlie Harrington**, whose experiments, documentation, and source code demonstrated different ways to regain control of the Electric Objects EO1 and extend its useful life.

In particular, the native EO1 Museum application was developed by modifying and extending the EO1 Android source code preserved in [spalt/EO1](https://github.com/spalt/EO1). **Special thanks are due to spalt for preserving and sharing this source code**, which provided the practical foundation for the current native application.

For detailed discussion of these earlier projects and their influence on EO1-Museum, see [Inspiration and Prior Work](docs/PRIOR_WORK.md). The evolution of EO1-Museum itself is documented separately in [EO1-Museum Development History](docs/DEVELOPMENT_HISTORY.md).

## Documentation

- [Roadmap](docs/ROADMAP.md) — planned improvements and future directions

