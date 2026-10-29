from pathlib import Path
from datetime import datetime
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
VERSION = "3.6"
EDITION = "Keyword + Filter Edition"
BUILD_DATE = "2026-10-29"

# Version history
#
# v3.6
#   - Added multiple subject-filter selection.
#   - Added object-type filters for non-painting collections.
#   - Subject filters can be combined, e.g. 2,3,4.
#   - Retained default color-image filtering.
#   - Retained dynamic target/progress display.
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

TARGET = 100
CANDIDATE_POOL = 600
TIMEOUT = 45

UA = "Mozilla/5.0 EO1-Met-Gallery/" + VERSION


# ============================================================
# Color filter settings
# ============================================================

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
# Object type filters
# Used mainly for All Open Access objects
# ============================================================

OBJECT_FILTERS = {

    "1": (
        "Any object type",
        []
    ),

    "2": (
        "Photograph",
        [
            "photograph",
            "photography",
        ]
    ),

    "3": (
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

    "4": (
        "Drawing / watercolor",
        [
            "drawing",
            "watercolor",
            "watercolour",
            "pastel",
            "gouache",
        ]
    ),

    "5": (
        "Sculpture",
        [
            "sculpture",
            "statue",
            "statuette",
            "relief",
        ]
    ),

    "6": (
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

    "7": (
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

    "8": (
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

    "9": (
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

    "10": (
        "Manuscript / book",
        [
            "manuscript",
            "book",
            "codex",
            "folio",
            "album",
        ]
    ),

    "11": (
        "Poster / graphic design",
        [
            "poster",
            "graphic design",
            "advertisement",
            "commercial print",
        ]
    ),
}


# ============================================================
# Subject filters
# Multiple selections are allowed.
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
# Download Met CSV if necessary
# ============================================================

def download_csv():

    if CSVFILE.exists():
        return

    print()
    print("MetObjects.csv not found.")
    print("Downloading Met Open Access metadata...")
    print()

    with fetch(CSV_URL) as r, open(CSVFILE, "wb") as f:

        while True:

            block = r.read(1024 * 1024)

            if not block:
                break

            f.write(block)

    print("Saved:", CSVFILE)


# ============================================================
# Keyword parser
#
# spaces = AND
# commas = OR
# ============================================================

def parse_query(query):

    query = query.strip()

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


# ============================================================
# Keyword matching
# ============================================================

def search_text(row):

    return " ".join(
        row.get(field, "") or ""
        for field in SEARCH_FIELDS
    ).casefold()


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


def matches_object_filter(row, object_terms):

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


def matches_subject_filter(row, subject_terms):

    if not subject_terms:
        return True

    haystack = subject_filter_text(row)

    return any(
        term.casefold() in haystack
        for term in subject_terms
    )


# ============================================================
# Candidate selection
# ============================================================

def choose_candidates(
    groups,
    paintings_only=True,
    subject_terms=None,
    object_terms=None
):

    subject_terms = subject_terms or []
    object_terms = object_terms or []

    reservoir = []
    seen = 0

    print()
    print("Searching Met metadata...")

    with open(
        CSVFILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            # Public Domain only

            if (
                row.get(
                    "Is Public Domain",
                    ""
                ).strip().lower()
                != "true"
            ):
                continue

            # Painting-only mode

            if paintings_only:

                classification = (
                    row.get(
                        "Classification",
                        ""
                    )
                    .strip()
                    .lower()
                )

                object_name = (
                    row.get(
                        "Object Name",
                        ""
                    )
                    .strip()
                    .lower()
                )

                if (
                    "paint" not in classification
                    and
                    "paint" not in object_name
                ):
                    continue

            # Keyword filter

            if not matches_query(
                row,
                groups
            ):
                continue

            # Object-type filter

            if not matches_object_filter(
                row,
                object_terms
            ):
                continue

            # Subject filter

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
                "title": row.get("Title", ""),
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

            # Reservoir sampling

            if len(reservoir) < CANDIDATE_POOL:

                reservoir.append(item)

            else:

                j = random.randrange(seen)

                if j < CANDIDATE_POOL:
                    reservoir[j] = item

    random.shuffle(reservoir)

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

    return reservoir


# ============================================================
# Met object API
# ============================================================

def object_json(oid):

    with fetch(
        OBJECT_API.format(oid)
    ) as r:

        return json.load(r)


# ============================================================
# Image download
# ============================================================

def download_image(url, path):

    with fetch(url) as r, open(path, "wb") as f:

        while True:

            block = r.read(1024 * 1024)

            if not block:
                break

            f.write(block)


# ============================================================
# Color-image test
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

    fraction = (
        chromatic
        /
        len(pixels)
    )

    return (
        fraction
        >= COLOR_PIXEL_FRACTION
    )


# ============================================================
# Archive current collection
# ============================================================

def archive_current_collection():

    ARCHIVE.mkdir(
        exist_ok=True
    )

    base = datetime.now().strftime(
        "%Y-%m-%d"
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

        target = (
            destination
            /
            "original"
        )

        shutil.move(
            str(ORIGINAL),
            str(target)
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


# ============================================================
# Delete current collection
# ============================================================

def delete_current_collection():

    if ORIGINAL.exists():
        shutil.rmtree(ORIGINAL)

    if META.exists():

        try:
            META.unlink()

        except OSError:
            pass


# ============================================================
# Collection mode
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
    print("[N] Start a NEW collection")
    print("[A] ADD to current collection")
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
                print("Cancelled.")

                return None

            delete_current_collection()

    ORIGINAL.mkdir(
        exist_ok=True
    )

    return False


# ============================================================
# Main
# ============================================================

def main():

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

    # --------------------------------------------------------
    # NEW / ADD
    # --------------------------------------------------------

    add_mode = prepare_collection()

    if add_mode is None:
        return 1

    # --------------------------------------------------------
    # Collection type
    # --------------------------------------------------------

    print()
    print("Collection type:")
    print("  1. Paintings")
    print("  2. All Open Access objects")
    print()

    mode = input(
        "Select [1/2] (default 1): "
    ).strip()

    paintings_only = (
        mode != "2"
    )

    # --------------------------------------------------------
    # Object-type filter
    # --------------------------------------------------------

    object_terms = []

    if not paintings_only:

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

        object_choice = input(
            "Select [1-11] (default 1): "
        ).strip()

        if (
            object_choice
            not in OBJECT_FILTERS
        ):
            object_choice = "1"

        (
            object_label,
            object_terms
        ) = OBJECT_FILTERS[
            object_choice
        ]

        print(
            "Object type filter:",
            object_label
        )

    # --------------------------------------------------------
    # Color filter
    # Default = YES
    # --------------------------------------------------------

    print()

    color_answer = input(
        "Color images only? [Y/n]: "
    ).strip().lower()

    color_only = (
        color_answer
        not in (
            "n",
            "no"
        )
    )

    if color_only:

        print(
            "Color filter enabled "
            "(grayscale/nearly grayscale "
            "images will be skipped)."
        )

    else:

        print(
            "Color filter disabled."
        )

    # --------------------------------------------------------
    # Subject filter
    # Multiple selections allowed
    # --------------------------------------------------------

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

    subject_input = input(
        "Select [1-6, comma separated] "
        "(default 1): "
    ).strip()

    if not subject_input:

        subject_choices = ["1"]

    else:

        subject_choices = [
            x.strip()
            for x in subject_input.split(",")
            if (
                x.strip()
                in SUBJECT_FILTERS
            )
        ]

        if (
            not subject_choices
            or "1" in subject_choices
        ):

            subject_choices = ["1"]

    subject_labels = []
    subject_terms = []

    for choice in subject_choices:

        (
            label,
            terms
        ) = SUBJECT_FILTERS[
            choice
        ]

        subject_labels.append(label)
        subject_terms.extend(terms)

    print(
        "Subject filter:",
        " + ".join(subject_labels)
    )

    # --------------------------------------------------------
    # Keyword
    # --------------------------------------------------------

    print()
    print("Keyword examples:")
    print("  monet")
    print("  monet landscape")
    print("  monet, renoir")
    print(
        "  renoir, monet, pissarro, "
        "sisley, morisot, cassatt"
    )
    print("  korean ceramics")
    print("  japanese woodblock")
    print("  egyptian sculpture")
    print()

    print(
        "Rule: spaces = AND, commas = OR"
    )

    if paintings_only:

        print(
            "Press Enter for random paintings "
            "without a keyword filter."
        )

    else:

        print(
            "Press Enter for random Open Access "
            "objects without a keyword filter."
        )

    print()

    query = input(
        "Search keyword(s): "
    ).strip()

    groups = parse_query(query)

    if groups:

        pretty = " OR ".join(
            "("
            +
            " AND ".join(group)
            +
            ")"
            for group in groups
        )

        print(
            "Search rule:",
            pretty
        )

    else:

        if paintings_only:

            print(
                "Search rule: "
                "all eligible paintings"
            )

        else:

            print(
                "Search rule: "
                "all eligible objects"
            )

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    print()

    download_csv()

    # --------------------------------------------------------
    # Candidate selection
    # --------------------------------------------------------

    candidates = choose_candidates(
        groups,
        paintings_only,
        subject_terms,
        object_terms
    )

    if not candidates:

        print()

        noun = (
            "painting"
            if paintings_only
            else "object"
        )

        print(
            "No matching %s records were found."
            % noun
        )

        print(
            "Try fewer or broader keywords."
        )

        return 2

    download_target = min(
        TARGET,
        len(candidates)
    )

    print()
    print(
        "Selected target before image checks: %d"
        % download_target
    )

    print(
        "(Some records may still be skipped "
        "for missing images, download errors, "
        "or the color filter.)"
    )

    print()

    # --------------------------------------------------------
    # Existing metadata for ADD mode
    # --------------------------------------------------------

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

    print(
        "Downloading/selecting up to "
        "%d selected images..."
        % download_target
    )

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

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

            obj = object_json(oid)

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

            # ------------------------------------------------
            # Actual image color test
            # ------------------------------------------------

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

            # ------------------------------------------------
            # Metadata
            # ------------------------------------------------

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

            rec["file"] = out.name

            saved.append(rec)

            existing_ids.add(oid)

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

            time.sleep(0.20)

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
                    "  Server is rate-limiting "
                    "requests; waiting 5 seconds..."
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

    # --------------------------------------------------------
    # Save metadata
    # --------------------------------------------------------

    META.write_text(
        json.dumps(
            saved,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

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
        "Images stored in:",
        ORIGINAL
    )

    print(
        "Metadata:",
        META
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

    if added_this_run == 0:

        print()
        print(
            "No new images were downloaded."
        )

        print(
            "Try broader keywords or filters."
        )

        return 2

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