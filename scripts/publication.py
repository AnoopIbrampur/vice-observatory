"""Publish only a fully validated candidate; preserve the last good data on failure."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile

from scripts import pipeline as p
from scripts import refresh_candidate as c
from scripts import title_audit


def record(root: Path, status: str, message: str = ""):
    path = root / "dist/publication.json"
    previous = p.read_json(path) if path.exists() else {"history": []}
    source = p.read_json(root / "data/current.json")
    analysis = p.read_json(root / "analysis/current.json")
    entry = dict(at=p.utc_now(), status=status, as_of=source["as_of"],
                 source_snapshot_id=source["snapshot_id"], analysis_id=analysis["analysis_id"],
                 run_url=os.environ.get("PUBLICATION_RUN_URL", ""), message=message)
    report = dict(schema_version=1, schedule="Daily at 12:23 UTC (GitHub may delay scheduled jobs)",
                  data_pointer=source, analysis_pointer=analysis,
                  title_audit_sha256=p.digest((root / "dist/title-audit.json").read_bytes()),
                  history=[entry, *previous["history"]][:30])
    p.atomic_write(path, p.encoded(report))
    return report


def refresh(root: Path, as_of):
    try:
        with tempfile.TemporaryDirectory(prefix="vice-publication-") as temporary:
            candidate = Path(temporary) / "candidate"
            c.create(root, candidate, as_of)
            # All source, derived and audit gates have passed in the isolated copy.
            # The workflow never uploads this checkout until overlay and tests finish.
            for folder in ("data", "analysis", "dist/data", "dist/analysis"):
                shutil.copytree(candidate / folder, root / folder, dirs_exist_ok=True)
            shutil.copyfile(candidate / "dist/title-audit.json", root / "dist/title-audit.json")
            shutil.copyfile(candidate / "docs/FINDINGS.md", root / "docs/FINDINGS.md")
        return record(root, "validated")
    except Exception as exc:
        record(root, "failed_retained_last_good", str(exc)[:300])
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["record", "refresh"])
    parser.add_argument("--as-of", type=p.parse_day, default=os.environ.get("AS_OF") or datetime.now(timezone.utc).date().isoformat())
    args = parser.parse_args()
    report = refresh(p.ROOT, args.as_of) if args.command == "refresh" else record(p.ROOT, "validated")
    print(json.dumps({"latest_attempt": report["history"][0]}, indent=2))
