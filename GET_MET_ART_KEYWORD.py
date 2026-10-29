from pathlib import Path
from datetime import datetime
import argparse
import csv
import json
import random
import shutil
import sys
import time
import urllib.error
import urllib.request

from PIL import Image


# ============================================================
# Script information
# ============================================================

SCRIPT_NAME = "The Met Gallery Downloader"
VERSION = "3.9"
EDITION = "CLI + Artist Filter + Diagnostic Edition"
BUILD_DATE = "2026-10-29"

# Version history
#
# v3.9
#   - Added --artist filter.
#   - Multiple artists can be separated by commas (OR).
#   - --artist and --query can be combined (AND).
#   - Artist matching uses Artist Display Name only.
#   - Removed misleading CSV image-URL diagnostic counts.
#   - Kept --diagnose and --check-api diagnostic modes.
#
# v3.8
#   - Added --diagnose KEYWORD.
#   - Added --check-api.
#   - Diagnostic mode compares CSV metadata with current Met API.
#   - Diagnostic mode never modifies the artwork collection.
#
# v3.7
#   - Added command-line options with argparse.
#   - Added --help and --version.
#   - Added safe --dry-run mode.
#   - Dry run prints a reproducible download command.
#   - Partial CLI options can be combined with interactive input.
#   - Added --target.
#
# v3.6
#   - Added multiple subject-filter selection.
#   - Added object-type filters for non-painting collections.
#
# v3.5
#   - Added subject filters.
#   - Added dynamic selected-target/progress display.
#
# v3.4
#   - Added actual image-based color filtering.
#
# v3.3
#   - Added NEW/ADD collection workflow.
#   - Added optional archive before replacing a collection.


# ============================================================
# Basic settings
# ============================================================

ROOT = Path(__file__).resolve().parent

CSVFILE = ROOT / "MetObjects.csv"
ORIGINAL = ROOT / "original"
META = ROOT / "met_metadata.json"
ARCHIVE = ROOT / "archive"

CSV_URL = (
    "https://media.githubusercontent.com/media/"
    "metmuseum/openaccess/master/MetObjects.csv"
)

OBJECT_API = (
    "https://collectionapi.metmuseum.org/"
    "public/collection/v1/objects/{}"
)

DEFAULT_TARGET = 100
CANDIDATE_POOL = 600
TIMEOUT = 45

UA = "Mozilla/5.0 EO1-Met-Gallery/" + VERSION

COLOR_CHANNEL_DELTA = 12
COLOR_PIXEL_FRACTION = 0.03


# ============================================================
# Search fields
# ============================================================

SEARCH_FIELDS = (
    "Title",
    "Artist Display Name",
    "Artist Display Bio",
    "Object Name",
    "Classification",
    "Medium",
    "Culture",
    "Period",
    "Dynasty",
    "Reign",
    "Portfolio",
    "Object Date",
    "Department",
    "Tags",
)


# ============================================================
# Object filters
# ============================================================

OBJECT_FILTERS = {
    "any": (
        "Any object type",
        []
    ),

    "photo": (
        "Photograph",
        [
            "photograph",
            "photography",
        ]
    ),

    "print": (
        "Print / engraving / lithograph",
        [
            "print",
            "engraving",
            "etching",
            "lithograph",
            "woodcut",
            "woodblock",
        ]
    ),

    "drawing": (
        "Drawing / watercolor",
        [
            "drawing",
            "watercolor",
            "watercolour",
            "pastel",
            "gouache",
        ]
    ),

    "sculpture": (
        "Sculpture",
        [
            "sculpture",
            "statue",
            "statuette",
            "relief",
        ]
    ),

    "ceramics": (
        "Ceramics",
        [
            "ceramic",
            "ceramics",
            "pottery",
            "porcelain",
            "earthenware",
            "stoneware",
        ]
    ),

    "textile": (
        "Textile / costume",
        [
            "textile",
            "costume",
            "dress",
            "garment",
            "fabric",
            "tapestry",
            "carpet",
        ]
    ),

    "furniture": (
        "Furniture / decorative arts",
        [
            "furniture",
            "chair",
            "table",
            "cabinet",
            "decorative arts",
            "vessel",
        ]
    ),

    "arms": (
        "Arms & armor",
        [
            "arms and armor",
            "arms & armor",
            "armor",
            "armour",
            "sword",
            "helmet",
            "shield",
        ]
    ),

    "manuscript": (
        "Manuscript / book",
        [
            "manuscript",
            "book",
            "codex",
            "folio",
            "album",
        ]
    ),

    "graphic": (
        "Poster / graphic design",
        [
            "poster",
            "graphic design",
            "advertisement",
            "commercial print",
        ]
    ),
}


OBJECT_MENU = {
    "1": "any",
    "2": "photo",
    "3": "print",
    "4": "drawing",
    "5": "sculpture",
    "6": "ceramics",
    "7": "textile",
    "8": "furniture",
    "9": "arms",
    "10": "manuscript",
    "11": "graphic",
}


# ============================================================
# Subject filters
# ============================================================

SUBJECT_FILTERS = {
    "1": (
        "Any subject",
        []
    ),

    "2": (
        "Portrait / figure",
        [
            "portrait",
            "self-portrait",
            "self portrait",
            "woman",
            "women",
            "man",
            "men",
            "girl",
            "girls",
            "boy",
            "boys",
            "figure",
            "figures",
            "person",
            "people",
            "mother",
            "child",
            "dancer",
            "dancers",
        ]
    ),

    "3": (
        "Landscape / nature",
        [
            "landscape",
            "river",
            "sea",
            "ocean",
            "coast",
            "mountain",
            "forest",
            "tree",
            "trees",
            "garden",
            "field",
            "fields",
            "park",
            "snow",
            "beach",
            "shore",
            "nature",
        ]
    ),

    "4": (
        "Still life / flowers / food",
        [
            "still life",
            "flower",
            "flowers",
            "fruit",
            "fruits",
            "vase",
            "bouquet",
            "table",
            "bottle",
            "apple",
            "apples",
            "pear",
            "pears",
            "peach",
            "peaches",
            "food",
        ]
    ),

    "5": (
        "City / architecture",
        [
            "city",
            "street",
            "bridge",
            "building",
            "buildings",
            "architecture",
            "church",
            "cathedral",
            "house",
            "houses",
            "interior",
            "room",
            "boulevard",
            "station",
            "harbor",
            "harbour",
        ]
    ),

    "6": (
        "Animals",
        [
            "animal",
            "animals",
            "horse",
            "horses",
            "dog",
            "dogs",
            "cat",
            "cats",
            "bird",
            "birds",
            "cattle",
            "cow",
            "sheep",
            "deer",
            "fish",
        ]
    ),
}


# ============================================================
# Command-line parser
# ============================================================

def build_parser():

    parser = argparse.ArgumentParser(
        description=(
            SCRIPT_NAME
            + " - download Open Access artwork "
            + "from The Metropolitan Museum of Art."
        )
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=(
            "%s v%s (%s)"
            % (
                SCRIPT_NAME,
                VERSION,
                BUILD_DATE,
            )
        ),
    )

    parser.add_argument(
        "--diagnose",
        metavar="KEYWORD",
        help=(
            "diagnose metadata filtering for a keyword "
            "without modifying the collection"
        ),
    )

    parser.add_argument(
        "--check-api",
        action="store_true",
        help=(
            "with --diagnose, compare CSV metadata "
            "against the current Met object API"
        ),
    )

    parser.add_argument(
        "--type",
        choices=[
            "painting",
            "all",
        ],
        dest="collection_type",
        help="collection type: painting or all",
    )

    parser.add_argument(
        "--object",
        choices=list(
            OBJECT_FILTERS.keys()
        ),
        dest="object_type",
        help="object filter for --type all",
    )

    parser.add_argument(
        "--subject",
        help=(
            "subject filter numbers, "
            "e.g. 2,3,4"
        ),
    )

    color_group = (
        parser.add_mutually_exclusive_group()
    )

    color_group.add_argument(
        "--color",
        dest="color_only",
        action="store_true",
        help="color images only",
    )

    color_group.add_argument(
        "--no-color",
        dest="color_only",
        action="store_false",
        help="disable color-image filtering",
    )

    parser.set_defaults(
        color_only=None
    )

    parser.add_argument(
        "--artist",
        help=(
            "artist name filter; "
            "commas separate alternative artists (OR)"
        ),
    )

    parser.add_argument(
        "--query",
        help=(
            "general metadata query; "
            "spaces=AND, commas=OR"
        ),
    )

    parser.add_argument(
        "--target",
        type=int,
        help=(
            "number of images to select "
            "(default: %d)"
            % DEFAULT_TARGET
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "search/count only; "
            "do not modify or download artwork"
        ),
    )

    return parser


# ============================================================
# Network
# ============================================================

def fetch(url):

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA
        }
    )

    return urllib.request.urlopen(
        req,
        timeout=TIMEOUT
    )


# ============================================================
# Download Met CSV
# ============================================================

def download_csv():

    if CSVFILE.exists():
        return

    print()
    print("MetObjects.csv not found.")
    print(
        "Downloading Met Open Access metadata..."
    )
    print()

    with fetch(CSV_URL) as r, \
            open(CSVFILE, "wb") as f:

        while True:

            block = r.read(
                1024 * 1024
            )

            if not block:
                break

            f.write(block)

    print(
        "Saved:",
        CSVFILE
    )


# ============================================================
# Basic helpers
# ============================================================

def search_text(row):

    return " ".join(
        row.get(field, "") or ""
        for field in SEARCH_FIELDS
    ).casefold()


def is_painting(row):

    classification = (
        row.get(
            "Classification",
            ""
        )
        .strip()
        .casefold()
    )

    object_name = (
        row.get(
            "Object Name",
            ""
        )
        .strip()
        .casefold()
    )

    return (
        "paint" in classification
        or
        "paint" in object_name
    )


def is_public_domain(row):

    value = (
        row.get(
            "Is Public Domain",
            ""
        )
        .strip()
        .casefold()
    )

    return value == "true"


# ============================================================
# Artist filter
# ============================================================

def parse_artist_filter(value):

    if not value:
        return []

    return [
        artist.strip().casefold()
        for artist in value.split(",")
        if artist.strip()
    ]


def matches_artist(row, artists):

    if not artists:
        return True

    artist_name = (
        row.get(
            "Artist Display Name",
            ""
        )
        or ""
    ).casefold()

    return any(
        artist in artist_name
        for artist in artists
    )


# ============================================================
# Object API
# ============================================================

def object_json(oid):

    with fetch(
        OBJECT_API.format(oid)
    ) as r:

        return json.load(r)


# ============================================================
# Diagnostic API comparison
# ============================================================

def diagnose_api_records(records):

    print()
    print(
        "=========================================="
    )
    print(
        " CSV vs CURRENT MET API"
    )
    print(
        "=========================================="
    )

    print()
    print(
        "Checking %d painting record(s)..."
        % len(records)
    )
    print()

    api_checked = 0
    api_errors = 0

    csv_public_count = 0
    api_public_count = 0
    api_image_count = 0

    disagreement_count = 0
    csv_false_api_true = 0
    csv_true_api_false = 0

    results = []

    for index, rec in enumerate(
        records,
        start=1
    ):

        oid = rec["objectID"]
        csv_public = rec["csv_public"]

        if csv_public:
            csv_public_count += 1

        try:

            obj = object_json(
                oid
            )

            api_checked += 1

            api_public = bool(
                obj.get(
                    "isPublicDomain"
                )
            )

            api_image = bool(
                obj.get(
                    "primaryImage"
                )
                or
                obj.get(
                    "primaryImageSmall"
                )
            )

            if api_public:
                api_public_count += 1

            if api_image:
                api_image_count += 1

            disagreement = (
                csv_public
                != api_public
            )

            if disagreement:

                disagreement_count += 1

                if (
                    not csv_public
                    and api_public
                ):
                    csv_false_api_true += 1

                elif (
                    csv_public
                    and not api_public
                ):
                    csv_true_api_false += 1

            result = {
                "objectID": oid,
                "title": (
                    obj.get("title")
                    or
                    rec["title"]
                ),
                "artist": (
                    obj.get(
                        "artistDisplayName"
                    )
                    or
                    rec["artist"]
                ),
                "csv_public":
                    csv_public,
                "api_public":
                    api_public,
                "api_image":
                    api_image,
                "disagreement":
                    disagreement,
            }

            results.append(
                result
            )

            marker = (
                "!"
                if disagreement
                else " "
            )

            print(
                "[%2d/%d] %s ID %-7s "
                "CSV=%-5s API=%-5s IMG=%-3s  %s"
                % (
                    index,
                    len(records),
                    marker,
                    oid,
                    str(csv_public),
                    str(api_public),
                    (
                        "yes"
                        if api_image
                        else "no"
                    ),
                    result["title"][:55],
                )
            )

            time.sleep(
                0.15
            )

        except Exception as e:

            api_errors += 1

            print(
                "[%2d/%d] ? ID %-7s API ERROR: %s"
                % (
                    index,
                    len(records),
                    oid,
                    e,
                )
            )

    print()
    print(
        "------------------------------------------"
    )
    print(
        "API COMPARISON SUMMARY"
    )
    print(
        "------------------------------------------"
    )

    print(
        "Painting records checked      :",
        len(records)
    )

    print(
        "Successful API checks         :",
        api_checked
    )

    print(
        "API errors                    :",
        api_errors
    )

    print()

    print(
        "CSV Public Domain = True      :",
        csv_public_count
    )

    print(
        "API isPublicDomain = True     :",
        api_public_count
    )

    print(
        "API image available           :",
        api_image_count
    )

    print()

    print(
        "CSV/API disagreements         :",
        disagreement_count
    )

    print(
        "CSV False -> API True         :",
        csv_false_api_true
    )

    print(
        "CSV True  -> API False        :",
        csv_true_api_false
    )

    disagreements = [
        r
        for r in results
        if r["disagreement"]
    ]

    if disagreements:

        print()
        print(
            "------------------------------------------"
        )
        print(
            "DISAGREEMENTS"
        )
        print(
            "------------------------------------------"
        )

        for r in disagreements:

            print()

            print(
                "Object ID :",
                r["objectID"]
            )

            print(
                "Artist    :",
                r["artist"]
                or "(blank)"
            )

            print(
                "Title     :",
                r["title"]
                or "(blank)"
            )

            print(
                "CSV Public:",
                r["csv_public"]
            )

            print(
                "API Public:",
                r["api_public"]
            )

            print(
                "API Image :",
                r["api_image"]
            )

    print()
    print(
        "=========================================="
    )

    if csv_false_api_true > 0:

        print(
            "IMPORTANT: Some records rejected by the "
            "CSV Public Domain filter are currently "
            "reported as Public Domain by the Met API."
        )

    elif disagreement_count == 0:

        print(
            "CSV and API Public Domain status agree "
            "for all successfully checked records."
        )

    print()
    print(
        "No artwork or collection files were changed."
    )

    return results


# ============================================================
# Diagnostic mode
# ============================================================

def diagnose_keyword(
    keyword,
    check_api=False
):

    keyword = (
        keyword or ""
    ).strip().casefold()

    if not keyword:

        print(
            "ERROR: diagnostic keyword is empty."
        )
        return 2

    download_csv()

    print()
    print(
        "=========================================="
    )
    print(
        " METADATA DIAGNOSTIC"
    )
    print(
        "=========================================="
    )

    print()
    print(
        "Keyword:",
        keyword
    )

    print()
    print(
        "Reading:",
        CSVFILE
    )

    total_rows = 0

    keyword_matches = 0
    public_matches = 0
    painting_matches = 0
    public_painting_matches = 0

    public_nonpainting = 0
    painting_nonpublic = 0

    artist_field_matches = 0
    title_field_matches = 0

    public_values = {}
    classifications = {}
    object_names = {}

    examples_public_painting = []
    examples_nonpublic_painting = []
    examples_public_nonpainting = []

    painting_records_for_api = []

    with open(
        CSVFILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        fieldnames = (
            reader.fieldnames
            or []
        )

        print()
        print(
            "Relevant CSV columns found:"
        )

        wanted_columns = (
            "Object ID",
            "Is Public Domain",
            "Object Name",
            "Classification",
            "Title",
            "Artist Display Name",
        )

        for name in wanted_columns:

            if name in fieldnames:

                print(
                    "  [OK]     ",
                    name
                )

            else:

                print(
                    "  [MISSING]",
                    name
                )

        for row in reader:

            total_rows += 1

            haystack = search_text(
                row
            )

            if keyword not in haystack:
                continue

            keyword_matches += 1

            artist = (
                row.get(
                    "Artist Display Name",
                    ""
                )
                or ""
            )

            title = (
                row.get(
                    "Title",
                    ""
                )
                or ""
            )

            if (
                keyword
                in artist.casefold()
            ):
                artist_field_matches += 1

            if (
                keyword
                in title.casefold()
            ):
                title_field_matches += 1

            pd_raw = (
                row.get(
                    "Is Public Domain",
                    ""
                )
                or ""
            ).strip()

            pd_key = (
                pd_raw
                if pd_raw
                else "(blank)"
            )

            public_values[
                pd_key
            ] = (
                public_values.get(
                    pd_key,
                    0
                )
                + 1
            )

            classification = (
                row.get(
                    "Classification",
                    ""
                )
                or ""
            ).strip()

            classification_key = (
                classification
                if classification
                else "(blank)"
            )

            classifications[
                classification_key
            ] = (
                classifications.get(
                    classification_key,
                    0
                )
                + 1
            )

            object_name = (
                row.get(
                    "Object Name",
                    ""
                )
                or ""
            ).strip()

            object_name_key = (
                object_name
                if object_name
                else "(blank)"
            )

            object_names[
                object_name_key
            ] = (
                object_names.get(
                    object_name_key,
                    0
                )
                + 1
            )

            public = is_public_domain(
                row
            )

            painting = is_painting(
                row
            )

            if painting:

                oid = (
                    row.get(
                        "Object ID",
                        ""
                    )
                    or ""
                ).strip()

                if oid.isdigit():

                    painting_records_for_api.append({
                        "objectID": int(oid),
                        "title": title,
                        "artist": artist,
                        "csv_public": public,
                    })

            if public:
                public_matches += 1

            if painting:
                painting_matches += 1

            if (
                public
                and painting
            ):
                public_painting_matches += 1

            if (
                public
                and not painting
            ):
                public_nonpainting += 1

            if (
                painting
                and not public
            ):
                painting_nonpublic += 1

            example = {
                "id": (
                    row.get(
                        "Object ID",
                        ""
                    )
                    or "?"
                ),
                "artist": artist,
                "title": title,
                "public": pd_raw,
                "classification": classification,
                "object_name": object_name,
            }

            if (
                public
                and painting
            ):

                if (
                    len(
                        examples_public_painting
                    )
                    < 10
                ):
                    examples_public_painting.append(
                        example
                    )

            elif (
                painting
                and not public
            ):

                if (
                    len(
                        examples_nonpublic_painting
                    )
                    < 15
                ):
                    examples_nonpublic_painting.append(
                        example
                    )

            elif (
                public
                and not painting
            ):

                if (
                    len(
                        examples_public_nonpainting
                    )
                    < 10
                ):
                    examples_public_nonpainting.append(
                        example
                    )

    print()
    print(
        "------------------------------------------"
    )
    print(
        "COUNTS"
    )
    print(
        "------------------------------------------"
    )

    print(
        "Total CSV records              :",
        total_rows
    )

    print(
        "Keyword anywhere in metadata   :",
        keyword_matches
    )

    print(
        "Keyword in Artist Display Name :",
        artist_field_matches
    )

    print(
        "Keyword in Title               :",
        title_field_matches
    )

    print()

    print(
        "Keyword + Public Domain        :",
        public_matches
    )

    print(
        "Keyword + Painting             :",
        painting_matches
    )

    print(
        "Keyword + Public + Painting    :",
        public_painting_matches
    )

    print()

    print(
        "Painting but NOT Public        :",
        painting_nonpublic
    )

    print(
        "Public but NOT Painting        :",
        public_nonpainting
    )

    print()
    print(
        "Image URLs are not evaluated from MetObjects.csv."
    )
    print(
        "Use --check-api to check current API image availability."
    )

    print()
    print(
        "------------------------------------------"
    )
    print(
        "RAW 'Is Public Domain' VALUES"
    )
    print(
        "------------------------------------------"
    )

    for value, count in sorted(
        public_values.items(),
        key=lambda x: (
            -x[1],
            x[0]
        )
    ):

        print(
            "%6d  %r"
            % (
                count,
                value
            )
        )

    print()
    print(
        "------------------------------------------"
    )
    print(
        "TOP CLASSIFICATIONS"
    )
    print(
        "------------------------------------------"
    )

    for value, count in sorted(
        classifications.items(),
        key=lambda x: (
            -x[1],
            x[0]
        )
    )[:15]:

        print(
            "%6d  %s"
            % (
                count,
                value
            )
        )

    print()
    print(
        "------------------------------------------"
    )
    print(
        "TOP OBJECT NAMES"
    )
    print(
        "------------------------------------------"
    )

    for value, count in sorted(
        object_names.items(),
        key=lambda x: (
            -x[1],
            x[0]
        )
    )[:15]:

        print(
            "%6d  %s"
            % (
                count,
                value
            )
        )

    def print_examples(
        heading,
        records
    ):

        print()
        print(
            "------------------------------------------"
        )
        print(
            heading
        )
        print(
            "------------------------------------------"
        )

        if not records:

            print(
                "(none)"
            )
            return

        for rec in records:

            print()

            print(
                "ID            :",
                rec["id"]
            )

            print(
                "Artist        :",
                rec["artist"]
                or "(blank)"
            )

            print(
                "Title         :",
                rec["title"]
                or "(blank)"
            )

            print(
                "Public Domain :",
                repr(
                    rec["public"]
                )
            )

            print(
                "Classification:",
                rec["classification"]
                or "(blank)"
            )

            print(
                "Object Name   :",
                rec["object_name"]
                or "(blank)"
            )

    print_examples(
        "EXAMPLES: PUBLIC + PAINTING",
        examples_public_painting
    )

    print_examples(
        "EXAMPLES: PAINTING BUT NOT PUBLIC",
        examples_nonpublic_painting
    )

    print_examples(
        "EXAMPLES: PUBLIC BUT NOT PAINTING",
        examples_public_nonpainting
    )

    print()
    print(
        "=========================================="
    )
    print(
        "DIAGNOSTIC SUMMARY"
    )
    print(
        "=========================================="
    )

    print()

    if keyword_matches == 0:

        print(
            "The keyword does not occur in the "
            "current MetObjects.csv metadata."
        )

    else:

        if (
            artist_field_matches
            < keyword_matches
        ):

            print(
                "Some keyword matches occur outside "
                "Artist Display Name."
            )

        if (
            painting_matches
            > public_painting_matches
        ):

            print(
                "%d matching painting record(s) are "
                "being rejected by the Public Domain filter."
                % (
                    painting_matches
                    -
                    public_painting_matches
                )
            )

        if (
            public_matches
            > public_painting_matches
        ):

            print(
                "%d Public Domain matching record(s) are "
                "being rejected by the painting test."
                % (
                    public_matches
                    -
                    public_painting_matches
                )
            )

        print()

        print(
            "Normal painting search would accept "
            "approximately %d metadata record(s) "
            "before subject/color checks."
            % public_painting_matches
        )

    print()
    print(
        "Diagnostic mode did not modify original/, "
        "archive/, or met_metadata.json."
    )

    if check_api:

        if painting_records_for_api:

            diagnose_api_records(
                painting_records_for_api
            )

        else:

            print()
            print(
                "No matching painting records "
                "available for API comparison."
            )

    return 0


# ============================================================
# Query parser
# ============================================================

def parse_query(query):

    query = (
        query or ""
    ).strip()

    if not query:
        return []

    groups = []

    for part in query.split(","):

        terms = [
            x.strip().casefold()
            for x in part.split()
            if x.strip()
        ]

        if terms:
            groups.append(terms)

    return groups


def matches_query(row, groups):

    if not groups:
        return True

    haystack = search_text(row)

    for group in groups:

        if all(
            term in haystack
            for term in group
        ):
            return True

    return False


# ============================================================
# Object filter
# ============================================================

def object_filter_text(row):

    fields = (
        "Object Name",
        "Classification",
        "Medium",
        "Department",
        "Title",
    )

    return " ".join(
        row.get(field, "") or ""
        for field in fields
    ).casefold()


def matches_object_filter(
    row,
    object_terms
):

    if not object_terms:
        return True

    haystack = object_filter_text(row)

    return any(
        term.casefold() in haystack
        for term in object_terms
    )


# ============================================================
# Subject filter
# ============================================================

def subject_filter_text(row):

    fields = (
        "Title",
        "Object Name",
        "Classification",
        "Medium",
        "Tags",
    )

    return " ".join(
        row.get(field, "") or ""
        for field in fields
    ).casefold()


def matches_subject_filter(
    row,
    subject_terms
):

    if not subject_terms:
        return True

    haystack = subject_filter_text(row)

    return any(
        term.casefold() in haystack
        for term in subject_terms
    )


def parse_subject_choices(value):

    if not value:
        return ["1"]

    choices = []

    for part in value.split(","):

        part = part.strip()

        if part in SUBJECT_FILTERS:
            choices.append(part)

    if (
        not choices
        or "1" in choices
    ):
        return ["1"]

    result = []

    for choice in choices:

        if choice not in result:
            result.append(choice)

    return result


def get_subject_info(choices):

    labels = []
    terms = []

    for choice in choices:

        label, choice_terms = (
            SUBJECT_FILTERS[choice]
        )

        labels.append(label)
        terms.extend(choice_terms)

    return labels, terms


# ============================================================
# Candidate selection
# ============================================================

def choose_candidates(
    groups,
    artists=None,
    paintings_only=True,
    subject_terms=None,
    object_terms=None
):

    artists = artists or []
    subject_terms = subject_terms or []
    object_terms = object_terms or []

    reservoir = []
    seen = 0

    print()
    print(
        "Searching Met metadata..."
    )

    with open(
        CSVFILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            if not is_public_domain(row):
                continue

            if (
                paintings_only
                and
                not is_painting(row)
            ):
                continue

            if not matches_artist(
                row,
                artists
            ):
                continue

            if not matches_query(
                row,
                groups
            ):
                continue

            if not matches_object_filter(
                row,
                object_terms
            ):
                continue

            if not matches_subject_filter(
                row,
                subject_terms
            ):
                continue

            oid = (
                row.get(
                    "Object ID",
                    ""
                ).strip()
            )

            if not oid.isdigit():
                continue

            seen += 1

            item = {
                "objectID": int(oid),
                "title": row.get(
                    "Title",
                    ""
                ),
                "artist": row.get(
                    "Artist Display Name",
                    ""
                ),
                "date": row.get(
                    "Object Date",
                    ""
                ),
                "objectURL": row.get(
                    "Link Resource",
                    ""
                ),
            }

            if (
                len(reservoir)
                < CANDIDATE_POOL
            ):

                reservoir.append(
                    item
                )

            else:

                j = random.randrange(
                    seen
                )

                if (
                    j
                    < CANDIDATE_POOL
                ):
                    reservoir[j] = item

    random.shuffle(
        reservoir
    )

    label = (
        "painting"
        if paintings_only
        else "object"
    )

    print(
        "Matching eligible %s records: %d"
        % (
            label,
            seen
        )
    )

    return reservoir, seen


# ============================================================
# Image download
# ============================================================

def download_image(url, path):

    with fetch(url) as r, \
            open(path, "wb") as f:

        while True:

            block = r.read(
                1024 * 1024
            )

            if not block:
                break

            f.write(block)


# ============================================================
# Color test
# ============================================================

def is_color_image(path):

    with Image.open(path) as im:

        im = im.convert("RGB")
        im.thumbnail((160, 160))

        pixels = list(
            im.getdata()
        )

    if not pixels:
        return False

    chromatic = sum(
        1
        for r, g, b in pixels
        if (
            max(r, g, b)
            -
            min(r, g, b)
        ) >= COLOR_CHANNEL_DELTA
    )

    return (
        chromatic
        /
        len(pixels)
        >= COLOR_PIXEL_FRACTION
    )


# ============================================================
# Archive current collection
# ============================================================

def archive_current_collection():

    ARCHIVE.mkdir(
        exist_ok=True
    )

    base = (
        datetime.now()
        .strftime("%Y-%m-%d")
    )

    destination = (
        ARCHIVE / base
    )

    n = 2

    while destination.exists():

        destination = (
            ARCHIVE
            /
            ("%s_%d" % (base, n))
        )

        n += 1

    destination.mkdir(
        parents=True
    )

    if ORIGINAL.exists():

        shutil.move(
            str(ORIGINAL),
            str(
                destination
                /
                "original"
            )
        )

    if META.exists():

        shutil.move(
            str(META),
            str(
                destination
                /
                META.name
            )
        )

    print()
    print(
        "Archived current collection to:"
    )
    print(destination)


def delete_current_collection():

    if ORIGINAL.exists():
        shutil.rmtree(ORIGINAL)

    if META.exists():

        try:
            META.unlink()

        except OSError:
            pass


# ============================================================
# Prepare collection
# ============================================================

def prepare_collection():

    ORIGINAL.mkdir(
        exist_ok=True
    )

    existing_count = len(
        [
            p
            for p in ORIGINAL.iterdir()
            if p.is_file()
        ]
    )

    print()
    print(
        "Existing images in original/:",
        existing_count
    )

    print()
    print(
        "[N] Start a NEW collection"
    )
    print(
        "[A] ADD to current collection"
    )
    print()

    choice = input(
        "Select [N/A] (default N): "
    ).strip().lower()

    add_mode = (
        choice == "a"
    )

    if add_mode:
        return True

    if (
        existing_count > 0
        or META.exists()
    ):

        print()
        print(
            "NEW mode replaces "
            "the current collection."
        )
        print()

        answer = input(
            "Archive current collection "
            "before replacing it? [Y/n]: "
        ).strip().lower()

        if answer not in (
            "n",
            "no"
        ):

            archive_current_collection()

        else:

            print()
            print(
                "WARNING: the current collection "
                "will be permanently deleted."
            )
            print()

            confirm = input(
                "Delete without archiving? [y/N]: "
            ).strip().lower()

            if confirm not in (
                "y",
                "yes"
            ):

                print()
                print(
                    "Cancelled."
                )

                return None

            delete_current_collection()

    ORIGINAL.mkdir(
        exist_ok=True
    )

    return False


# ============================================================
# Interactive helpers
# ============================================================

def ask_collection_type():

    print()
    print("Collection type:")
    print("  1. Paintings")
    print(
        "  2. All Open Access objects"
    )
    print()

    value = input(
        "Select [1/2] (default 1): "
    ).strip()

    if value == "2":
        return "all"

    return "painting"


def ask_object_type():

    print()
    print("Object type filter:")
    print("  1. Any object type")
    print("  2. Photograph")
    print(
        "  3. Print / engraving / lithograph"
    )
    print(
        "  4. Drawing / watercolor"
    )
    print("  5. Sculpture")
    print("  6. Ceramics")
    print("  7. Textile / costume")
    print(
        "  8. Furniture / decorative arts"
    )
    print("  9. Arms & armor")
    print(" 10. Manuscript / book")
    print(
        " 11. Poster / graphic design"
    )
    print()

    value = input(
        "Select [1-11] (default 1): "
    ).strip()

    return OBJECT_MENU.get(
        value,
        "any"
    )


def ask_color():

    print()

    value = input(
        "Color images only? [Y/n]: "
    ).strip().lower()

    return (
        value
        not in (
            "n",
            "no"
        )
    )


def ask_subject():

    print()
    print(
        "Subject filter "
        "(multiple selections allowed):"
    )
    print("  1. Any subject")
    print("  2. Portrait / figure")
    print("  3. Landscape / nature")
    print(
        "  4. Still life / flowers / food"
    )
    print("  5. City / architecture")
    print("  6. Animals")
    print()

    value = input(
        "Select [1-6, comma separated] "
        "(default 1): "
    ).strip()

    return ",".join(
        parse_subject_choices(value)
    )


def ask_artist():

    print()
    print("Artist filter (optional):")
    print("  renoir")
    print("  claude monet")
    print("  renoir, pissarro, sisley")
    print()
    print(
        "Commas mean OR. "
        "Matching is against Artist Display Name only."
    )
    print()

    return input(
        "Artist(s), or Enter for any artist: "
    ).strip()


def ask_query(paintings_only):

    print()
    print("General keyword examples:")
    print("  landscape")
    print("  water lilies")
    print("  landscape, garden")
    print("  korean ceramics")
    print("  japanese woodblock")
    print()

    print(
        "Rule: spaces = AND, commas = OR"
    )

    if paintings_only:

        print(
            "Press Enter for no general metadata filter."
        )

    else:

        print(
            "Press Enter for no general metadata filter."
        )

    print()

    return input(
        "General keyword(s): "
    ).strip()


# ============================================================
# Command quoting
# ============================================================

def command_quote(value):

    value = str(value)

    if not value:
        return '""'

    if any(
        ch.isspace()
        or ch in ',&|<>^'
        for ch in value
    ):

        value = value.replace(
            '"',
            '\\"'
        )

        return (
            '"'
            + value
            + '"'
        )

    return value


# ============================================================
# Build reproducible command
# ============================================================

def build_download_command(
    collection_type,
    object_type,
    subject_value,
    color_only,
    artist,
    query,
    target
):

    script = Path(
        sys.argv[0]
    ).name

    parts = [
        "python",
        command_quote(script),
        "--type",
        collection_type,
    ]

    if collection_type == "all":

        parts.extend([
            "--object",
            object_type,
        ])

    parts.extend([
        "--subject",
        subject_value,
    ])

    if color_only:
        parts.append("--color")
    else:
        parts.append("--no-color")

    if artist:

        parts.extend([
            "--artist",
            command_quote(artist),
        ])

    if query:

        parts.extend([
            "--query",
            command_quote(query),
        ])

    parts.extend([
        "--target",
        str(target),
    ])

    return " ".join(parts)


# ============================================================
# Dry-run report
# ============================================================

def show_dry_run(
    collection_type,
    object_type,
    subject_choices,
    subject_labels,
    color_only,
    artist,
    query,
    target,
    match_count
):

    print()
    print(
        "=========================================="
    )
    print(
        " DRY RUN RESULT"
    )
    print(
        "=========================================="
    )

    print()

    if collection_type == "painting":

        print(
            "Collection type : Paintings"
        )

    else:

        print(
            "Collection type : "
            "All Open Access objects"
        )

        print(
            "Object filter   :",
            OBJECT_FILTERS[
                object_type
            ][0]
        )

    print(
        "Subject         :",
        " + ".join(subject_labels)
    )

    print(
        "Color only      :",
        "Yes"
        if color_only
        else "No"
    )

    print(
        "Artist          :",
        artist
        if artist
        else "(any)"
    )

    print(
        "General query   :",
        query
        if query
        else "(none)"
    )

    print(
        "Target          :",
        target
    )

    print()

    print(
        "Matching metadata records :",
        match_count
    )

    print(
        "Download target           :",
        min(
            target,
            match_count
        )
    )

    if color_only:

        print()
        print(
            "NOTE: Color filtering was NOT evaluated."
        )

        print(
            "It requires downloading the actual images."
        )

    print()
    print(
        "No artwork, metadata, archive, or current "
        "collection was changed."
    )

    command = build_download_command(
        collection_type,
        object_type,
        ",".join(subject_choices),
        color_only,
        artist,
        query,
        target
    )

    print()
    print(
        "To download with exactly these search settings:"
    )
    print()
    print(command)
    print()


# ============================================================
# Main
# ============================================================

def main():

    parser = build_parser()
    args = parser.parse_args()

    # Diagnostic mode has priority over normal operation.

    if args.diagnose is not None:

        print()
        print(
            "%s v%s"
            % (
                SCRIPT_NAME,
                VERSION
            )
        )

        return diagnose_keyword(
            args.diagnose,
            check_api=args.check_api
        )

    if args.check_api:

        parser.error(
            "--check-api requires --diagnose KEYWORD"
        )

    print()
    print(
        "=========================================="
    )
    print(
        " %s v%s"
        % (
            SCRIPT_NAME,
            VERSION
        )
    )
    print(
        " %s"
        % EDITION
    )
    print(
        " Build: %s"
        % BUILD_DATE
    )
    print(
        "=========================================="
    )

    collection_type = (
        args.collection_type
    )

    if collection_type is None:

        collection_type = (
            ask_collection_type()
        )

    paintings_only = (
        collection_type
        == "painting"
    )

    if paintings_only:

        object_type = "any"
        object_terms = []

    else:

        object_type = (
            args.object_type
        )

        if object_type is None:

            object_type = (
                ask_object_type()
            )

        object_terms = (
            OBJECT_FILTERS[
                object_type
            ][1]
        )

    color_only = (
        args.color_only
    )

    if color_only is None:

        color_only = ask_color()

    subject_value = (
        args.subject
    )

    if subject_value is None:

        subject_value = (
            ask_subject()
        )

    subject_choices = (
        parse_subject_choices(
            subject_value
        )
    )

    (
        subject_labels,
        subject_terms
    ) = get_subject_info(
        subject_choices
    )

    if args.artist is None:

        artist = ask_artist()

    else:

        artist = (
            args.artist.strip()
        )

    artists = (
        parse_artist_filter(
            artist
        )
    )

    if args.query is None:

        query = ask_query(
            paintings_only
        )

    else:

        query = (
            args.query.strip()
        )

    groups = parse_query(
        query
    )

    target = (
        args.target
        if args.target is not None
        else DEFAULT_TARGET
    )

    if target <= 0:

        parser.error(
            "--target must be greater than zero"
        )

    download_csv()

    candidates, match_count = (
        choose_candidates(
            groups,
            artists,
            paintings_only,
            subject_terms,
            object_terms
        )
    )

    if args.dry_run:

        show_dry_run(
            collection_type,
            object_type,
            subject_choices,
            subject_labels,
            color_only,
            artist,
            query,
            target,
            match_count
        )

        return 0

    if not candidates:

        print()
        print(
            "No matching records were found."
        )

        return 2

    add_mode = (
        prepare_collection()
    )

    if add_mode is None:
        return 1

    download_target = min(
        target,
        len(candidates)
    )

    print()
    print(
        "Selected target before image checks: %d"
        % download_target
    )

    saved = []
    failures = 0
    color_skips = 0

    if (
        add_mode
        and META.exists()
    ):

        try:

            old_records = json.loads(
                META.read_text(
                    encoding="utf-8"
                )
            )

            if isinstance(
                old_records,
                list
            ):

                saved.extend(
                    old_records
                )

        except Exception:
            pass

    existing_ids = {
        rec.get("objectID")
        for rec in saved
        if (
            isinstance(rec, dict)
            and
            rec.get("objectID")
            is not None
        )
    }

    added_this_run = 0

    print()
    print(
        "Downloading/selecting up to "
        "%d selected images..."
        % download_target
    )

    for item in candidates:

        if (
            added_this_run
            >= download_target
        ):
            break

        oid = item[
            "objectID"
        ]

        if oid in existing_ids:
            continue

        try:

            obj = object_json(
                oid
            )

            if not obj.get(
                "isPublicDomain"
            ):
                continue

            image = (
                obj.get(
                    "primaryImage"
                )
                or
                obj.get(
                    "primaryImageSmall"
                )
                or
                ""
            )

            if not image:
                continue

            out = ORIGINAL / (
                "met_%06d.jpg"
                % oid
            )

            if (
                not out.exists()
                or
                out.stat().st_size
                < 10000
            ):

                download_image(
                    image,
                    out
                )

            if (
                color_only
                and
                not is_color_image(out)
            ):

                color_skips += 1

                print(
                    "  Skip %s: "
                    "grayscale/nearly grayscale image"
                    % oid
                )

                try:
                    out.unlink()

                except OSError:
                    pass

                continue

            rec = dict(item)

            rec["title"] = (
                obj.get("title")
                or
                item["title"]
            )

            rec["artist"] = (
                obj.get(
                    "artistDisplayName"
                )
                or
                item["artist"]
            )

            rec["date"] = (
                obj.get(
                    "objectDate"
                )
                or
                item["date"]
            )

            rec["objectURL"] = (
                obj.get(
                    "objectURL"
                )
                or
                item["objectURL"]
            )

            rec["file"] = (
                out.name
            )

            saved.append(
                rec
            )

            existing_ids.add(
                oid
            )

            added_this_run += 1

            print(
                "[%3d/%d] %s - %s"
                % (
                    added_this_run,
                    download_target,
                    rec["artist"]
                    or "Unknown",
                    rec["title"]
                    or "Untitled",
                )
            )

            time.sleep(
                0.20
            )

        except urllib.error.HTTPError as e:

            failures += 1

            print(
                "  Skip %s: HTTP %s"
                % (
                    oid,
                    e.code
                )
            )

            if e.code in (
                403,
                429
            ):

                print(
                    "  Server is rate-limiting; "
                    "waiting 5 seconds..."
                )

                time.sleep(5)

        except Exception as e:

            failures += 1

            print(
                "  Skip %s: %s"
                % (
                    oid,
                    e
                )
            )

    META.write_text(
        json.dumps(
            saved,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()

    print(
        "Added this run:",
        added_this_run
    )

    print(
        "Total images in metadata:",
        len(saved)
    )

    print(
        "Failures:",
        failures
    )

    if color_only:

        print(
            "Skipped by color filter:",
            color_skips
        )

    print()
    print(
        "Run make_gallery.py to rebuild "
        "the EO1 display collection."
    )

    return 0


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )