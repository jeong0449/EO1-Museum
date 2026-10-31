#!/usr/bin/env python3
"""
render_art.py

EO1 HTML/JavaScript artwork -> EO1-friendly MP4.

Pipeline:
    HTML/JS
      -> headless Chromium (1080x1920)
      -> Chromium CDP screen recording (temporary WebM)
      -> FFmpeg
      -> H.264 / yuv420p MP4
      -> delete temporary WebM

No physical monitor capture, OBS, browser window, crop, or per-frame screenshots.

Requirements:
    pip install playwright
    playwright install chromium
    ffmpeg -version

Example:
    python render_art.py "EO1_Space_Jellyfish(2).html" -o jellyfish.mp4 -d 60
"""

import argparse
import asyncio
import base64
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlencode

from playwright.async_api import async_playwright

__version__ = "1.1.0"

W, H = 1080, 1920


async def read_cdp_stream(cdp, handle: str, output: Path) -> int:
    total = 0
    with output.open("wb") as f:
        while True:
            result = await cdp.send("IO.read", {"handle": handle})
            data = result.get("data", "")
            if data:
                if result.get("base64Encoded"):
                    chunk = base64.b64decode(data)
                else:
                    chunk = data.encode("latin1")
                f.write(chunk)
                total += len(chunk)

            if result.get("eof"):
                break

    try:
        await cdp.send("IO.close", {"handle": handle})
    except Exception:
        pass

    return total



def build_artwork_url(html_file: Path, preview: bool) -> str:
    url = html_file.as_uri()
    if preview:
        url += "?" + urlencode({"preview": "1"})
    return url


def parse_set_values(items):
    values = {}
    for item in items or []:
        if "=" not in item:
            raise ValueError(
                f'Invalid --set value "{item}". Use id=value, for example balls=12.'
            )
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f'Invalid --set value "{item}": empty element id.')
        values[key] = value
    return values


async def apply_controls(page, values):
    """Set form controls by element id, then dispatch input/change events."""
    if not values:
        return

    results = await page.evaluate(
        """values => {
            const out = [];
            for (const [id, raw] of Object.entries(values)) {
                const el = document.getElementById(id);
                if (!el) {
                    out.push({id, ok:false, reason:"element not found"});
                    continue;
                }

                if (el.type === "checkbox" || el.type === "radio") {
                    const v = String(raw).trim().toLowerCase();
                    el.checked = ["1","true","yes","on","checked"].includes(v);
                } else {
                    el.value = String(raw);
                }

                el.dispatchEvent(new Event("input",  {bubbles:true}));
                el.dispatchEvent(new Event("change", {bubbles:true}));

                out.push({
                    id,
                    ok:true,
                    value: (el.type === "checkbox" || el.type === "radio")
                        ? el.checked
                        : el.value
                });
            }
            return out;
        }""",
        values,
    )

    failed = [r for r in results if not r["ok"]]
    if failed:
        details = ", ".join(f'{r["id"]}: {r["reason"]}' for r in failed)
        raise RuntimeError(f"--set failed: {details}")

    print("Applied controls:")
    for r in results:
        print(f'  {r["id"]}={r["value"]}')


async def record_webm(html_file: Path, webm_file: Path,
                      duration: float, fps: int, preview: bool,
                      control_values: dict) -> tuple[float, int]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
            ],
        )

        page = await browser.new_page(
            viewport={"width": W, "height": H},
            device_scale_factor=1,
        )

        artwork_url = build_artwork_url(html_file, preview)
        print(f"Artwork URL: {artwork_url}")
        await page.goto(artwork_url, wait_until="load")
        await page.wait_for_selector("canvas")

        # Apply requested interactive-control values before recording begins.
        await apply_controls(page, control_values)

        # Give the artwork one brief turn to react/reinitialize after events.
        if control_values:
            await page.wait_for_timeout(100)

        canvas = page.locator("canvas").first
        box = await canvas.bounding_box()
        if not box:
            await browser.close()
            raise RuntimeError("Canvas is not visible.")

        print(
            f"Canvas CSS size: {box['width']:.0f} x {box['height']:.0f} "
            f"(target {W} x {H})"
        )

        cdp = await page.context.new_cdp_session(page)
        await cdp.send("Page.enable")

        print(f"Recording in Chromium: {duration:g} s at max {fps} fps ...")
        t0 = time.perf_counter()

        try:
            start_result = await cdp.send(
                "Page.startScreenRecording",
                {
                    "audio": False,
                    "maxWidth": W,
                    "maxHeight": H,
                    "frameRate": fps,
                },
            )
        except Exception as e:
            await browser.close()
            raise RuntimeError(
                "This Chromium build does not support Page.startScreenRecording().\n"
                f"CDP error: {e}"
            )

        start_handle = start_result.get("stream")

        # Real-time recording: the artwork runs with Chromium's normal clock.
        await page.wait_for_timeout(duration * 1000)

        stop_result = await cdp.send("Page.stopScreenRecording")
        recording_wall = time.perf_counter() - t0

        handle = stop_result.get("stream") or start_handle
        if not handle:
            await browser.close()
            raise RuntimeError("Chromium returned no recording stream handle.")

        print(f"Recording stopped after {recording_wall:.2f} s.")
        print("Saving temporary WebM stream ...")

        size = await read_cdp_stream(cdp, handle, webm_file)

        await browser.close()

    return recording_wall, size


def convert_to_mp4(webm_file: Path, output: Path,
                   preset: str, crf: int) -> float:
    print("Converting WebM -> H.264 MP4 ...")
    t0 = time.perf_counter()

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(webm_file),
        "-an",
        "-c:v", "libx264",
        "-preset", preset,
        "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output),
    ]

    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed with exit code {result.returncode}")

    return time.perf_counter() - t0


async def run(args):
    html_file = args.html.resolve()
    output = args.output.resolve()

    if not html_file.exists():
        raise FileNotFoundError(f"HTML file not found: {html_file}")

    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            'FFmpeg was not found in PATH. Confirm that "ffmpeg -version" works.'
        )

    output.parent.mkdir(parents=True, exist_ok=True)

    overall_start = time.perf_counter()

    # Temporary WebM is automatically removed when the block ends.
    with tempfile.TemporaryDirectory(prefix="eo1_render_") as td:
        webm_file = Path(td) / "chromium_recording.webm"

        recording_wall, webm_size = await record_webm(
            html_file, webm_file, args.duration, args.fps,
            args.preview, parse_set_values(args.set_values)
        )

        print(f"Temporary WebM: {webm_size / (1024 * 1024):.2f} MiB")

        encode_wall = convert_to_mp4(
            webm_file, output, args.preset, args.crf
        )

    total_wall = time.perf_counter() - overall_start

    print()
    print(f"Done: {output}")
    if output.exists():
        print(f"MP4 size: {output.stat().st_size / (1024 * 1024):.2f} MiB")
    print(f"Chromium recording: {recording_wall:.2f} s")
    print(f"MP4 conversion:     {encode_wall:.2f} s")
    print(f"Total wall time:    {total_wall:.2f} s")
    print(
        f"Overall ratio:      {total_wall / args.duration:.2f}x realtime"
    )


def main():
    ap = argparse.ArgumentParser(
        description="Render EO1-Museum HTML/JavaScript artwork to EO1-compatible 1080x1920 H.264 MP4."
    )
    ap.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    ap.add_argument("html", type=Path, help="Input HTML artwork")
    ap.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("eo1_art.mp4"),
        help="Output MP4 file"
    )
    ap.add_argument(
        "-d", "--duration",
        type=float,
        default=60.0,
        help="Recording duration in seconds (default: 60)"
    )
    ap.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Maximum recording frame rate (default: 30)"
    )
    ap.add_argument(
        "--preview",
        action="store_true",
        help="Open the artwork with ?preview=1 (useful for hiding control panels)"
    )
    ap.add_argument(
        "--set",
        dest="set_values",
        nargs="+",
        metavar="ID=VALUE",
        help=(
            "Set HTML controls by element id before recording. "
            "Example: --set balls=12 speed=80 size=15 trail=97. "
            "Checkbox values accept true/false, yes/no, on/off, or 1/0."
        )
    )
    ap.add_argument(
        "--preset",
        default="veryfast",
        help="x264 preset for final MP4 (default: veryfast)"
    )
    ap.add_argument(
        "--crf",
        type=int,
        default=18,
        help="H.264 CRF quality (default: 18)"
    )

    args = ap.parse_args()

    if args.duration <= 0:
        ap.error("--duration must be > 0")
    if args.fps <= 0:
        ap.error("--fps must be > 0")
    if not 0 <= args.crf <= 51:
        ap.error("--crf must be between 0 and 51")

    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
