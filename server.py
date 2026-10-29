#!/usr/bin/env python3
"""
EO1-Museum PC Gallery Server

Normal gallery server:
    python server.py

Allow EO1 Safe Sync for this server session:
    python server.py --sync

Optional:
    python server.py --sync --port 8000
    python server.py --host 0.0.0.0 --port 8000

Control endpoint:
    GET /eo1-status

Example response:
    EO1M-8F29C74A
    SYNC=1

The server ID must match TRUSTED_SERVER in the EO1 .config file.
"""

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import argparse
import os

ROOT = Path(__file__).resolve().parent

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
DEFAULT_SERVER_ID = "EO1M-8F29C74A"


class EO1Handler(SimpleHTTPRequestHandler):
    sync_enabled = False
    server_id = DEFAULT_SERVER_ID

    def do_GET(self):
        # Small control endpoint used by the EO1 Android app.
        if self.path.split("?", 1)[0].rstrip("/") == "/eo1-status":
            body = (
                f"{self.server_id}\n"
                f"SYNC={1 if self.sync_enabled else 0}\n"
            ).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return

        # Everything else is served normally from the EO1-Museum directory:
        # index.html, images.js, display/*.jpg, etc.
        super().do_GET()

    def end_headers(self):
        # Avoid stale gallery/control data while developing.
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(
        description="Serve the EO1-Museum PC Gallery."
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Allow the EO1 app to perform Safe Sync during this server session.",
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
    parser.add_argument(
        "--server-id",
        default=DEFAULT_SERVER_ID,
        help=(
            "Server identity returned by /eo1-status. "
            "Must match TRUSTED_SERVER in EO1 .config."
        ),
    )
    args = parser.parse_args()

    os.chdir(ROOT)

    EO1Handler.sync_enabled = args.sync
    EO1Handler.server_id = args.server_id

    httpd = ThreadingHTTPServer((args.host, args.port), EO1Handler)

    print()
    print("=" * 60)
    print("EO1-Museum PC Gallery Server")
    print("=" * 60)
    print(f"Root      : {ROOT}")
    print(f"Address   : http://{args.host}:{args.port}/")
    print(f"Server ID : {args.server_id}")
    print(f"Safe Sync : {'ENABLED' if args.sync else 'disabled'}")
    print()
    print("EO1 control endpoint:")
    print(f"  http://<PC-IP>:{args.port}/eo1-status")
    print()
    if args.sync:
        print("EO1 may sync when Network Gallery is opened.")
    else:
        print("Gallery only. EO1 Safe Sync is not requested.")
    print()
    print("Press Ctrl+C to stop.")
    print("=" * 60)
    print()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping EO1-Museum server...")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
