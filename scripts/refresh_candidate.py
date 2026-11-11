"""Acquire a validated refresh in isolation; never push, deploy, or edit source."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from scripts import analysis as a
from scripts import check_release
from scripts import pipeline as p


def create(root: Path, output: Path, as_of) -> dict:
    root, output = root.resolve(), output.resolve()
    if output == root or output.is_relative_to(root):
        raise p.PipelineError("Candidate output must be outside the source checkout")
    if output.exists():
        raise p.PipelineError("Candidate output already exists; choose a new directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vice-candidate-", dir=output.parent) as temporary:
        stage = Path(temporary) / "checkout"
        stage.mkdir()
        for folder in ("scripts", "config", "docs", "dist", "data", "analysis"):
            shutil.copytree(root / folder, stage / folder, ignore=shutil.ignore_patterns("__pycache__", ".refresh.lock", "status.json"))
        source = p.refresh(stage, as_of)
        derived = a.run(stage)
        gate = check_release.check(stage)
        candidate = Path(temporary) / "candidate"
        candidate.mkdir()
        for folder in ("data", "analysis", "dist/data", "dist/analysis"):
            shutil.copytree(stage / folder, candidate / folder, ignore=shutil.ignore_patterns("status.json", ".refresh.lock"))
        (candidate / "docs").mkdir()
        shutil.copyfile(stage / "docs/FINDINGS.md", candidate / "docs/FINDINGS.md")
        report = {"status": "validated_candidate", "as_of": as_of.isoformat(),
                  "source_snapshot_id": source["snapshot_id"], "analysis_id": derived["analysis_id"],
                  "source_checkout_modified": False, "pushed": False, "deployed": False,
                  "release_gate": gate}
        (candidate / "CANDIDATE.json").write_bytes(p.encoded(report))
        (candidate / "README.txt").write_text(
            "Validated refresh candidate, not a deployment. Overlay these files only onto the matching project source, "
            "then run the full test suite and release gate before committing. Do not describe this artifact as live data.\n")
        os.replace(candidate, output)
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=p.ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--as-of", type=p.parse_day, default=os.environ.get("AS_OF") or datetime.now(timezone.utc).date().isoformat())
    args = parser.parse_args(argv)
    try:
        print(json.dumps(create(args.root, args.output, args.as_of), indent=2))
        return 0
    except (p.PipelineError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Candidate refresh failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
