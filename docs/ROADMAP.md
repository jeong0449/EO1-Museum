# EO1-Museum Roadmap

EO1-Museum has evolved from an experimental workaround into a largely self-contained digital museum display. With the native Android gallery, fullscreen Local and PC Gallery modes, cross-fade transitions, automatic HOME startup, PC-to-EO1 Safe Sync, and dedicated presentation of wide landscape artworks now implemented, most of the core functionality originally envisioned for the project is complete.

Future development will therefore focus less on restoring or extending basic EO1 functionality and more on improving **content discovery, curation, metadata, and gallery management**.

- **Artwork information** — optionally display the title, artist, date, medium, source collection, and other metadata together with each artwork.
- **Exhibition and curation tools** — further develop workflows for creating themed exhibitions based on artists, periods, movements, cultures, subjects, or other metadata. Current tools already support artist- and keyword-based discovery, but more flexible curation remains possible.
- **Additional open-access collections** — extend artwork discovery beyond the Metropolitan Museum of Art and Wikimedia Commons when suitable museums or cultural institutions provide reusable high-quality images and metadata.
- **Local and personal collections** — make it easier to combine museum artworks with personal photographs or manually curated image collections within the same gallery workflow.
- **Richer collection metadata** — preserve more information about downloaded artworks throughout the pipeline from discovery to `original/`, `display/`, and ultimately the EO1, rather than treating the final gallery primarily as a collection of media files.
- **Safe Sync robustness** — continue testing PC-to-EO1 synchronization under interrupted Wi-Fi connections, limited storage, large collections, and other failure conditions. Safe Sync now transfers not only base artwork images but also companion media such as pre-rendered pan videos for wide artworks.
- **Gallery configuration** — move selected parameters, such as image display duration, transition timing, PC server address, synchronization limits, and wide-artwork presentation settings into convenient configuration mechanisms without making the application unnecessarily complex.

Wide landscape artwork presentation, previously listed as a future goal, is now implemented. Wide works can be accompanied by pre-rendered horizontal pan videos generated on the PC. These videos can be played through the PC/Network Gallery and transferred together with their base artwork through Safe Sync for subsequent playback in the Local Gallery. A static left-center-right presentation provides a fallback when a pan video is unavailable.

Experimental work on Linux USB boot and extending the original Android environment with USB storage remains documented in [Experimental Linux USB Boot](docs/01_LINUX_USB_BOOT.md) and [Extending the Original Android Environment](docs/02_ANDROID_EXTENSIONS.md). These approaches are no longer required for normal EO1-Museum operation, since the native Android application and Safe Sync architecture now provide the essential functionality without replacing the original operating system.

The goal remains the same: not to turn the EO1 into a modern tablet, but to preserve its distinctive portrait display and give it a useful second life as a quiet, dedicated window into art.
