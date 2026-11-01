# Search Examples

**Last updated:** 2026-11-01

EO1-Museum currently provides two artwork discovery tools:

- `GET_MET_ART_KEYWORD.py` — searches The Metropolitan Museum of Art Open Access collection
- `GET_COMMONS_ART.py` — discovers public-domain artwork images from Wikimedia Commons

The two tools serve the same general purpose — finding usable artwork for EO1-Museum — but they work in different ways.

The Met provides a well-structured museum collection with rich metadata. Wikimedia Commons is much broader, but its category and file structure is more complex.

---

# 1. The Metropolitan Museum of Art

`GET_MET_ART_KEYWORD.py` searches The Metropolitan Museum of Art Open Access dataset (`MetObjects.csv`) and uses the Met Collection API when downloading images.

The tool is intended not only as a downloader, but also as a lightweight artwork discovery and curation tool. Searches can combine artist, date, geographic region, medium, culture, subject, tags, and the Met Highlight designation.

The current version supports both command-line searches and interactive operation.

## Start with dry-run

Before downloading artwork, it is usually useful to preview the search:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Pierre-Auguste Renoir" --dry-run

Dry-run reports the number of matching metadata records and prints a reproducible command for the actual download.

It does not modify the current artwork collection, `met_metadata.json`, or the archive.

If `MetObjects.csv` is not already present, however, the Open Access dataset may still be downloaded because it is required for searching.

Dry-run does not save the filtered metadata records as a separate file. It reports the number of matches only.

---

## Artist search

The `--artist` option searches the `Artist Display Name` field specifically.

For example:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Vincent van Gogh" --dry-run

To download the selected works:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Vincent van Gogh" --target 100

Multiple artists separated by commas are treated as alternatives (OR):

    python GET_MET_ART_KEYWORD.py --type painting --artist "Renoir,Pissarro,Sisley" --dry-run

This can be useful for building a small collection around a group of related artists:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Amedeo Modigliani,Gustav Klimt,Egon Schiele" --target 10

The number of usable works may be much smaller than the target because the Met Open Access collection contains only a limited number of eligible works for some artists.

---

## General metadata search

The `--query` option performs a broad search across multiple metadata fields, including:

- title
- artist name and biographical information
- artist nationality
- object name
- classification
- medium
- culture
- country and region
- period and dynasty
- object date
- department
- tags

Words separated by spaces are treated as AND conditions:

    --query "edo landscape"

Commas separate alternatives (OR):

    --query "landscape,garden"

For example:

    python GET_MET_ART_KEYWORD.py --type painting --query "landscape" --dry-run

or:

    python GET_MET_ART_KEYWORD.py --type painting --query "edo landscape" --dry-run

Artist and general metadata filters can be combined:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Renoir" --query "portrait" --dry-run

In this case, both conditions must match.

For a specific artist, `--artist` is generally preferable to using the artist's name as a general keyword.

---

## Search by date

The `--year` option accepts either a single year:

    --year 1888

or a range:

    --year 1600-1750

For example, to explore European paintings from the Baroque period:

    python GET_MET_ART_KEYWORD.py --type painting --year 1600-1750 --region europe --dry-run

To narrow this to oil paintings:

    python GET_MET_ART_KEYWORD.py --type painting --year 1600-1750 --region europe --medium oil --dry-run

A date range is particularly useful when an art-historical period is not represented consistently in the Met metadata.

For example, a broad exploration of the two centuries leading up to Impressionism can be approximated with:

    python GET_MET_ART_KEYWORD.py --type painting --year 1670-1870 --region europe --medium oil --dry-run

---

## Geographic region

The `--region` option provides broad geographic and cultural filtering.

Current values are:

- `asia`
- `europe`
- `africa`
- `americas`
- `oceania`

For example:

    python GET_MET_ART_KEYWORD.py --type painting --region europe --dry-run

or:

    python GET_MET_ART_KEYWORD.py --type all --region asia --dry-run

Region filtering is intentionally broad. It is designed for discovery rather than precise geographic or art-historical classification.

It can be combined with other filters:

    python GET_MET_ART_KEYWORD.py --type painting --year 1600-1750 --region europe --medium oil --target 20

---

## Medium

The `--medium` option searches the Met `Medium` metadata.

For example:

    python GET_MET_ART_KEYWORD.py --type painting --medium oil --dry-run

Multiple terms separated by commas are alternatives (OR):

    python GET_MET_ART_KEYWORD.py --type painting --medium "oil,tempera" --dry-run

Medium is especially useful in combination with date and region:

    python GET_MET_ART_KEYWORD.py --type painting --year 1670-1870 --region europe --medium oil --dry-run

For works other than paintings:

    python GET_MET_ART_KEYWORD.py --type all --object print --medium lithograph --dry-run

---

## Culture

The `--culture` option searches the Met `Culture` field.

For example:

    python GET_MET_ART_KEYWORD.py --type all --culture japanese --dry-run

Multiple alternatives can be supplied:

    python GET_MET_ART_KEYWORD.py --type all --culture "japanese,chinese" --dry-run

The Met's Culture metadata is not a controlled art-historical taxonomy for every object. Similar material may be described in different ways, so `--culture` should be treated as a discovery filter rather than an exhaustive classification.

If a culture search produces unexpectedly few results, try `--query`, `--artist`, or other metadata filters instead.

---

## Tags

The Met dataset contains descriptive tags for many objects.

The `--tag` option searches this field directly.

For example:

    python GET_MET_ART_KEYWORD.py --type painting --tag flowers --dry-run

Multiple tags separated by commas are treated as alternatives (OR):

    python GET_MET_ART_KEYWORD.py --type painting --tag "flowers,birds" --dry-run

A tag can be combined with other filters:

    python GET_MET_ART_KEYWORD.py --type painting --region europe --tag flowers --dry-run

or:

    python GET_MET_ART_KEYWORD.py --type painting --year 1800-1900 --tag portrait --dry-run

Tags are useful for visually oriented curation because they often describe what is actually depicted rather than only when or where the object was made.

---

## Met Highlights

The `--highlight` option restricts the search to objects marked as highlights by The Metropolitan Museum of Art.

For example:

    python GET_MET_ART_KEYWORD.py --type painting --highlight --dry-run

This becomes particularly useful when combined with other filters.

European oil paintings from approximately the two centuries before Impressionism:

    python GET_MET_ART_KEYWORD.py --type painting --year 1670-1870 --region europe --medium oil --highlight --dry-run

To download up to 100 works using exactly those criteria:

    python GET_MET_ART_KEYWORD.py --type painting --year 1670-1870 --region europe --medium oil --highlight --target 100

Highlights provide a convenient way to create a smaller, museum-curated pool from a much larger metadata search.

---

## Combining filters: curation examples

The main strength of the Met tool is that filters can be combined to construct a curatorial theme.

### Baroque-era European oil paintings

    python GET_MET_ART_KEYWORD.py --type painting --year 1600-1750 --region europe --medium oil --dry-run

To restrict this to Met Highlights:

    python GET_MET_ART_KEYWORD.py --type painting --year 1600-1750 --region europe --medium oil --highlight --dry-run

### European painting before Impressionism

    python GET_MET_ART_KEYWORD.py --type painting --year 1670-1870 --region europe --medium oil --dry-run

For a smaller museum-selected pool:

    python GET_MET_ART_KEYWORD.py --type painting --year 1670-1870 --region europe --medium oil --highlight --dry-run

### European flower paintings

    python GET_MET_ART_KEYWORD.py --type painting --region europe --tag flowers --dry-run

### Nineteenth-century European landscapes

    python GET_MET_ART_KEYWORD.py --type painting --year 1800-1900 --region europe --subject 3 --dry-run

### Impressionist and Post-Impressionist artists

    python GET_MET_ART_KEYWORD.py --type painting --artist "Renoir,Pissarro,Sisley,Degas,Manet,Cezanne,Van Gogh,Gauguin" --dry-run

### A small early-twentieth-century European collection

    python GET_MET_ART_KEYWORD.py --type painting --artist "Amedeo Modigliani,Gustav Klimt,Egon Schiele" --target 10

### Portraits from the nineteenth century

    python GET_MET_ART_KEYWORD.py --type painting --year 1800-1900 --subject 2 --dry-run

### Still life and flowers

    python GET_MET_ART_KEYWORD.py --type painting --subject 4 --dry-run

### Animals in Asian art

    python GET_MET_ART_KEYWORD.py --type all --region asia --subject 6 --dry-run

These searches are deliberately flexible. They are intended to generate interesting candidate pools rather than reproduce a formal art-historical catalog.

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

Subject filters can also be combined with other metadata:

    python GET_MET_ART_KEYWORD.py --type painting --year 1800-1900 --region europe --subject 3 --dry-run

or with an artist:

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

Actual color filtering requires examining downloaded image data. Therefore dry-run can report the metadata search result, but it cannot determine the final number of images that will pass the color test.

---

## Target size

The default target is 100 works.

A different number can be specified with:

    --target 50

For example:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Pissarro" --target 50

For a small addition to an existing collection:

    python GET_MET_ART_KEYWORD.py --type painting --year 1600-1750 --region europe --medium oil --target 10

If fewer eligible works are available, EO1-Museum uses what it can find.

The target is an upper limit on the selected candidate set. It does not guarantee that the requested number of new works will be added, particularly when eligible works are already present in the current collection.

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

For example, Japanese prints:

    python GET_MET_ART_KEYWORD.py --type all --object print --query japanese --dry-run

Prints by several major Japanese artists:

    python GET_MET_ART_KEYWORD.py --type all --object print --artist "Hokusai,Hiroshige,Utamaro,Kuniyoshi" --dry-run

Korean ceramics:

    python GET_MET_ART_KEYWORD.py --type all --object ceramics --query joseon --dry-run

Asian prints:

    python GET_MET_ART_KEYWORD.py --type all --object print --region asia --dry-run

Lithographs:

    python GET_MET_ART_KEYWORD.py --type all --object print --medium lithograph --dry-run

The `--type all` mode is particularly useful for artists whose important works are not primarily paintings.

---

## Diagnostic mode

If a search gives an unexpected result, the Met tool provides a diagnostic mode.

For example:

    python GET_MET_ART_KEYWORD.py --diagnose "monet"

This examines how the keyword appears in the Open Access metadata and how records are affected by the Public Domain and painting filters.

To compare those records with the current Met Collection API:

    python GET_MET_ART_KEYWORD.py --diagnose "monet" --check-api

Diagnostic mode does not modify the artwork collection.

This can be particularly useful when an artist is known to be represented at the Met but a normal search returns few or no downloadable works.

---

## Search strategy

There is no single best metadata field for every type of artwork search.

A useful rule of thumb is:

- use `--artist` when you know the artist
- use `--year` for a historical time window
- use `--region` for broad geographic discovery
- use `--medium` for material or technique
- use `--culture` when the Met Culture field is likely to be informative
- use `--tag` for depicted subjects
- use `--highlight` when you want a smaller museum-selected pool
- use `--query` when you want to search broadly across metadata
- combine filters when you want to construct a more specific curatorial theme

For example, instead of searching for the word `baroque`, it may be more productive to construct the intended collection explicitly:

    python GET_MET_ART_KEYWORD.py --type painting --year 1600-1750 --region europe --medium oil --highlight --dry-run

This reflects the basic philosophy of the Met discovery tool: use structured metadata to build a candidate collection, inspect the result, and then refine the search.

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
- date and geographic filtering
- medium, culture, and tag filtering
- Met Highlight selection
- subject and object-type filters
- broad metadata searches
- combinations of structured filters for thematic curation
- relatively consistent source quality

Example:

    python GET_MET_ART_KEYWORD.py --type painting --year 1600-1750 --region europe --medium oil --highlight --dry-run

The Met tool is particularly useful when you want to construct a collection from several curatorial criteria rather than search for one artist only.

## Wikimedia Commons

Use `GET_COMMONS_ART.py` when you want:

- broader coverage for a particular artist
- works that may not be available through The Met Open Access collection
- Public Domain / CC0 digital reproductions from many institutions and sources
- a reusable artist-level discovery cache

Example:

    python GET_COMMONS_ART.py --artist "Claude Monet" --dry-run

The Met can be thought of as **structured, metadata-driven curation**, while Wikimedia Commons provides **broader artist-centered discovery**.

Neither completely replaces the other.

---

# 4. A practical workflow

For a new artist or curatorial theme, a useful workflow is to start with The Met.

For an artist:

    python GET_MET_ART_KEYWORD.py --type painting --artist "Vincent van Gogh" --dry-run

For a historical theme:

    python GET_MET_ART_KEYWORD.py --type painting --year 1600-1750 --region europe --medium oil --dry-run

For a smaller museum-selected pool:

    python GET_MET_ART_KEYWORD.py --type painting --year 1600-1750 --region europe --medium oil --highlight --dry-run

If the result looks useful, remove `--dry-run` and specify the desired target:

    python GET_MET_ART_KEYWORD.py --type painting --year 1600-1750 --region europe --medium oil --highlight --target 20

For broader artist-centered discovery, try Commons:

    python GET_COMMONS_ART.py --artist "Vincent van Gogh" --dry-run

The first run creates the discovery cache.

Then download from the cached pool:

    python GET_COMMONS_ART.py --artist "Vincent van Gogh" --target 100

After viewing the resulting images on EO1, add visually unsuitable Commons works to:

    metadata/Vincent_van_Gogh_reject.txt

and run the Commons selection again.

The overall process is therefore iterative:

    define a theme
          ↓
    dry-run
          ↓
    inspect the number of candidates
          ↓
    refine the filters
          ↓
    download a collection
          ↓
    view it on EO1
          ↓
    refine again

The search tools are discovery aids. Final curation remains a human decision.

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

For the Met tool, that question can now be refined further:

**What kind of collection do I want to curate?**

`make_gallery.py` and the EO1 application then answer the next question:

**How should those works be prepared and displayed on the EO1?**

Try different artists, periods, regions, media, subjects, and combinations of filters. Unexpected discoveries can sometimes make the most interesting exhibitions.
