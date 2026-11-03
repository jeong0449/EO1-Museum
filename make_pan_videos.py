#!/usr/bin/env python3
"""
EO1-Museum Pan Video Generator

Scans display/ for pan_*.jpg files and creates matching
pan_*.mp4 files when the image aspect ratio meets the threshold.

Default:
    threshold = 1.3
    duration  = 20 seconds
    fps       = 30
    codec     = H.264 / libx264
    preset    = veryfast
    CRF       = 20
    output    = 1080 x 1920
    upscale   = never

Examples:

    python make_pan_videos.py

    python make_pan_videos.py --threshold 1.5

    python make_pan_videos.py --force

    python make_pan_videos.py --directory display
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


# ============================================================
# Settings
# ============================================================

SCREEN_W = 1080
SCREEN_H = 1920

DEFAULT_THRESHOLD = 1.3

DURATION = 20
FPS = 30

CRF = 20
PRESET = "veryfast"


# ============================================================
# Helpers
# ============================================================

def require_program(name):

    if shutil.which(name) is None:

        print(
            f"ERROR: '{name}' was not found in PATH."
        )

        sys.exit(1)


def get_image_size(path):

    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        str(path),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(
        result.stdout
    )

    stream = data["streams"][0]

    return (
        int(stream["width"]),
        int(stream["height"]),
    )


def make_even(value):

    value = int(
        round(value)
    )

    if value % 2:
        value -= 1

    return value


def format_size(num_bytes):

    return (
        f"{num_bytes / (1024 * 1024):.2f} MB"
    )


# ============================================================
# Video encoder
# ============================================================

def encode_video(
    input_path,
    output_path,
    source_w,
    source_h,
):

    # --------------------------------------------------------
    # Never upscale.
    #
    # If taller than EO1 screen:
    #     downscale to height 1920.
    #
    # Otherwise:
    #     preserve original resolution.
    # --------------------------------------------------------

    if source_h > SCREEN_H:

        scale = (
            SCREEN_H /
            source_h
        )

    else:

        scale = 1.0


    pan_w = make_even(
        source_w * scale
    )

    pan_h = make_even(
        source_h * scale
    )


    # --------------------------------------------------------
    # Horizontal travel
    # --------------------------------------------------------

    travel = (
        pan_w -
        SCREEN_W
    )

    if travel <= 0:

        return None


    # --------------------------------------------------------
    # Vertical centering
    # --------------------------------------------------------

    top = max(
        0,
        (
            SCREEN_H -
            pan_h
        ) // 2
    )


    # --------------------------------------------------------
    # Pan geometry
    # --------------------------------------------------------

    total_frames = (
        DURATION *
        FPS
    )

    x_expression = (
        f"-{travel}*n/"
        f"{total_frames - 1}"
    )


    # --------------------------------------------------------
    # FFmpeg filter
    #
    # Artwork moves from:
    #
    #     x = 0
    #
    # to:
    #
    #     x = -travel
    #
    # over the complete video.
    # --------------------------------------------------------

    filter_complex = (

        f"[0:v]"
        f"scale={pan_w}:{pan_h},"
        f"format=rgba"
        f"[art];"

        f"color=c=black:"
        f"s={SCREEN_W}x{SCREEN_H}:"
        f"r={FPS}:"
        f"d={DURATION}"
        f"[bg];"

        f"[bg][art]"
        f"overlay="
        f"x='{x_expression}':"
        f"y={top}:"
        f"shortest=1"
        f"[out]"
    )


    # --------------------------------------------------------
    # FFmpeg command
    # --------------------------------------------------------

    cmd = [

        "ffmpeg",

        "-y",

        "-hide_banner",

        "-loglevel",
        "warning",

        "-loop",
        "1",

        "-framerate",
        str(FPS),

        "-i",
        str(input_path),

        "-filter_complex",
        filter_complex,

        "-map",
        "[out]",

        "-t",
        str(DURATION),

        "-r",
        str(FPS),

        "-c:v",
        "libx264",

        "-preset",
        PRESET,

        "-crf",
        str(CRF),

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        str(output_path),
    ]


    # --------------------------------------------------------
    # Encode
    # --------------------------------------------------------

    start_time = (
        time.perf_counter()
    )

    subprocess.run(
        cmd,
        check=True,
    )

    elapsed = (
        time.perf_counter() -
        start_time
    )


    return {

        "pan_w": pan_w,

        "pan_h": pan_h,

        "travel": travel,

        "top": top,

        "elapsed": elapsed,

        "size":
            output_path.stat().st_size,
    }


# ============================================================
# Main
# ============================================================

def main():

    parser = argparse.ArgumentParser(

        description=(
            "Create EO1-Museum pan MP4 files "
            "from pan_*.jpg images."
        )
    )


    parser.add_argument(

        "--directory",
        "-d",

        default="display",

        help=(
            "Directory containing pan_*.jpg "
            "(default: display)"
        ),
    )


    parser.add_argument(

        "--threshold",

        type=float,

        default=DEFAULT_THRESHOLD,

        help=(
            "Minimum aspect ratio for MP4 generation "
            f"(default: {DEFAULT_THRESHOLD})"
        ),
    )


    parser.add_argument(

        "--force",

        action="store_true",

        help=(
            "Recreate MP4 files even when "
            "they already exist"
        ),
    )


    args = parser.parse_args()


    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if args.threshold <= 1.0:

        print(
            "ERROR: --threshold must be greater than 1.0."
        )

        sys.exit(1)


    require_program(
        "ffmpeg"
    )

    require_program(
        "ffprobe"
    )


    directory = Path(
        args.directory
    )


    if not directory.is_dir():

        print(
            f"ERROR: Directory not found: "
            f"{directory}"
        )

        sys.exit(1)


    # --------------------------------------------------------
    # Find pan images
    # --------------------------------------------------------

    images = sorted(
        directory.glob(
            "pan_*.jpg"
        )
    )


    print()

    print(
        "EO1-Museum Pan Video Generator"
    )

    print(
        "=" * 55
    )

    print(
        f"Directory : {directory}"
    )

    print(
        f"Threshold : {args.threshold:.3f}"
    )

    print(
        f"Video     : "
        f"{SCREEN_W}x{SCREEN_H}, "
        f"{DURATION}s, "
        f"{FPS} fps"
    )

    print(
        f"Encoder   : "
        f"libx264 / "
        f"{PRESET} / "
        f"CRF {CRF}"
    )

    print(
        f"Found     : "
        f"{len(images)} pan image(s)"
    )

    print()


    if not images:

        return


    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    created = 0

    skipped_ratio = 0

    skipped_existing = 0

    failed = 0

    total_encode_time = 0.0


    # --------------------------------------------------------
    # Process
    # --------------------------------------------------------

    for index, image_path in enumerate(
        images,
        1,
    ):

        output_path = (
            image_path.with_suffix(
                ".mp4"
            )
        )


        # ----------------------------------------------------
        # Read dimensions
        # ----------------------------------------------------

        try:

            source_w, source_h = (
                get_image_size(
                    image_path
                )
            )

        except Exception as exc:

            failed += 1

            print(
                f"[{index:3}/{len(images)}] "
                f"ERROR "
                f"{image_path.name}: "
                f"{exc}"
            )

            continue


        ratio = (
            source_w /
            source_h
        )


        # ----------------------------------------------------
        # Threshold
        # ----------------------------------------------------

        if ratio < args.threshold:

            skipped_ratio += 1

            print(
                f"[{index:3}/{len(images)}] "
                f"SKIP  "
                f"{image_path.name} "
                f"ratio={ratio:.3f} "
                f"< {args.threshold:.3f}"
            )

            continue


        # ----------------------------------------------------
        # Existing MP4
        # ----------------------------------------------------

        if (
            output_path.exists()
            and
            not args.force
        ):

            skipped_existing += 1

            print(
                f"[{index:3}/{len(images)}] "
                f"SKIP  "
                f"{output_path.name} "
                f"already exists"
            )

            continue


        # ----------------------------------------------------
        # Encode
        # ----------------------------------------------------

        print(
            f"[{index:3}/{len(images)}] "
            f"MAKE  "
            f"{image_path.name} "
            f"({source_w}x{source_h}, "
            f"ratio={ratio:.3f})"
        )


        try:

            result = encode_video(

                image_path,

                output_path,

                source_w,

                source_h,
            )

        except subprocess.CalledProcessError:

            failed += 1

            print(
                "              "
                "ERROR: ffmpeg failed"
            )

            try:

                output_path.unlink(
                    missing_ok=True
                )

            except Exception:

                pass

            continue


        if result is None:

            failed += 1

            print(
                "              "
                "ERROR: no horizontal travel "
                "after scaling"
            )

            continue


        # ----------------------------------------------------
        # Success
        # ----------------------------------------------------

        created += 1

        total_encode_time += (
            result["elapsed"]
        )


        print(

            f"              "
            f"OK    "
            f"{output_path.name} | "

            f"{result['elapsed']:.1f}s | "

            f"{format_size(result['size'])} | "

            f"travel="
            f"{result['travel']}px"
        )


    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()

    print(
        "=" * 55
    )

    print(
        "SUMMARY"
    )

    print(
        "=" * 55
    )

    print(
        f"Created          : "
        f"{created}"
    )

    print(
        f"Skipped (ratio)  : "
        f"{skipped_ratio}"
    )

    print(
        f"Skipped (exists) : "
        f"{skipped_existing}"
    )

    print(
        f"Failed           : "
        f"{failed}"
    )


    if created:

        print(
            f"Encode time      : "
            f"{total_encode_time / 60:.1f} min"
        )

        print(
            f"Average/video    : "
            f"{total_encode_time / created:.1f} s"
        )


    print()


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":

    main()