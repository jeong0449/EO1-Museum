from pathlib import Path
import json
import random
import shutil
import socket
import time
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET


# ============================================================
# EO1-Museum
# eMuseum Gallery Downloader v1.2
#
# New:
#   - clear original/ and start a new collection
#
# Resume:
#   - preserve existing collection
#   - continue until TARGET images are collected
#
# Download policy:
#   - random sampling across search results
#   - timeout + retry
#   - skip bad images
#   - save metadata after every successful image
# ============================================================

ROOT = Path(__file__).resolve().parent

KEY_FILE = ROOT / "emuseum_key.txt"
ORIGINAL = ROOT / "original"
META = ROOT / "emuseum_metadata.json"

BASE_URL = "https://apis.data.go.kr/1371027/openapi/list"

TARGET = 100
PAGE_SIZE = 100
CANDIDATE_POOL = 500

API_TIMEOUT = 30
IMAGE_TIMEOUT = 15
IMAGE_RETRIES = 2

API_DELAY = 0.15
DOWNLOAD_DELAY = 0.10

USER_AGENT = "EO1-Museum-eMuseum/1.2"


# ============================================================
# Service key
# ============================================================

def read_service_key():
    if not KEY_FILE.exists():
        print()
        print("ERROR: emuseum_key.txt was not found.")
        print(f"Expected: {KEY_FILE}")
        raise SystemExit(1)

    key = KEY_FILE.read_text(
        encoding="utf-8"
    ).strip()

    if not key:
        print("ERROR: emuseum_key.txt is empty.")
        raise SystemExit(1)

    return key


SERVICE_KEY = read_service_key()


# ============================================================
# HTTP
# ============================================================

def request_bytes(url, timeout):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT}
    )

    with urllib.request.urlopen(
        req,
        timeout=timeout
    ) as response:
        return response.read()


# ============================================================
# API
# ============================================================

def make_list_url(keyword, page_no, num_rows):
    params = {
        "serviceKey": SERVICE_KEY,
        "numOfRows": num_rows,
        "pageNo": page_no,
        "nameKr": keyword,
    }

    return (
        BASE_URL
        + "?"
        + urllib.parse.urlencode(params)
    )


def parse_data_element(data_element):
    record = {}

    for item in data_element.findall("item"):
        key = item.get("key")
        value = item.get("value", "")

        if key:
            record[key] = value

    return record


def fetch_page(keyword, page_no, num_rows=PAGE_SIZE):
    url = make_list_url(
        keyword,
        page_no,
        num_rows
    )

    xml_data = request_bytes(
        url,
        API_TIMEOUT
    )

    root = ET.fromstring(xml_data)

    result_code = root.findtext(
        "resultCode", ""
    )

    result_msg = root.findtext(
        "resultMsg", ""
    )

    if result_code != "0000":
        raise RuntimeError(
            f"eMuseum API error "
            f"{result_code}: {result_msg}"
        )

    try:
        total_count = int(
            root.findtext(
                "totalCount", "0"
            )
        )
    except ValueError:
        total_count = 0

    records = []

    for data_element in root.findall("./list/data"):
        records.append(
            parse_data_element(data_element)
        )

    return total_count, records


# ============================================================
# Candidate collection
# ============================================================

def collect_candidates(keyword):
    print()
    print("Checking collection size...")

    total_count, first_page = fetch_page(
        keyword,
        1
    )

    print(f"Matching records: {total_count:,}")

    if total_count == 0:
        return 0, []

    total_pages = (
        total_count + PAGE_SIZE - 1
    ) // PAGE_SIZE

    pages_needed = max(
        1,
        (CANDIDATE_POOL + PAGE_SIZE - 1)
        // PAGE_SIZE
    )

    if total_pages <= pages_needed:
        page_numbers = list(
            range(1, total_pages + 1)
        )
    else:
        page_numbers = [1]

        remaining = list(
            range(2, total_pages + 1)
        )

        random.shuffle(remaining)

        page_numbers.extend(
            remaining[:pages_needed - 1]
        )

    candidates = []

    print()
    print(
        "Collecting candidates from "
        f"{len(page_numbers)} page(s)..."
    )

    for n, page_no in enumerate(
        page_numbers,
        start=1
    ):
        print(
            f"\rPage {n}/{len(page_numbers)} "
            f"(API page {page_no})",
            end="",
            flush=True
        )

        try:
            if page_no == 1:
                records = first_page
            else:
                _, records = fetch_page(
                    keyword,
                    page_no
                )

        except Exception as e:
            print()
            print(
                f"Warning: API page "
                f"{page_no} failed: {e}"
            )
            continue

        for record in records:
            if not record.get("id"):
                continue

            if not record.get("imgUri"):
                continue

            candidates.append(record)

            if len(candidates) >= CANDIDATE_POOL:
                break

        if len(candidates) >= CANDIDATE_POOL:
            break

        time.sleep(API_DELAY)

    print()

    # Remove duplicate IDs

    unique = {}

    for record in candidates:
        object_id = record.get("id")

        if object_id:
            unique[object_id] = record

    candidates = list(unique.values())

    random.shuffle(candidates)

    print(
        f"Image candidates: "
        f"{len(candidates):,}"
    )

    return total_count, candidates


# ============================================================
# Collection management
# ============================================================

def count_existing_images():
    if not ORIGINAL.exists():
        return 0

    return len(
        list(ORIGINAL.glob("emuseum_*.jpg"))
    )


def clear_collection():
    print()
    print("Clearing current original/ collection...")

    if ORIGINAL.exists():
        for item in ORIGINAL.iterdir():
            try:
                if item.is_file() or item.is_symlink():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                print(
                    f"WARNING: could not remove "
                    f"{item.name}: {e}"
                )

    ORIGINAL.mkdir(
        parents=True,
        exist_ok=True
    )

    if META.exists():
        try:
            META.unlink()
        except OSError as e:
            print(
                "WARNING: could not remove "
                f"{META.name}: {e}"
            )

    print("Current collection cleared.")


# ============================================================
# Metadata
# ============================================================

def make_metadata(record, filename):
    return {
        "source": "eMuseum",
        "id": record.get("id", ""),

        "title": (
            record.get("nameKr")
            or record.get("name")
            or ""
        ),

        "titleOriginal":
            record.get("name", ""),

        "titleChinese":
            record.get("nameCn", ""),

        "museum":
            record.get("museumName2", ""),

        "museumSection":
            record.get("museumName3", ""),

        "museumCode":
            record.get("museumCode", ""),

        "author":
            record.get("author", ""),

        "nationalityCode":
            record.get(
                "nationalityCode", ""
            ),

        "materialCode":
            record.get(
                "materialCode", ""
            ),

        "purposeCode":
            record.get(
                "purposeCode", ""
            ),

        "sizeRangeCode":
            record.get(
                "sizeRangeCode", ""
            ),

        "indexWord":
            record.get("indexWord", ""),

        "imageURL":
            record.get("imgUri", ""),

        "thumbnailURL":
            record.get(
                "imgThumUriL", ""
            ),

        "filename": filename
    }


def load_metadata():
    if not META.exists():
        return []

    try:
        data = json.loads(
            META.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, list):
            return data

    except Exception:
        pass

    return []


def save_metadata(metadata_by_id):
    META.write_text(
        json.dumps(
            list(metadata_by_id.values()),
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


# ============================================================
# Image download
# ============================================================

def filename_for(record):
    return (
        "emuseum_"
        + record.get("id", "")
        + ".jpg"
    )


def download_image(record):
    image_url = record.get("imgUri", "")

    if not image_url:
        return None

    filename = filename_for(record)
    output_file = ORIGINAL / filename

    # Existing valid file: reuse it

    if output_file.exists():
        size = output_file.stat().st_size

        if size >= 10_000:
            return {
                "filename": filename,
                "bytes": size,
                "existing": True
            }

        try:
            output_file.unlink()
        except OSError:
            pass

    for attempt in range(
        1,
        IMAGE_RETRIES + 1
    ):
        try:
            image_data = request_bytes(
                image_url,
                IMAGE_TIMEOUT
            )

            if len(image_data) < 10_000:
                raise RuntimeError(
                    "response too small: "
                    f"{len(image_data)} bytes"
                )

            output_file.write_bytes(
                image_data
            )

            return {
                "filename": filename,
                "bytes": len(image_data),
                "existing": False
            }

        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            socket.timeout,
            TimeoutError,
            RuntimeError,
            OSError
        ) as e:
            print(
                f"      attempt "
                f"{attempt}/{IMAGE_RETRIES} "
                f"failed: {e}"
            )

            if attempt < IMAGE_RETRIES:
                time.sleep(1)

    return None


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 60)
    print("EO1-Museum eMuseum Gallery Downloader v1.2")
    print("=" * 60)

    existing_count = count_existing_images()

    print()
    print(
        f"Existing images in original/: "
        f"{existing_count}"
    )

    if existing_count > 0:
        print()
        print("[N] Start a NEW collection")
        print("[R] RESUME previous download")
        print()

        mode = input(
            "Select [N/R] (default N): "
        ).strip().lower()

        if mode == "r":
            resume = True
            print()
            print("Resume mode selected.")
        else:
            resume = False

            print()
            print(
                "WARNING: NEW mode will delete "
                "all files currently in:"
            )
            print(f"  {ORIGINAL}")
            print()

            confirm = input(
                "Continue? [y/N]: "
            ).strip().lower()

            if confirm != "y":
                print("Cancelled.")
                return

            clear_collection()

    else:
        resume = False

        ORIGINAL.mkdir(
            parents=True,
            exist_ok=True
        )

    print()

    keyword = input(
        "Search keyword(s): "
    ).strip()

    if not keyword:
        print("No search keyword entered.")
        return

    print()
    print(f"Search: {keyword}")

    try:
        total_count, candidates = (
            collect_candidates(keyword)
        )

    except Exception as e:
        print()
        print("API ERROR:")
        print(e)
        return

    if total_count == 0:
        print()
        print("No matching objects found.")
        return

    if not candidates:
        print()
        print(
            "No records with "
            "downloadable images found."
        )
        return

    # --------------------------------------------------------
    # Restore valid metadata in Resume mode
    # --------------------------------------------------------

    metadata_by_id = {}

    if resume:
        existing_metadata = load_metadata()

        for item in existing_metadata:
            object_id = item.get("id", "")
            filename = item.get("filename", "")

            if not object_id or not filename:
                continue

            path = ORIGINAL / filename

            if (
                path.exists()
                and path.stat().st_size >= 10_000
            ):
                metadata_by_id[object_id] = item

    success = len(metadata_by_id)

    print()
    print(f"Target              : {TARGET}")
    print(
        f"Already completed   : {success}"
    )
    print(
        f"Still needed        : "
        f"{max(0, TARGET - success)}"
    )
    print()

    if success >= TARGET:
        print("Collection is already complete.")
        return

    print("Downloading...")
    print()

    attempted = 0
    failed = 0

    for record in candidates:
        if success >= TARGET:
            break

        object_id = record.get("id", "")

        if not object_id:
            continue

        if object_id in metadata_by_id:
            continue

        attempted += 1

        title = (
            record.get("nameKr")
            or record.get("name")
            or "(untitled)"
        )

        museum = record.get(
            "museumName2",
            "Unknown museum"
        )

        print(
            f"[{success + 1:3}/{TARGET}] "
            f"{title} — {museum}"
        )

        result = download_image(record)

        if result is None:
            failed += 1
            print("      skipped")
            continue

        success += 1

        metadata_by_id[object_id] = (
            make_metadata(
                record,
                result["filename"]
            )
        )

        if result["existing"]:
            print(
                "      existing file reused"
            )
        else:
            print(
                f"      {result['filename']} "
                f"({result['bytes'] / 1024:.0f} KB)"
            )

        # Save immediately after every success

        save_metadata(metadata_by_id)

        time.sleep(DOWNLOAD_DELAY)

    # Final save

    save_metadata(metadata_by_id)

    print()
    print("=" * 60)
    print("Finished")
    print("=" * 60)

    print(
        f"Search matches : {total_count:,}"
    )

    print(
        f"Candidates     : {len(candidates):,}"
    )

    print(
        f"Attempted      : {attempted:,}"
    )

    print(
        f"Failed/skipped : {failed:,}"
    )

    print(
        f"Collection     : {success}/{TARGET}"
    )

    print(
        f"Images         : {ORIGINAL}"
    )

    print(
        f"Metadata       : {META}"
    )

    if success >= TARGET:
        print()
        print("Target collection complete.")

    else:
        print()
        print(
            "Target was not reached."
        )
        print(
            "Run again and select "
            "RESUME to continue."
        )


if __name__ == "__main__":
    main()
