"""Serve the real static bundle and verify assets/download bytes over loopback HTTP."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.request import urlopen

from scripts import check_release as r
from scripts import pipeline as p


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def check(root: Path) -> dict:
    source = p.read_json(root / "dist/data/current.json")
    derived = p.read_json(root / "dist/analysis/current.json")
    files = {"index.html": None, "case-study.html": None, "app.mjs": None, "model.mjs": None, "investigation.mjs": None, "style.css": None, "favicon.svg": None,
             "data/current.json": None, "analysis/current.json": None, "publication.json": None,
             "title-audit.json": p.read_json(root / "dist/publication.json")["title_audit_sha256"]}
    for folder, pointer, is_analysis in (("data", source, False), ("analysis", derived, True)):
        for name, relative in r.pointer_files(pointer, is_analysis).items():
            files[f"{folder}/{relative}"] = pointer["files_sha256"][name]
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(root / "dist")))
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.05), daemon=True)
    thread.start()
    checks = []
    try:
        for relative, expected_hash in files.items():
            with urlopen(f"http://127.0.0.1:{server.server_port}/{relative}", timeout=5) as response:
                body = response.read()
                if response.status != 200 or (expected_hash and p.digest(body) != expected_hash):
                    raise p.PipelineError(f"HTTP asset/hash failure: {relative}")
                checks.append({"path": relative, "status": response.status, "bytes": len(body), "mime": response.headers.get_content_type(), "hash_verified": expected_hash is not None})
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)
    return {"status": "passed", "requests": len(checks), "files": checks, "external_requests": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=p.ROOT)
    args = parser.parse_args()
    print(json.dumps(check(args.root.resolve()), indent=2))


if __name__ == "__main__":
    main()
