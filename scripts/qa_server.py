"""Local-only browser QA server with explicit missing/tampered/stale fixtures.

Use / normally or /__qa__/{missing,tampered,stale}/ for failure scenarios.
Faults are applied to responses, never to project files. Not shipped in dist/.
"""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import urlsplit

from scripts import pipeline as p


def fault(scenario: str, path: str, payload: bytes) -> tuple[int, bytes]:
    if scenario == "missing" and path == "/data/current.json":
        return 503, b'{"error":"deliberate local QA outage"}'
    if scenario == "tampered" and path.endswith("/dataset.json"):
        return 200, payload + b"\n "
    if scenario == "stale" and path == "/analysis/current.json":
        value = json.loads(payload)
        value["source_snapshot_id"] = "0" * 64
        return 200, p.encoded(value)
    return 200, payload


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        original = self.path
        path = urlsplit(original).path
        scenario = "valid"
        if path.startswith("/__qa__/"):
            parts = path.split("/", 3)
            if len(parts) != 4 or parts[2] not in {"missing", "tampered", "stale"}:
                self.send_error(404)
                return
            scenario, path = parts[2], "/" + parts[3]
        self.path = path
        try:
            if scenario != "valid" and (path.endswith("/current.json") or path.endswith("/dataset.json")):
                actual = self.translate_path(path)
                try:
                    with open(actual, "rb") as stream:
                        status, body = fault(scenario, path, stream.read())
                except OSError:
                    self.send_error(404)
                    return
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            else:
                super().do_GET()
        finally:
            self.path = original


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=str(p.ROOT / "dist")))
    print(f"Local QA server: http://127.0.0.1:{args.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
