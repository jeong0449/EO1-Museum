from pathlib import Path
import sys
import json

try:
    from PIL import Image, ImageOps
except ImportError:
    print()
    print("Pillow is not installed.")
    print("Run:  python -m pip install pillow")
    input("Press Enter to close...")
    sys.exit(1)


# ============================================================
# EO1-Museum
# Gallery Builder
#
# Builds the EO1 display collection from every supported
# image found in original/.
#
# Source-independent:
#   The Met
#   eMuseum
#   Cleveland Museum of Art
#   personal images
#   etc.
#
# Wide landscape images can also receive a pre-rendered
# horizontal-pan image for Network Gallery.
# ============================================================

ROOT = Path(__file__).resolve().parent

SRC = ROOT / "original"
DST = ROOT / "display"

W, H = 1080, 1920
QUALITY = 90
SERVER_ID = "EO1M-8F29C74A"

# Wide-artwork pan settings
PAN_THRESHOLD = 1.2
PAN_HEIGHT = H
PAN_QUALITY = 90

EXTS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}


# ============================================================
# Prepare directories
# ============================================================

SRC.mkdir(exist_ok=True)
DST.mkdir(exist_ok=True)


# ============================================================
# Find all source images
# ============================================================

# Optional Met metadata. Matching is by the ORIGINAL filename, never
# by the index of a sorted list. Other sources remain fully supported.
metadata_by_file = {}
metadata_path = ROOT / "met_metadata.json"
if metadata_path.is_file():
    try:
        for entry in json.loads(metadata_path.read_text(encoding="utf-8")):
            if isinstance(entry, dict) and entry.get("file"):
                metadata_by_file[Path(entry["file"]).name] = entry
    except (ValueError, OSError) as exc:
        print(f"WARNING: cannot load Met metadata: {exc}")

files = sorted(
    p for p in SRC.iterdir()
    if p.is_file()
    and p.suffix.lower() in EXTS
)


if not files:
    print()
    print("No images found in:")
    print(f"  {SRC}")
    print()
    input("Press Enter to close...")
    sys.exit(0)


print()
print("=" * 60)
print("EO1-Museum Gallery Builder")
print("=" * 60)

print()
print(f"Source        : {SRC}")
print(f"Images        : {len(files)}")
print(f"Output        : {DST}")
print(f"Pan threshold : > {PAN_THRESHOLD}")
print()


# ============================================================
# Clear old display collection
# ============================================================

print("Clearing old display collection...")

for p in DST.iterdir():

    if p.is_file():

        try:
            p.unlink()

        except Exception as e:

            print(
                f"WARNING: could not remove "
                f"{p.name}: {e}"
            )


# ============================================================
# Build display images
# ============================================================

print()
print("Building gallery...")
print()

made = []
pan_count = 0


for n, src in enumerate(files, 1):

    outname = f"{n:04d}.jpg"
    out = DST / outname

    pan_outname = f"pan_{outname}"
    pan_out = DST / pan_outname

    try:

        with Image.open(src) as source:

            # Correct orientation using EXIF metadata.
            source = ImageOps.exif_transpose(source)

            # Convert to RGB for JPEG output.
            source = source.convert("RGB")

            # IMPORTANT:
            # Determine the aspect ratio BEFORE creating the
            # normal 1080 x 1920 display image.
            source_w, source_h = source.size
            ratio = source_w / source_h


            # ------------------------------------------------
            # Normal EO1 display image
            # ------------------------------------------------

            # Work on a copy because the source image may also
            # be needed for generation of the pan image.
            im = source.copy()

            # Preserve aspect ratio and fit inside
            # the EO1's 1080 x 1920 portrait display.
            im.thumbnail(
                (W, H),
                Image.LANCZOS
            )

            # Black 1080 x 1920 canvas.
            canvas = Image.new(
                "RGB",
                (W, H),
                (0, 0, 0)
            )

            # Center image.
            x = (W - im.width) // 2
            y = (H - im.height) // 2

            canvas.paste(
                im,
                (x, y)
            )

            # Save optimized JPEG.
            canvas.save(
                out,
                "JPEG",
                quality=QUALITY,
                optimize=True
            )


            # ------------------------------------------------
            # Optional pan/detail image
            # ------------------------------------------------

            pan_path = None

            if ratio > PAN_THRESHOLD:

                # Create the wide detail image without upscaling.
                #
                # PAN_HEIGHT is a maximum height, not a target.
                #
                # Source height > 1920:
                #     reduce to 1920 px
                #
                # Source height <= 1920:
                #     keep original dimensions

                pan_height = min(
                    source_h,
                    PAN_HEIGHT
                )

                pan_width = round(
                    source_w *
                    pan_height /
                    source_h
                )

                if pan_height < source_h:

                    pan_im = source.resize(
                        (
                            pan_width,
                            pan_height
                        ),
                        Image.LANCZOS
                    )

                else:

                    pan_im = source.copy()


                pan_im.save(
                    pan_out,
                    "JPEG",
                    quality=PAN_QUALITY,
                    optimize=True
                )

                pan_path = (
                    "display/" + pan_outname
                )

                pan_count += 1
        # Store Network Gallery metadata.
        #
        # Normal image:
        #
        # {
        #   "display": "display/0001.jpg",
        #   "pan": null
        # }
        #
        # Wide image:
        #
        # {
        #   "display": "display/0002.jpg",
        #   "pan": "display/pan_0002.jpg"
        # }

        item = {
            "display": "display/" + outname,
            "pan": pan_path,
        }
        source_metadata = metadata_by_file.get(src.name)
        if source_metadata:
            for source_key, dest_key in (
                ("title", "title"),
                ("artist", "artist"),
                ("date", "date"),
                ("medium", "medium"),
            ):
                if source_metadata.get(source_key):
                    item[dest_key] = str(source_metadata[source_key])
            item["institution"] = "The Metropolitan Museum of Art"
        made.append(item)


        if pan_path:

            print(
                f"[{n:3}/{len(files)}] "
                f"{src.name} -> "
                f"{outname} + {pan_outname} "
                f"(ratio {ratio:.2f})"
            )

        else:

            print(
                f"[{n:3}/{len(files)}] "
                f"{src.name} -> {outname} "
                f"(ratio {ratio:.2f})"
            )


    except Exception as e:

        print(
            f"[{n:3}/{len(files)}] "
            f"SKIP {src.name}: {e}"
        )


# ============================================================
# Write images.js for Network Gallery
# ============================================================

js = (
    f"// server-id: {SERVER_ID}\n"
    "var images = "
    + json.dumps(
        made,
        ensure_ascii=False,
        indent=2
    )
    + ";\n"
)

(ROOT / "images.js").write_text(
    js,
    encoding="utf-8"
)

# ============================================================
# Write artwork_info.json for EO1 Internal Gallery / Safe Sync
# ============================================================
# Use the exact same records and ordering as images.js.
# This is a JSON array, as expected by MainActivity.java.
manifest_path = ROOT / "artwork_info.json"
manifest_path.write_text(
    json.dumps(made, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8"
)


# ============================================================
# Summary
# ============================================================

print()
print("=" * 60)
print("Gallery complete")
print("=" * 60)

print()

print(
    f"Source images : {len(files)}"
)

print(
    f"Created       : {len(made)}"
)

print(
    f"Pan images    : {pan_count}"
)

print(
    f"Pan threshold : > {PAN_THRESHOLD}"
)

print(
    f"Resolution    : {W} x {H}"
)

print(
    f"Display       : {DST}"
)

print(
    f"Gallery list  : "
    f"{ROOT / 'images.js'}"
)

print(f"Artwork info   : {manifest_path}")


if len(made) != len(files):

    print()

    print(
        f"Skipped       : "
        f"{len(files) - len(made)}"
    )


print()