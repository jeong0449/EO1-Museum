#!/usr/bin/env python3
"""
EO1-Museum Initial Setup Server

A minimal HTTP server for transferring installation files such as
Firefox and ADBApprovalHelper.apk to the EO1 during initial setup.

Usage:
    python setup_server.py

Optional:
    python setup_server.py --host 0.0.0.0 --port 8000
"""

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import argparse
import os

ROOT = Path(__file__).resolve().parent

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000


class SetupHandler(SimpleHTTPRequestHandler):
    # Android 4.4.2 needs APK files served with the proper MIME type.
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".apk": "application/vnd.android.package-archive",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Serve EO1-Museum initial setup files."
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Bind address (default: {DEFAULT_HOST}).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"HTTP port (default: {DEFAULT_PORT}).",
    )
    args = parser.parse_args()

    os.chdir(ROOT)
    httpd = ThreadingHTTPServer((args.host, args.port), SetupHandler)

    print()
    print("=" * 60)
    print("EO1-Museum Initial Setup Server")
    print("=" * 60)
    print(f"Root    : {ROOT}")
    print(f"Address : http://{args.host}:{args.port}/")
    print()
    print("Use the EO1 browser to download setup files, for example:")
    print(f"  http://<PC-IP>:{args.port}/firefox.apk")
    print(f"  http://<PC-IP>:{args.port}/ADBApprovalHelper.apk")
    print()
    print("Press Ctrl+C to stop.")
    print("=" * 60)
    print()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping EO1-Museum setup server...")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
