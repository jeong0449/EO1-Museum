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

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "original"
DST = ROOT / "display"

W, H = 1080, 1920
QUALITY = 90
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

SRC.mkdir(exist_ok=True)
DST.mkdir(exist_ok=True)

META = ROOT / "met_metadata.json"

# Build the display from only the most recent Met selection.
# original/ remains a cumulative collection/cache.
if not META.exists():
    print("Metadata file not found:", META)
    print("Run GET_MET_ART_KEYWORD.py first.")
    input("Press Enter to close...")
    sys.exit(1)

try:
    records = json.loads(META.read_text(encoding="utf-8"))
except Exception as e:
    print("Could not read metadata:", e)
    input("Press Enter to close...")
    sys.exit(1)

files = []
for rec in records:
    name = rec.get("file", "")
    if not name:
        continue
    p = SRC / name
    if p.is_file() and p.suffix.lower() in EXTS:
        files.append(p)

if not files:
    print("No selected images found from:", META)
    input("Run GET_MET_ART_KEYWORD.py first, then press Enter to close...")
    sys.exit(0)

print("Building gallery from the latest selection: %d image(s)" % len(files))

# Rebuild display folder so deleted originals don't linger.
for p in DST.iterdir():
    if p.is_file():
        try:
            p.unlink()
        except Exception:
            pass

made = []
for n, src in enumerate(files, 1):
    outname = "%04d.jpg" % n
    out = DST / outname
    try:
        im = Image.open(src)
        im = ImageOps.exif_transpose(im).convert("RGB")
        # Preserve aspect ratio and fit inside 1080x1920.
        im.thumbnail((W, H), Image.LANCZOS)

        canvas = Image.new("RGB", (W, H), (0, 0, 0))
        x = (W - im.width) // 2
        y = (H - im.height) // 2
        canvas.paste(im, (x, y))
        canvas.save(out, "JPEG", quality=QUALITY, optimize=True)
        made.append("display/" + outname)
        print("%s -> %s" % (src.name, outname))
    except Exception as e:
        print("SKIP %s: %s" % (src.name, e))

js = "var images = [\n" + "".join(
    '  "%s",\n' % s.replace("\\", "/") for s in made
) + "];\n"
(ROOT / "images.js").write_text(js, encoding="utf-8")

print()
print("Created %d EO1 images (1080x1920)." % len(made))
print("Gallery list written to images.js")
