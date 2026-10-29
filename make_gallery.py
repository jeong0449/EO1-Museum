from pathlib import Path
import sys

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
# ============================================================

ROOT = Path(__file__).resolve().parent

SRC = ROOT / "original"
DST = ROOT / "display"

W, H = 1080, 1920
QUALITY = 90
SERVER_ID = "EO1M-8F29C74A"

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
print(f"Source : {SRC}")
print(f"Images : {len(files)}")
print(f"Output : {DST}")
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

for n, src in enumerate(files, 1):

    outname = f"{n:04d}.jpg"
    out = DST / outname

    try:

        with Image.open(src) as im:

            # Correct orientation using EXIF metadata
            im = ImageOps.exif_transpose(im)

            # Convert to RGB for JPEG output
            im = im.convert("RGB")

            # Preserve aspect ratio and fit inside
            # the EO1's 1080 x 1920 portrait display.
            im.thumbnail(
                (W, H),
                Image.LANCZOS
            )

            # Black 1080 x 1920 canvas
            canvas = Image.new(
                "RGB",
                (W, H),
                (0, 0, 0)
            )

            # Center image
            x = (W - im.width) // 2
            y = (H - im.height) // 2

            canvas.paste(
                im,
                (x, y)
            )

            # Save optimized JPEG
            canvas.save(
                out,
                "JPEG",
                quality=QUALITY,
                optimize=True
            )

        made.append(
            "display/" + outname
        )

        print(
            f"[{n:3}/{len(files)}] "
            f"{src.name} -> {outname}"
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
    "var images = [\n"
    + "".join(
        f'  "{s.replace(chr(92), "/")}",\n'
        for s in made
    )
    + "];\n"
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