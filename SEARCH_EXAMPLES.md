# Search Examples

**Last updated:** 2026-10-29

EO1-Museum currently provides two artwork discovery tools:

- `GET_MET_ART_KEYWORD.py` — searches The Metropolitan Museum of Art Open Access collection
- `GET_COMMONS_ART.py` — discovers public-domain artwork images from Wikimedia Commons

The two tools serve the same general purpose — finding usable artwork for EO1-Museum — but they work in different ways.

The Met provides a well-structured museum collection with rich metadata. Wikimedia Commons is much broader, but its category and file structure is more complex.

---

# 1. The Metropolitan Museum of Art

## Basic search

`GET_MET_ART_KEYWORD.py` searches the Met Open Access dataset (`MetObjects.csv`) and then uses the Met Collection API when downloading images.

The current version supports command-line searches as well as interactive operation.

A simple artist search can be previewed without downloading anything:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Pierre-Auguste Renoir" --dry-run

To actually create the collection:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Pierre-Auguste Renoir" --target 100

The `--artist` option searches the `Artist Display Name` field specifically.

Multiple artists separated by commas are treated as alternatives (OR):

    python GET_MET_ART_KEYWORD.py --type painting --artist "Renoir, Pissarro, Sisley" --dry-run

---

## General metadata search

The `--query` option searches multiple metadata fields, including title, artist information, object name, classification, medium, culture, period, dynasty, object date, department, and tags.

Words separated by spaces are treated as AND conditions:

    --query "edo landscape"

Commas separate alternative searches (OR):

    --query "landscape, garden"

For example:

    python GET_MET_ART_KEYWORD.py --type painting --query "landscape" --dry-run

or:

    python GET_MET_ART_KEYWORD.py --type painting --query "edo landscape" --dry-run

Artist and general metadata filters can be combined. In that case both conditions must match:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Renoir" --query "portrait" --dry-run

This is often preferable to using an artist name as a general keyword because `--artist` is restricted to the actual artist-name field.

---

## Dry-run first

Before downloading a new collection, it is often useful to add:

    --dry-run

For example:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Vincent van Gogh" --dry-run

Dry-run reports the matching metadata count and prints a reproducible command that can be used for the actual download.

It does **not** modify the current artwork collection, `met_metadata.json`, or the archive.

If `MetObjects.csv` is not already present, however, the Open Access dataset may still be downloaded because it is required for searching.

---

## Target size

The default target is 100 works.

A different number can be specified with:

    --target 50

For example:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Pissarro" --target 50

If fewer eligible works are available, EO1-Museum uses what it can find.

---

## Subject filters

The Met tool also provides broad subject filters.

Current subject groups are:

1. Any subject
2. Portrait / figure
3. Landscape / nature
4. Still life / flowers / food
5. City / architecture
6. Animals

Multiple subject groups can be combined.

For example, landscapes and city scenes:

    python GET_MET_ART_KEYWORD.py --type painting --subject 3,5 --dry-run

Subject filters can also be combined with an artist:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Pissarro" --subject 3,5 --dry-run

These filters are intentionally broad discovery aids rather than precise art-historical classifications.

---

## Color filtering

To request color images only:

    --color

To disable the color-image filter:

    --no-color

For example:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Renoir" --color --dry-run

Note that actual color filtering requires examining downloaded image data. Therefore dry-run can report the metadata search result, but it cannot determine the final number of images that will pass the color test.

---

## Objects other than paintings

The Met tool can also explore Open Access objects beyond paintings:

    --type all

Optional object filters include:

- photograph
- print / engraving / lithograph
- drawing / watercolor
- sculpture
- ceramics
- textile / costume
- furniture / decorative arts
- arms & armor
- manuscript / book
- poster / graphic design

For example:

    python GET_MET_ART_KEYWORD.py --type all --object ceramics --query "joseon" --dry-run

or:

    python GET_MET_ART_KEYWORD.py --type all --object print --query "japanese" --dry-run

---

## Diagnostic mode

If a search gives an unexpected result, the Met tool provides a diagnostic mode.

For example:

    python GET_MET_ART_KEYWORD.py --diagnose "monet"

This examines how the keyword appears in the Open Access metadata and how records are affected by the Public Domain and painting filters.

To compare those records with the current Met Collection API:

    python GET_MET_ART_KEYWORD.py --diagnose "monet" --check-api

Diagnostic mode does not modify the artwork collection.

This can be useful when the number of available works seems unexpectedly small.

---

## Some useful Met search terms

The following examples were found while exploring the Met Open Access dataset.

The counts are approximate and should **not** be interpreted as official collection statistics. The dataset and EO1-Museum filtering rules may change over time.

### European artists

| Search term | Approx. matches |
|---|---:|
| renoir | 27 |
| cezanne | 24 |
| degas | 23 |
| manet | 21 |
| pissarro | 20 |
| van gogh | 18 |
| gauguin | 10 |
| seurat | 10 |
| sisley | 8 |
| morisot | 2 |

For current versions of the script, artist searches are preferably made with `--artist` rather than treating the name as a general metadata keyword.

Example:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Pissarro" --dry-run

### Asian art

| Search term | Approx. matches |
|---|---:|
| hokusai | 61 |
| shibata zeshin | 80 |
| kyosai | 49 |
| edo | 941 |
| qing | 498 |
| ming | 204 |
| joseon | 69 |
| goryeo | 6 |

These terms may refer to artists, periods, cultures, dynasties, titles, or other metadata. Use `--artist` for a specific artist and `--query` for broader metadata exploration.

### Subjects

| Search term | Approx. matches |
|---|---:|
| portrait | 814 |
| landscape | 351 |
| cat | 210 |
| sea | 106 |
| flowers | 105 |

Again, these are approximate discovery results rather than catalog statistics.

---

# 2. Wikimedia Commons

`GET_COMMONS_ART.py` takes a different approach.

Instead of performing a broad keyword search across metadata, it starts with an artist and looks for a Wikimedia Commons category of the form:

    Category:Paintings by <artist> by title

It then follows the individual artwork categories, examines the image files associated with each work, and selects usable digital representations.

The discovery path is approximately:

    artist
      ↓
    Paintings by <artist> by title
      ↓
    individual artwork categories
      ↓
    image files
      ↓
    Public Domain / CC0 filter
      ↓
    resolution filter
      ↓
    largest eligible image for each artwork

This makes Commons particularly useful when The Met has few usable digital images for an artist.

---

## Discover an artist without downloading images

A good first step is:

    python GET_COMMONS_ART.py --artist "Claude Monet" --dry-run

For Vincent van Gogh:

    python GET_COMMONS_ART.py --artist "Vincent van Gogh" --dry-run

Unlike the Met dry-run, a first Commons dry-run may take considerable time.

The program must explore the Commons category structure and inspect the files associated with individual artworks.

No artwork images are downloaded in dry-run mode, but the discovery result is cached.

For example:

    metadata/Claude_Monet.json

or:

    metadata/Vincent_van_Gogh.json

This JSON file contains the eligible artworks discovered during the scan.

---

## Discovery cache

A Commons scan can involve hundreds of artwork categories and many API requests, so the result is preserved.

For example:

    metadata/
        Claude_Monet.json
        Vincent_van_Gogh.json

If the cache already exists, the next command reuses it instead of scanning Wikimedia Commons again.

Thus:

    python GET_COMMONS_ART.py --artist "Claude Monet" --dry-run

is fast after the first complete discovery scan.

The cached JSON is part of EO1-Museum's discovery data and can be retained with the project.

---

## Force a new Commons scan

To ignore the existing cache and scan Wikimedia Commons again:

    python GET_COMMONS_ART.py --artist "Claude Monet" --refresh --dry-run

Use `--refresh` only when a new discovery scan is actually wanted.

Commons categories and files can change over time, but there is normally no reason to repeat an expensive scan for every gallery update.

---

## Download artworks from the cached discovery result

After inspecting the dry-run result, download a random selection with:

    python GET_COMMONS_ART.py --artist "Claude Monet" --target 100

If the artist cache already exists, Commons is not rescanned.

The selected images are placed in:

    original/

with filenames such as:

    Claude_Monet__Water_Lilies.jpg

The artist and artwork title are therefore preserved in the local filename.

---

## Image eligibility

For each artwork, `GET_COMMONS_ART.py` examines available digital files and currently accepts raster images such as JPEG, PNG, WebP, and TIFF.

The image must also:

- have a clearly acceptable Public Domain or CC0 status
- meet the minimum resolution requirement

The default minimum dimensions are:

    short side >= 700 pixels
    long side  >= 1200 pixels

If several eligible digital images exist for the same artwork, the program selects the one with the largest pixel count.

These rules select a technically usable digital representation. They do not guarantee that it will be the visually best reproduction.

---

## Human curation and reject lists

A high-resolution image is not necessarily a good reproduction.

Some Commons files may come from old printed books, faded scans, poor photography, or otherwise undesirable sources.

EO1-Museum therefore keeps the final visual judgment with the user.

To exclude an artwork from future random selections, create or edit:

    metadata/<Artist>_reject.txt

For example:

    metadata/Claude_Monet_reject.txt

with one artwork name per line:

    Water Lilies
    The Magpie
    Impression, Sunrise

Blank lines and lines beginning with `#` are ignored.

The original discovery cache is not destroyed. Rejected works remain in the JSON discovery result but are removed from the pool used for future selections.

This provides a simple human-in-the-loop curation process:

    machine discovery
          ↓
    rights / format / resolution filtering
          ↓
    EO1 display
          ↓
    human visual judgment
          ↓
    reject list

---

# 3. Choosing between The Met and Wikimedia Commons

The two discovery tools are complementary.

## The Met

Use `GET_MET_ART_KEYWORD.py` when you want:

- fast searches over a well-structured museum dataset
- artist searches
- general keyword searches
- subject filters
- object-type filters
- exploration by culture, period, medium, subject, or other metadata
- relatively consistent source quality

Example:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Renoir" --dry-run

## Wikimedia Commons

Use `GET_COMMONS_ART.py` when you want:

- broader coverage for a particular artist
- works that may not be available through The Met Open Access collection
- Public Domain / CC0 digital reproductions from many institutions and sources
- a reusable artist-level discovery cache

Example:

    python GET_COMMONS_ART.py --artist "Claude Monet" --dry-run

The Met can be thought of as **curated discovery**, while Wikimedia Commons provides **broad discovery**.

Neither completely replaces the other.

---

# 4. A practical workflow

For a new artist, a useful workflow is to start with The Met:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Vincent van Gogh" --dry-run

If the result looks useful, download the desired number:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Vincent van Gogh" --target 100

For broader discovery, try Commons:

    python GET_COMMONS_ART.py --artist "Vincent van Gogh" --dry-run

The first run creates the discovery cache.

Then download from the cached pool:

    python GET_COMMONS_ART.py --artist "Vincent van Gogh" --target 100

After viewing the resulting images on EO1, add visually unsuitable works to:

    metadata/Vincent_van_Gogh_reject.txt

and run the Commons selection again.

---

# 5. From discovery to EO1

Regardless of the source, selected artwork eventually follows the same EO1-Museum pipeline:

    The Met
       │
       └── GET_MET_ART_KEYWORD.py ──┐
                                    │
    Wikimedia Commons               ├──> original/
       │                            │
       └── GET_COMMONS_ART.py ──────┘
                                           │
                                           ▼
                                    make_gallery.py
                                           │
                                           ▼
                                        display/
                                           │
                                           ▼
                                          EO1

The discovery tools answer the question:

**What artwork can I find and actually use?**

`make_gallery.py` and the EO1 application then answer the next question:

**How should those works be prepared and displayed on the EO1?**

Try different artists, subjects, and collections. Unexpected discoveries can sometimes make the most interesting exhibitions.
