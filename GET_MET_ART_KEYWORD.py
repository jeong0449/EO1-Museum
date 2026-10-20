from pathlib import Path
import csv, json, random, time, urllib.request, urllib.error, sys

ROOT = Path(__file__).resolve().parent
CSVFILE = ROOT / "MetObjects.csv"
ORIGINAL = ROOT / "original"
META = ROOT / "met_metadata.json"

CSV_URL = "https://media.githubusercontent.com/media/metmuseum/openaccess/master/MetObjects.csv"
OBJECT_API = "https://collectionapi.metmuseum.org/public/collection/v1/objects/{}"

TARGET = 100
CANDIDATE_POOL = 600
TIMEOUT = 45
UA = "Mozilla/5.0 EO1-Met-Gallery/3.0"

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
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    return urllib.request.urlopen(req, timeout=TIMEOUT)

def download_csv():
    if CSVFILE.exists() and CSVFILE.stat().st_size > 10_000_000:
        print("Using existing MetObjects.csv (%.1f MB)" % (CSVFILE.stat().st_size / 1048576))
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
                    print("\r  %.0f%%  (%.1f / %.1f MB)" %
                          (done * 100 / total, done / 1048576, total / 1048576),
                          end="", flush=True)
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
        words = [w.casefold() for w in part.strip().split() if w.strip()]
        if words:
            groups.append(words)
    return groups

def matches_query(row, groups):
    if not groups:
        return True

    search_text = " ".join(
        row.get(field, "") or "" for field in SEARCH_FIELDS
    ).casefold()

    return any(all(word in search_text for word in group) for group in groups)

def choose_candidates(groups):
    if groups:
        print("Scanning CSV for matching public-domain paintings...")
    else:
        print("Scanning CSV for public-domain paintings...")

    reservoir = []
    seen = 0

    with open(CSVFILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row.get("Is Public Domain", "").strip().lower() != "true":
                continue

            classification = row.get("Classification", "").strip().lower()
            object_name = row.get("Object Name", "").strip().lower()

            # Keep conventional paintings; tolerate variations in the dataset.
            if "paint" not in classification and "paint" not in object_name:
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
                "artist": row.get("Artist Display Name", ""),
                "date": row.get("Object Date", ""),
                "objectURL": row.get("Link Resource", "")
            }

            # Reservoir sampling keeps a random pool without storing all matches.
            if len(reservoir) < CANDIDATE_POOL:
                reservoir.append(item)
            else:
                j = random.randrange(seen)
                if j < CANDIDATE_POOL:
                    reservoir[j] = item

    random.shuffle(reservoir)
    print("Matching eligible painting records:", seen)
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

def main():
    print()
    print("==========================================")
    print(" The Met Gallery Downloader v3")
    print(" Keyword Search Edition")
    print("==========================================")
    print()
    print("Keyword examples:")
    print("  monet")
    print("  monet landscape")
    print("  monet, renoir")
    print("  monet landscape, renoir portrait")
    print()
    print("Rule: spaces = AND, commas = OR")
    print("Press Enter for random paintings without a keyword filter.")
    print()

    query = input("Search keyword(s): ").strip()
    groups = parse_query(query)

    if groups:
        pretty = " OR ".join("(" + " AND ".join(g) + ")" for g in groups)
        print("Search rule:", pretty)
    else:
        print("Search rule: all eligible paintings")

    print()
    download_csv()
    candidates = choose_candidates(groups)

    if not candidates:
        print()
        print("No matching painting records were found.")
        print("Try fewer or broader keywords.")
        return 2

    saved = []
    failures = 0

    print("Downloading/selecting up to %d images..." % TARGET)

    for item in candidates:
        if len(saved) >= TARGET:
            break

        oid = item["objectID"]

        try:
            obj = object_json(oid)

            if not obj.get("isPublicDomain"):
                continue

            image = obj.get("primaryImage") or obj.get("primaryImageSmall") or ""
            if not image:
                continue

            out = ORIGINAL / ("met_%06d.jpg" % oid)

            if not out.exists() or out.stat().st_size < 10000:
                download_image(image, out)

            rec = dict(item)
            rec["title"] = obj.get("title") or item["title"]
            rec["artist"] = obj.get("artistDisplayName") or item["artist"]
            rec["date"] = obj.get("objectDate") or item["date"]
            rec["objectURL"] = obj.get("objectURL") or item["objectURL"]
            rec["file"] = out.name
            saved.append(rec)

            print("[%3d/%d] %s - %s" % (
                len(saved), TARGET,
                rec["artist"] or "Unknown",
                rec["title"] or "Untitled"
            ))

            time.sleep(0.20)

        except urllib.error.HTTPError as e:
            failures += 1
            print("  Skip %s: HTTP %s" % (oid, e.code))
            if e.code in (403, 429):
                print("  Server is rate-limiting requests; waiting 5 seconds...")
                time.sleep(5)

        except Exception as e:
            failures += 1
            print("  Skip %s: %s" % (oid, e))

    META.write_text(
        json.dumps(saved, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print()
    print("Finished: %d images selected/saved in %s" % (len(saved), ORIGINAL))
    print("Metadata:", META)
    print("Failures:", failures)

    if len(saved) == 0:
        print()
        print("No images were downloaded.")
        print("The Met object API may also be temporarily unavailable.")
        return 2

    return 0

if __name__ == "__main__":
    sys.exit(main())
