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
            # Optional pan image
            # ------------------------------------------------

            pan_path = None

            if ratio > PAN_THRESHOLD:

                # Resize the original so that its height is
                # exactly the EO1 screen height (1920 px).
                #
                # Example:
                #
                #   1400 x 1050
                #        ↓
                #   2560 x 1920
                #
                # The resulting image is wider than the
                # 1080-pixel EO1 viewport and can therefore
                # be moved horizontally by index.html.

                pan_width = round(
                    source_w * PAN_HEIGHT / source_h
                )

                pan_im = source.resize(
                    (pan_width, PAN_HEIGHT),
                    Image.LANCZOS
                )

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

        made.append(
            {
                "display": (
                    "display/" + outname
                ),
                "pan": pan_path
            }
        )


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


if len(made) != len(files):

    print()

    print(
        f"Skipped       : "
        f"{len(files) - len(made)}"
    )


print()