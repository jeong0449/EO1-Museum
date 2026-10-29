from pathlib import Path
import csv, json, random, time, urllib.request, urllib.error, sys, shutil
from datetime import datetime
from PIL import Image

ROOT = Path(__file__).resolve().parent
CSVFILE = ROOT / "MetObjects.csv"
ORIGINAL = ROOT / "original"
META = ROOT / "met_metadata.json"
ARCHIVE = ROOT / "archive"

CSV_URL = "https://media.githubusercontent.com/media/metmuseum/openaccess/master/MetObjects.csv"
OBJECT_API = "https://collectionapi.metmuseum.org/public/collection/v1/objects/{}"

TARGET = 100
CANDIDATE_POOL = 600
TIMEOUT = 45
UA = "Mozilla/5.0 EO1-Met-Gallery/3.4"

# Color-image test. A sampled pixel is considered chromatic when the
# difference between its strongest and weakest RGB channels exceeds
# COLOR_CHANNEL_DELTA. The image is accepted as color when at least
# COLOR_PIXEL_FRACTION of sampled pixels are chromatic.
COLOR_CHANNEL_DELTA = 12
COLOR_PIXEL_FRACTION = 0.03

ORIGINAL.mkdir(exist_ok=True)

# Search these MetObjects.csv fields.
SEARCH_FIELDS = [
    "Title",
    "Artist Display Name",
    "Artist Nationality",
    "Object Name",
    "Classification",
    "Culture",
    "Period",
    "Dynasty",
    "Reign",
    "Object Date",
    "Medium",
    "Credit Line",
]


def fetch(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "*/*"}
    )
    return urllib.request.urlopen(req, timeout=TIMEOUT)


def download_csv():
    if CSVFILE.exists() and CSVFILE.stat().st_size > 10_000_000:
        print(
            "Using existing MetObjects.csv (%.1f MB)"
            % (CSVFILE.stat().st_size / 1048576)
        )
        return

    print("Downloading The Met Open Access CSV.")
    print("This is a large file (about 300 MB), so the first run can take a while.")

    tmp = CSVFILE.with_suffix(".csv.part")

    try:
        with fetch(CSV_URL) as r, open(tmp, "wb") as f:
            total = int(r.headers.get("Content-Length", "0") or 0)
            done = 0

            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break

                f.write(chunk)
                done += len(chunk)

                if total:
                    print(
                        "\r  %.0f%%  (%.1f / %.1f MB)"
                        % (
                            done * 100 / total,
                            done / 1048576,
                            total / 1048576,
                        ),
                        end="",
                        flush=True,
                    )

        print()
        tmp.replace(CSVFILE)

    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def parse_query(text):
    """
    Comma = OR between groups.
    Spaces = AND inside each group.

      monet landscape
        -> monet AND landscape

      monet, renoir
        -> monet OR renoir

      monet landscape, renoir portrait
        -> (monet AND landscape) OR (renoir AND portrait)

    Blank input means no keyword filter.
    """
    groups = []

    for part in text.split(","):
        words = [
            w.casefold()
            for w in part.strip().split()
            if w.strip()
        ]

        if words:
            groups.append(words)

    return groups


def matches_query(row, groups):
    if not groups:
        return True

    search_text = " ".join(
        row.get(field, "") or ""
        for field in SEARCH_FIELDS
    ).casefold()

    return any(
        all(word in search_text for word in group)
        for group in groups
    )


def choose_candidates(groups, paintings_only=True):
    noun = "paintings" if paintings_only else "objects"

    if groups:
        print(
            "Scanning CSV for matching public-domain %s..."
            % noun
        )
    else:
        print(
            "Scanning CSV for public-domain %s..."
            % noun
        )

    reservoir = []
    seen = 0

    with open(
        CSVFILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            # Public Domain only.
            if (
                row.get("Is Public Domain", "")
                .strip()
                .lower()
                != "true"
            ):
                continue

            classification = (
                row.get("Classification", "")
                .strip()
                .lower()
            )

            object_name = (
                row.get("Object Name", "")
                .strip()
                .lower()
            )

            # Paintings mode:
            # preserve the original painting filter.
            #
            # All Objects mode:
            # do not restrict Classification/Object Name.
            if paintings_only:
                if (
                    "paint" not in classification
                    and "paint" not in object_name
                ):
                    continue

            if not matches_query(row, groups):
                continue

            oid = row.get("Object ID", "").strip()

            if not oid.isdigit():
                continue

            seen += 1

            item = {
                "objectID": int(oid),
                "title": row.get("Title", ""),
                "artist": row.get(
                    "Artist Display Name", ""
                ),
                "date": row.get("Object Date", ""),
                "objectURL": row.get(
                    "Link Resource", ""
                ),
            }

            # Reservoir sampling keeps a random pool
            # without storing every matching record.
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
        % (label, seen)
    )

    return reservoir


def object_json(oid):
    with fetch(OBJECT_API.format(oid)) as r:
        return json.load(r)


def download_image(url, path):
    with fetch(url) as r, open(path, "wb") as f:
        while True:
            b = r.read(1024 * 1024)

            if not b:
                break

            f.write(b)


def is_color_image(path):
    """
    Return True when the downloaded image contains a meaningful amount
    of chromatic information.

    The image is reduced to a small RGB thumbnail for speed. This is an
    image-content test, not a metadata guess: grayscale and nearly
    grayscale works are rejected when "Color images only" is enabled.
    """
    with Image.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((160, 160))

        pixels = list(im.getdata())

    if not pixels:
        return False

    chromatic = sum(
        1
        for r, g, b in pixels
        if max(r, g, b) - min(r, g, b) >= COLOR_CHANNEL_DELTA
    )

    return (chromatic / len(pixels)) >= COLOR_PIXEL_FRACTION



# ============================================================
# Collection management
# ============================================================

def count_existing_images():
    if not ORIGINAL.exists():
        return 0
    return len([
        p for p in ORIGINAL.iterdir()
        if p.is_file()
        and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
    ])


def archive_collection():
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    date_name = datetime.now().strftime("%Y-%m-%d")
    archive_dir = ARCHIVE / date_name

    if archive_dir.exists():
        i = 2
        while (ARCHIVE / f"{date_name}_{i}").exists():
            i += 1
        archive_dir = ARCHIVE / f"{date_name}_{i}"

    archive_dir.mkdir(parents=True, exist_ok=False)

    print()
    print("Archiving current original/ collection...")
    print(f"  -> {archive_dir}")

    moved = 0
    if ORIGINAL.exists():
        for item in list(ORIGINAL.iterdir()):
            shutil.move(str(item), str(archive_dir / item.name))
            moved += 1

    if META.exists():
        shutil.move(str(META), str(archive_dir / META.name))

    ORIGINAL.mkdir(parents=True, exist_ok=True)
    print(f"Archived files: {moved}")
    print("Current collection archived.")
    return archive_dir


def delete_collection():
    if ORIGINAL.exists():
        for item in list(ORIGINAL.iterdir()):
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    if META.exists():
        META.unlink()

    ORIGINAL.mkdir(parents=True, exist_ok=True)
    print("Current collection deleted.")


def main():
    print()
    print("==========================================")
    print(" The Met Gallery Downloader v3.4")
    print(" Keyword Search Edition")
    print("==========================================")
    print()

    existing_count = count_existing_images()

    print(f"Existing images in original/: {existing_count}")

    if existing_count > 0:
        print()
        print("[N] Start a NEW collection")
        print("[A] ADD to current collection")
        print()
        print("NEW mode replaces the current collection.")
        print()

        collection_mode = input(
            "Select [N/A] (default N): "
        ).strip().lower()

        if collection_mode == "a":
            add_mode = True
            print()
            print("Add mode selected.")
        else:
            add_mode = False
            print()
            print("NEW mode will replace all files currently in:")
            print(f"  {ORIGINAL}")
            print()

            archive_answer = input(
                "Archive current collection before replacing it? [Y/n]: "
            ).strip().lower()

            if archive_answer in ("", "y", "yes"):
                archive_collection()
            else:
                print()
                print(
                    "WARNING: the current collection will be permanently deleted."
                )
                confirm = input(
                    "Delete without archiving? [y/N]: "
                ).strip().lower()

                if confirm != "y":
                    print("Cancelled.")
                    return 0

                delete_collection()
    else:
        add_mode = False
        ORIGINAL.mkdir(parents=True, exist_ok=True)

    print()

    print("Collection type:")
    print("  1. Paintings")
    print("  2. All Open Access objects")
    print()

    mode = input(
        "Select [1/2] (default 1): "
    ).strip()

    paintings_only = (mode != "2")

    print()
    color_answer = input(
        "Color images only? [y/N]: "
    ).strip().lower()
    color_only = color_answer in ("y", "yes")

    if color_only:
        print(
            "Color filter enabled "
            "(grayscale/nearly grayscale images will be skipped)."
        )
    else:
        print("Color filter disabled.")

    print()
    print("Keyword examples:")
    print("  monet")
    print("  monet landscape")
    print("  monet, renoir")
    print("  korean ceramics")
    print("  japanese woodblock")
    print("  egyptian sculpture")
    print()
    print("Rule: spaces = AND, commas = OR")

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
            "(" + " AND ".join(g) + ")"
            for g in groups
        )

        print(
            "Search rule:",
            pretty
        )

    else:
        if paintings_only:
            print(
                "Search rule: all eligible paintings"
            )
        else:
            print(
                "Search rule: all eligible objects"
            )

    print()

    download_csv()

    candidates = choose_candidates(
        groups,
        paintings_only
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

    saved = []
    failures = 0
    color_skips = 0

    if add_mode and META.exists():
        try:
            existing_meta = json.loads(META.read_text(encoding="utf-8"))
            if isinstance(existing_meta, list):
                saved = existing_meta
        except Exception:
            saved = []

    existing_ids = {
        rec.get("objectID")
        for rec in saved
        if isinstance(rec, dict) and rec.get("objectID") is not None
    }
    added_this_run = 0

    print(
        "Downloading/selecting up to %d images..."
        % TARGET
    )

    for item in candidates:

        if add_mode:
            if added_this_run >= TARGET:
                break
        else:
            if len(saved) >= TARGET:
                break

        oid = item["objectID"]

        if oid in existing_ids:
            continue

        try:
            obj = object_json(oid)

            # Double-check Public Domain status
            # against the object API.
            if not obj.get("isPublicDomain"):
                continue

            image = (
                obj.get("primaryImage")
                or obj.get("primaryImageSmall")
                or ""
            )

            # Some museum objects have metadata
            # but no downloadable image.
            if not image:
                continue

            out = ORIGINAL / (
                "met_%06d.jpg" % oid
            )

            if (
                not out.exists()
                or out.stat().st_size < 10000
            ):
                download_image(
                    image,
                    out
                )

            if color_only and not is_color_image(out):
                color_skips += 1
                print(
                    "  Skip %s: grayscale/nearly grayscale image"
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
                or item["title"]
            )

            rec["artist"] = (
                obj.get("artistDisplayName")
                or item["artist"]
            )

            rec["date"] = (
                obj.get("objectDate")
                or item["date"]
            )

            rec["objectURL"] = (
                obj.get("objectURL")
                or item["objectURL"]
            )

            rec["file"] = out.name

            saved.append(rec)
            existing_ids.add(oid)
            added_this_run += 1

            print(
                "[%3d/%d] %s - %s"
                % (
                    (added_this_run if add_mode else len(saved)),
                    TARGET,
                    rec["artist"] or "Unknown",
                    rec["title"] or "Untitled",
                )
            )

            time.sleep(0.20)

        except urllib.error.HTTPError as e:

            failures += 1

            print(
                "  Skip %s: HTTP %s"
                % (oid, e.code)
            )

            if e.code in (403, 429):
                print(
                    "  Server is rate-limiting "
                    "requests; waiting 5 seconds..."
                )
                time.sleep(5)

        except Exception as e:

            failures += 1

            print(
                "  Skip %s: %s"
                % (oid, e)
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
        "Finished: %d images selected/saved in %s"
        % (
            len(saved),
            ORIGINAL
        )
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

    if len(saved) == 0:
        print()
        print(
            "No images were downloaded."
        )
        print(
            "The Met object API may also "
            "be temporarily unavailable."
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())