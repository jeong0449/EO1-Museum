#!/usr/bin/env python3
"""
GET_COMMONS_ART.py

Wikimedia Commons Public Domain artwork discovery/downloader
for EO1-Museum

Version: 0.5
Date: 2026-10-29

Purpose
-------
Discover usable public-domain artwork images from Wikimedia Commons,
cache the discovery result by artist, and download a random selection
for EO1-Museum.

The script treats Wikimedia Commons primarily as an artwork discovery
source rather than simply as an image search engine.

Basic usage
-----------

Download 100 randomly selected Claude Monet paintings:

    python GET_COMMONS_ART.py --artist "Claude Monet" --target 100

Dry run:

    python GET_COMMONS_ART.py --artist "Claude Monet" --target 100 --dry-run

Force Wikimedia Commons rescan:

    python GET_COMMONS_ART.py --artist "Claude Monet" --target 100 --refresh

Show help:

    python GET_COMMONS_ART.py --help

Show version:

    python GET_COMMONS_ART.py --version


Cache
-----

    metadata/
        Claude_Monet.json
        Claude_Monet_downloaded.json
        Claude_Monet_reject.txt


Reject list
-----------

To permanently exclude an artwork from future random selections,
add its artwork name to:

    metadata/Claude_Monet_reject.txt

One artwork name per line:

    Water Lilies
    The Magpie
    Impression, Sunrise

Blank lines and lines beginning with # are ignored.

The names should match the artwork names shown by this program.


Downloaded files
----------------

    original/
        Claude_Monet__Water_Lilies.jpg
        Claude_Monet__The_Magpie.jpg
        ...


Discovery strategy
------------------

    Category:Paintings by <artist> by title
        -> individual artwork categories
        -> image files

    Fallback:
    Category:Paintings by <artist> by year
        -> year categories -> image files

    Final fallback:
    Category:Paintings by <artist>
        -> category tree -> image files
        -> Public Domain / CC0
        -> resolution filter
        -> largest eligible image per artwork

The expensive Commons scan is cached per artist.

If the artist cache already exists, Commons is not rescanned unless
--refresh is specified.
"""

import argparse
import html
import json
import random
import re
import shutil
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ============================================================
# Configuration
# ============================================================

VERSION = "0.5"
BUILD_DATE = "2026-10-31"

API = "https://commons.wikimedia.org/w/api.php"

USER_AGENT = (
    f"EO1-Museum/{VERSION} "
    "(https://github.com/jeong0449/EO1-Museum)"
)

HEADERS = {
    "User-Agent": USER_AGENT
}

OUTPUT_DIR = Path("original")
METADATA_DIR = Path("metadata")

TIMEOUT = 30


# ============================================================
# HTTP session
# ============================================================

def make_session():

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    retry = Retry(
        total=5,
        connect=5,
        read=5,
        status=5,
        backoff_factor=1.0,
        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],
        allowed_methods=[
            "GET"
        ],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(
        max_retries=retry
    )

    session.mount(
        "https://",
        adapter
    )

    session.mount(
        "http://",
        adapter
    )

    return session


SESSION = make_session()


# ============================================================
# Utility functions
# ============================================================

def artist_slug(artist):

    slug = str(artist).strip()

    slug = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        slug
    )

    slug = re.sub(
        r"\s+",
        "_",
        slug
    )

    return slug


def cache_path(artist):

    return (
        METADATA_DIR
        / f"{artist_slug(artist)}.json"
    )


def downloaded_metadata_path(artist):

    return (
        METADATA_DIR
        / f"{artist_slug(artist)}_downloaded.json"
    )


def reject_path(artist):

    return (
        METADATA_DIR
        / f"{artist_slug(artist)}_reject.txt"
    )


def strip_html(text):

    if not text:
        return ""

    text = html.unescape(
        str(text)
    )

    text = re.sub(
        r"<[^>]+>",
        "",
        text
    )

    return text.strip()


def safe_filename(name):

    name = str(name)

    name = name.replace(
        "File:",
        ""
    )

    name = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        name
    )

    name = name.strip()

    return name


# ============================================================
# Reject list
# ============================================================

def load_reject_list(artist):
    """
    Load artwork names that should not be selected.

    File:
        metadata/<Artist>_reject.txt

    Format:
        one artwork name per line

    Blank lines and # comments are ignored.

    Matching is case-insensitive and ignores leading/trailing spaces.
    """

    path = reject_path(
        artist
    )

    if not path.exists():

        return set()

    rejected = set()

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            for line in f:

                line = line.strip()

                if not line:
                    continue

                if line.startswith("#"):
                    continue

                rejected.add(
                    line.casefold()
                )

    except Exception as e:

        print(
            f"WARNING: could not read "
            f"reject list: {e}"
        )

        return set()

    return rejected


def apply_reject_list(
    items,
    artist
):
    """
    Remove rejected artworks from the eligible pool.
    """

    rejected = load_reject_list(
        artist
    )

    if not rejected:

        return items, 0

    accepted = []
    rejected_count = 0

    for item in items:

        artwork_name = str(
            item.get(
                "artwork_name",
                ""
            )
        ).strip()

        if (
            artwork_name.casefold()
            in rejected
        ):

            rejected_count += 1
            continue

        accepted.append(
            item
        )

    return (
        accepted,
        rejected_count
    )


# ============================================================
# API access with retry
# ============================================================

def api_get(params):

    params = dict(params)

    params["format"] = "json"
    params["formatversion"] = 2

    last_error = None

    for attempt in range(1, 6):

        try:

            response = SESSION.get(
                API,
                params=params,
                timeout=TIMEOUT,
            )

            response.raise_for_status()

            return response.json()

        except (
            requests.exceptions.SSLError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as e:

            last_error = e

            if attempt == 5:
                break

            wait = 2 ** (
                attempt - 1
            )

            print(
                f"\n[NETWORK] "
                f"{type(e).__name__}"
            )

            print(
                f"Retry "
                f"{attempt}/5 "
                f"after {wait} sec..."
            )

            time.sleep(
                wait
            )

    raise last_error


# ============================================================
# Cache
# ============================================================

def migrate_legacy_cache(artist):

    METADATA_DIR.mkdir(
        exist_ok=True
    )

    slug = artist_slug(
        artist
    )

    legacy = Path(
        f"{slug}.json"
    )

    destination = cache_path(
        artist
    )

    if (
        legacy.exists()
        and
        not destination.exists()
    ):

        print()

        print(
            f"Found existing cache: "
            f"{legacy}"
        )

        shutil.move(
            str(legacy),
            str(destination)
        )

        print(
            f"Moved to: "
            f"{destination}"
        )


def load_cache(artist):

    path = cache_path(
        artist
    )

    if not path.exists():
        return None

    print()

    print(
        f"Loading cache: "
        f"{path}"
    )

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(
                f
            )

    except Exception as e:

        print(
            f"ERROR reading cache: "
            f"{e}"
        )

        return None

    # v0.2/v0.3/v0.4 plain-list cache
    if isinstance(
        data,
        list
    ):

        print(
            f"Cached eligible artworks: "
            f"{len(data)}"
        )

        return data

    # Tolerate future dict-style cache
    if isinstance(
        data,
        dict
    ):

        items = data.get(
            "items"
        )

        if isinstance(
            items,
            list
        ):

            print(
                f"Cached eligible artworks: "
                f"{len(items)}"
            )

            return items

    print(
        "ERROR: unrecognized "
        "cache format."
    )

    return None


def save_cache(
    artist,
    metadata
):

    METADATA_DIR.mkdir(
        exist_ok=True
    )

    path = cache_path(
        artist
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()

    print(
        f"Metadata saved: "
        f"{path}"
    )


# ============================================================
# Commons categories
# ============================================================

def category_members(
    category,
    member_type
):

    results = []

    continuation = None

    while True:

        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmtype": member_type,
            "cmlimit": "500",
        }

        if continuation:

            params[
                "cmcontinue"
            ] = continuation

        data = api_get(
            params
        )

        members = (
            data.get(
                "query",
                {}
            )
            .get(
                "categorymembers",
                []
            )
        )

        results.extend(
            members
        )

        if "continue" not in data:
            break

        continuation = (
            data["continue"]
            ["cmcontinue"]
        )

    return results


def category_exists(category):

    data = api_get({
        "action": "query",
        "titles": category,
    })

    pages = (
        data.get(
            "query",
            {}
        )
        .get(
            "pages",
            []
        )
    )

    if not pages:
        return False

    return not pages[0].get(
        "missing",
        False
    )


# ============================================================
# Find artwork categories
# ============================================================

def find_discovery_category(artist):
    """Find the best Commons category structure available for an artist.

    Preferred strategy:
      1. Paintings by <artist> by title  (one category per artwork)
      2. Paintings by <artist> by year   (files grouped by year)
      3. Paintings by <artist>           (generic fallback)
    """

    candidates = [
        (f"Category:Paintings by {artist} by title", "title"),
        (f"Category:Paintings by {artist} by year", "flat"),
        (f"Category:Paintings by {artist}", "flat"),
    ]

    print()

    for category, strategy in candidates:
        print(f"Looking for: {category}")
        if category_exists(category):
            print(f"Found. Discovery mode: {strategy}")
            return category, strategy
        print("Not found.")

    return None, None


def collect_artwork_categories(artist):
    category, strategy = find_discovery_category(artist)

    if not category:
        return None, None

    if strategy == "title":
        print()
        print("Reading artwork categories...")
        artworks = category_members(category, "subcat")
        print(f"Artwork categories found: {len(artworks)}")
        return strategy, artworks

    print()
    print(f"Using category tree: {category}")
    return strategy, category


def collect_files_recursive(category, max_depth=2):
    """Collect unique files from a Commons category tree.

    This fallback is intended for artists whose Commons structure is grouped
    by year or museum rather than by individual artwork title.
    """

    files = {}
    visited = set()

    def walk(cat, depth):
        if cat in visited or depth > max_depth:
            return
        visited.add(cat)

        for item in category_members(cat, "file"):
            files[item["pageid"]] = item["title"]

        if depth == max_depth:
            return

        for subcat in category_members(cat, "subcat"):
            walk(subcat["title"], depth + 1)

    walk(category, 0)
    return files


def artwork_name_from_file_title(title):
    name = str(title or "").replace("File:", "", 1)
    name = re.sub(r"\.(?:jpe?g|png|webp|tiff?)$", "", name, flags=re.I)
    return name.strip() or "Untitled"


def scan_flat_category_tree(category, min_short_side, min_long_side):
    print()
    print("Scanning category tree for artwork files...")

    files = collect_files_recursive(category, max_depth=2)
    print(f"Unique image files found: {len(files)}")

    if not files:
        return []

    metadata = get_image_metadata(files.keys())
    selected = []

    for item in metadata:
        if not is_raster_image(item):
            continue
        if not is_pd_or_cc0(item):
            continue
        if not resolution_ok(item, min_short_side, min_long_side):
            continue

        item = dict(item)
        item["artwork_category"] = category
        item["artwork_name"] = artwork_name_from_file_title(item.get("title"))
        item["files_in_category"] = 1
        selected.append(item)

    print(f"Eligible artwork files: {len(selected)}")
    return selected


# ============================================================
# Collect image files
# ============================================================

def collect_files_from_artwork_category(
    category
):

    files = {}

    # Direct files
    direct = category_members(
        category,
        "file"
    )

    for item in direct:

        files[
            item["pageid"]
        ] = item["title"]

    # One level of subcategories
    subcats = category_members(
        category,
        "subcat"
    )

    for subcat in subcats:

        subcat_title = (
            subcat["title"]
        )

        try:

            subfiles = (
                category_members(
                    subcat_title,
                    "file"
                )
            )

        except Exception as e:

            print(
                f"    subcategory "
                f"warning: {e}"
            )

            continue

        for item in subfiles:

            files[
                item["pageid"]
            ] = item["title"]

    return files


# ============================================================
# Image metadata
# ============================================================

def get_image_metadata(
    pageids
):

    results = []

    pageids = list(
        pageids
    )

    if not pageids:
        return results

    batch_size = 20

    for start in range(
        0,
        len(pageids),
        batch_size
    ):

        batch = pageids[
            start:
            start + batch_size
        ]

        params = {
            "action": "query",
            "pageids": "|".join(
                str(x)
                for x in batch
            ),
            "prop": "imageinfo",
            "iiprop":
                "url|size|mime|extmetadata",
        }

        data = api_get(
            params
        )

        pages = (
            data.get(
                "query",
                {}
            )
            .get(
                "pages",
                []
            )
        )

        for page in pages:

            imageinfo = page.get(
                "imageinfo"
            )

            if not imageinfo:
                continue

            info = imageinfo[0]

            ext = info.get(
                "extmetadata",
                {}
            )

            def field(name):

                obj = ext.get(
                    name,
                    {}
                )

                if isinstance(
                    obj,
                    dict
                ):

                    return strip_html(
                        obj.get(
                            "value",
                            ""
                        )
                    )

                return ""

            results.append({

                "pageid":
                    page.get(
                        "pageid"
                    ),

                "title":
                    page.get(
                        "title"
                    ),

                "url":
                    info.get(
                        "url"
                    ),

                "descriptionurl":
                    info.get(
                        "descriptionurl"
                    ),

                "width":
                    info.get(
                        "width"
                    ),

                "height":
                    info.get(
                        "height"
                    ),

                "mime":
                    info.get(
                        "mime"
                    ),

                "artist":
                    field(
                        "Artist"
                    ),

                "credit":
                    field(
                        "Credit"
                    ),

                "license":
                    field(
                        "LicenseShortName"
                    ),

                "license_url":
                    field(
                        "LicenseUrl"
                    ),

                "usage_terms":
                    field(
                        "UsageTerms"
                    ),

                "copyrighted":
                    field(
                        "Copyrighted"
                    ),

                "description":
                    field(
                        "ImageDescription"
                    ),

                "date":
                    field(
                        "DateTimeOriginal"
                    ),
            })

        time.sleep(
            0.03
        )

    return results


# ============================================================
# Filters
# ============================================================

def is_raster_image(item):

    mime = (
        item.get(
            "mime"
        )
        or ""
    ).lower()

    return mime in {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/tiff",
    }


def is_pd_or_cc0(item):

    text = (
        (
            item.get(
                "license"
            )
            or ""
        )
        + " "
        + (
            item.get(
                "usage_terms"
            )
            or ""
        )
    ).lower()

    if "cc0" in text:
        return True

    pd_terms = [
        "public domain",
        "pd-old",
        "pd-art",
        "pd-us",
        "pd-1923",
        "pd-author",
        "pd-expired",
    ]

    return any(
        term in text
        for term in pd_terms
    )


def resolution_ok(
    item,
    min_short_side,
    min_long_side
):

    width = (
        item.get(
            "width"
        )
        or 0
    )

    height = (
        item.get(
            "height"
        )
        or 0
    )

    short_side = min(
        width,
        height
    )

    long_side = max(
        width,
        height
    )

    return (
        short_side
        >= min_short_side
        and
        long_side
        >= min_long_side
    )


def pixel_count(item):

    width = (
        item.get(
            "width"
        )
        or 0
    )

    height = (
        item.get(
            "height"
        )
        or 0
    )

    return width * height


# ============================================================
# Best image for one artwork
# ============================================================

def select_best_image(
    metadata,
    min_short_side,
    min_long_side
):

    candidates = []

    for item in metadata:

        if not is_raster_image(
            item
        ):
            continue

        if not is_pd_or_cc0(
            item
        ):
            continue

        if not resolution_ok(
            item,
            min_short_side,
            min_long_side
        ):
            continue

        candidates.append(
            item
        )

    if not candidates:
        return None

    candidates.sort(
        key=pixel_count,
        reverse=True
    )

    return candidates[0]


# ============================================================
# Scan artworks
# ============================================================

def scan_artworks(
    artwork_categories,
    min_short_side,
    min_long_side
):

    selected = []

    total = len(
        artwork_categories
    )

    print()

    print(
        "Scanning individual "
        "artworks..."
    )

    print()

    for index, artwork in enumerate(
        artwork_categories,
        1
    ):

        category = (
            artwork["title"]
        )

        display_name = (
            category.replace(
                "Category:",
                ""
            )
        )

        try:

            files = (
                collect_files_from_artwork_category(
                    category
                )
            )

            if not files:

                print(
                    f"[{index:3d}/{total}] "
                    f"{display_name}: "
                    f"no files"
                )

                continue

            metadata = (
                get_image_metadata(
                    files.keys()
                )
            )

            best = (
                select_best_image(
                    metadata,
                    min_short_side,
                    min_long_side
                )
            )

            if best:

                best[
                    "artwork_category"
                ] = category

                best[
                    "artwork_name"
                ] = display_name

                best[
                    "files_in_category"
                ] = len(files)

                selected.append(
                    best
                )

                print(
                    f"[{index:3d}/{total}] "
                    f"{display_name}: "
                    f"{len(files)} files -> "
                    f"{best['width']}x"
                    f"{best['height']} "
                    f"{best['license']}"
                )

            else:

                print(
                    f"[{index:3d}/{total}] "
                    f"{display_name}: "
                    f"{len(files)} files -> "
                    f"no eligible PD/CC0 image"
                )

        except Exception as e:

            print(
                f"[{index:3d}/{total}] "
                f"{display_name}: "
                f"ERROR: {e}"
            )

        time.sleep(
            0.03
        )

    return selected


# ============================================================
# Filename / download
# ============================================================

def extension_from_item(item):

    mime = (
        item.get(
            "mime"
        )
        or ""
    ).lower()

    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/tiff": ".tif",
    }

    return mapping.get(
        mime,
        ".jpg"
    )


def make_download_filename(
    item,
    artist
):

    artist_name = (
        safe_filename(
            artist
        )
        .replace(
            " ",
            "_"
        )
    )

    artwork_name = (
        safe_filename(
            item.get(
                "artwork_name",
                "Untitled"
            )
        )
        .replace(
            " ",
            "_"
        )
    )

    ext = extension_from_item(
        item
    )

    return (
        f"{artist_name}"
        f"__"
        f"{artwork_name}"
        f"{ext}"
    )


def download_file(
    item,
    artist
):

    url = item.get(
        "url"
    )

    if not url:

        raise ValueError(
            "No download URL"
        )

    filename = (
        make_download_filename(
            item,
            artist
        )
    )

    destination = (
        OUTPUT_DIR
        / filename
    )

    # Already exists

    if destination.exists():

        print(
            f"[SKIP] "
            f"{filename}"
        )

        return (
            filename,
            True
        )

    # Download

    print(
        f"[GET ] "
        f"{filename}"
    )

    last_error = None

    for attempt in range(
        1,
        6
    ):

        try:

            with SESSION.get(
                url,
                stream=True,
                timeout=60,
            ) as response:

                response.raise_for_status()

                with open(
                    destination,
                    "wb"
                ) as f:

                    for chunk in (
                        response.iter_content(
                            chunk_size=
                            1024 * 1024
                        )
                    ):

                        if chunk:

                            f.write(
                                chunk
                            )

            return (
                filename,
                False
            )

        except (
            requests.exceptions.SSLError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as e:

            last_error = e

            if destination.exists():

                try:

                    destination.unlink()

                except Exception:
                    pass

            if attempt == 5:
                break

            wait = 2 ** (
                attempt - 1
            )

            print(
                f"       retry "
                f"{attempt}/5 "
                f"after {wait} sec..."
            )

            time.sleep(
                wait
            )

    raise last_error


# ============================================================
# Preview selected works
# ============================================================

def print_selection(chosen):

    print()

    print(
        f"Selected: "
        f"{len(chosen)}"
    )

    print()

    for index, item in enumerate(
        chosen[:20],
        1
    ):

        print(
            f"{index:3d}. "
            f"{item.get('artwork_name', '?')} "
            f"[{item.get('width', '?')}x"
            f"{item.get('height', '?')}] "
            f"{item.get('license', '')}"
        )

    if len(chosen) > 20:

        print(
            f"... and "
            f"{len(chosen) - 20} more"
        )


# ============================================================
# Main
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        prog="GET_COMMONS_ART.py",

        description=(
            "EO1-Museum Wikimedia Commons artwork "
            "discovery and downloader."
        ),

        epilog="""
Examples:

  Download 100 random Monet paintings:
    python GET_COMMONS_ART.py --artist "Claude Monet" --target 100

  Preview selection without downloading:
    python GET_COMMONS_ART.py --artist "Claude Monet" --target 100 --dry-run

  Force a new Commons discovery scan:
    python GET_COMMONS_ART.py --artist "Claude Monet" --refresh

Rejecting artwork:

  Create or edit:

    metadata/Claude_Monet_reject.txt

  Put one artwork name on each line. Example:

    Water Lilies
    The Magpie

  Rejected artworks remain in the discovery cache but are excluded
  from future random selections.

Notes:

  * Only Public Domain / CC0 image files are accepted.
  * The largest eligible image is selected for each artwork.
  * Discovery results are cached by artist.
  * Use --refresh only when you really want to rescan Commons.
""",

        formatter_class=
            argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=(
            f"%(prog)s "
            f"{VERSION} "
            f"({BUILD_DATE})"
        ),
    )

    parser.add_argument(
        "--artist",
        required=True,
        help=(
            'artist name, e.g. '
            '"Claude Monet"'
        ),
    )

    parser.add_argument(
        "--target",
        type=int,
        default=100,
        help=(
            "maximum number of artworks "
            "to select (default: 100)"
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "select artworks but do not "
            "download image files"
        ),
    )

    parser.add_argument(
        "--refresh",
        action="store_true",
        help=(
            "ignore the artist cache and "
            "rescan Wikimedia Commons"
        ),
    )

    parser.add_argument(
        "--min-short-side",
        type=int,
        default=700,
        metavar="PIXELS",
        help=(
            "minimum short image dimension "
            "(default: 700)"
        ),
    )

    parser.add_argument(
        "--min-long-side",
        type=int,
        default=1200,
        metavar="PIXELS",
        help=(
            "minimum long image dimension "
            "(default: 1200)"
        ),
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    print("=" * 60)

    print(
        f"GET_COMMONS_ART.py "
        f"v{VERSION}"
    )

    print(
        "Wikimedia Commons "
        "Public Domain artwork discovery tool"
    )

    print("=" * 60)

    print(
        f"Artist          : "
        f"{args.artist}"
    )

    print(
        f"Target          : "
        f"{args.target}"
    )

    print(
        f"Min short side  : "
        f"{args.min_short_side}"
    )

    print(
        f"Min long side   : "
        f"{args.min_long_side}"
    )

    print(
        f"Refresh         : "
        f"{args.refresh}"
    )

    # --------------------------------------------------------
    # Directories
    # --------------------------------------------------------

    METADATA_DIR.mkdir(
        exist_ok=True
    )

    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    # --------------------------------------------------------
    # Move legacy cache if necessary
    # --------------------------------------------------------

    migrate_legacy_cache(
        args.artist
    )

    # --------------------------------------------------------
    # Load cache
    # --------------------------------------------------------

    eligible = None

    if not args.refresh:

        eligible = load_cache(
            args.artist
        )

    # --------------------------------------------------------
    # Rescan if cache unavailable
    # --------------------------------------------------------

    if eligible is not None:

        print()

        print(
            "Using cached Commons scan."
        )

        print(
            "No category rescan required."
        )

    else:

        print()

        print(
            "No usable cache found "
            "or --refresh specified."
        )

        print(
            "Scanning Wikimedia Commons..."
        )

        discovery_mode, discovery_source = (
            collect_artwork_categories(
                args.artist
            )
        )

        if not discovery_source:

            print()
            print("No usable Commons painting category found.")
            print("Tried: by title, by year, and the artist painting category.")
            return

        if discovery_mode == "title":
            eligible = scan_artworks(
                discovery_source,
                args.min_short_side,
                args.min_long_side
            )
            source_count = len(discovery_source)
            source_label = "Artwork categories"
        else:
            eligible = scan_flat_category_tree(
                discovery_source,
                args.min_short_side,
                args.min_long_side
            )
            source_count = len(eligible)
            source_label = "Eligible files"

        print()
        print("=" * 60)
        print(f"Discovery mode     : {discovery_mode}")
        print(f"{source_label:<19}: {source_count}")
        print(f"Eligible artworks   : {len(eligible)}")

        print("=" * 60)

        save_cache(
            args.artist,
            eligible
        )

    # --------------------------------------------------------
    # Check eligible records
    # --------------------------------------------------------

    if not eligible:

        print()

        print(
            "No eligible images."
        )

        return

    # --------------------------------------------------------
    # Apply human reject list
    # --------------------------------------------------------

    discovery_count = len(
        eligible
    )

    eligible, rejected_count = (
        apply_reject_list(
            eligible,
            args.artist
        )
    )

    print()

    print(
        f"Discovered       : "
        f"{discovery_count}"
    )

    print(
        f"Rejected by user : "
        f"{rejected_count}"
    )

    print(
        f"Available        : "
        f"{len(eligible)}"
    )

    reject_file = reject_path(
        args.artist
    )

    print(
        f"Reject list      : "
        f"{reject_file}"
    )

    if not eligible:

        print()

        print(
            "No artworks remain after "
            "applying the reject list."
        )

        return

    # --------------------------------------------------------
    # Random selection
    # --------------------------------------------------------

    chosen = list(
        eligible
    )

    random.shuffle(
        chosen
    )

    target = max(
        0,
        args.target
    )

    chosen = chosen[
        :target
    ]

    print_selection(
        chosen
    )

    # --------------------------------------------------------
    # Dry run
    # --------------------------------------------------------

    if args.dry_run:

        print()

        print(
            "DRY RUN: "
            "nothing downloaded."
        )

        return

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    print()

    print(
        f"Downloading to: "
        f"{OUTPUT_DIR.resolve()}"
    )

    print()

    downloaded = []

    new_count = 0
    skipped_count = 0
    error_count = 0

    for item in chosen:

        try:

            filename, skipped = (
                download_file(
                    item,
                    args.artist
                )
            )

            record = dict(
                item
            )

            record[
                "local_file"
            ] = filename

            record[
                "skipped_existing"
            ] = skipped

            downloaded.append(
                record
            )

            if skipped:

                skipped_count += 1

            else:

                new_count += 1

        except Exception as e:

            error_count += 1

            print(
                f"    ERROR: {e}"
            )

    # --------------------------------------------------------
    # Save download log
    # --------------------------------------------------------

    log_path = (
        downloaded_metadata_path(
            args.artist
        )
    )

    with open(
        log_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            downloaded,
            f,
            ensure_ascii=False,
            indent=2
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()

    print("=" * 60)

    print(
        f"Discovered      : "
        f"{discovery_count}"
    )

    print(
        f"Rejected        : "
        f"{rejected_count}"
    )

    print(
        f"Available       : "
        f"{len(eligible)}"
    )

    print(
        f"Selected        : "
        f"{len(chosen)}"
    )

    print(
        f"New downloads   : "
        f"{new_count}"
    )

    print(
        f"Already existed : "
        f"{skipped_count}"
    )

    print(
        f"Errors          : "
        f"{error_count}"
    )

    print(
        f"Directory       : "
        f"{OUTPUT_DIR.resolve()}"
    )

    print(
        f"Cache           : "
        f"{cache_path(args.artist)}"
    )

    print(
        f"Reject list     : "
        f"{reject_path(args.artist)}"
    )

    print(
        f"Download log    : "
        f"{log_path}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()