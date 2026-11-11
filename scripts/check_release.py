"""Offline release gate: provenance, download references, HTML and payload budgets."""

from __future__ import annotations

import argparse
import gzip
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

from scripts import analysis as a
from scripts import pipeline as p


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.duplicate_ids, self.assets, self.labels, self.anchors = set(), [], [], [], []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get("id"):
            key = attrs["id"]
            if key in self.ids:
                self.duplicate_ids.append(key)
            self.ids.add(key)
        if tag == "script" and attrs.get("src"):
            self.assets.append(attrs["src"])
        if tag == "link" and attrs.get("rel") in {"stylesheet", "icon"}:
            self.assets.append(attrs["href"])
        if tag == "label" and attrs.get("for"):
            self.labels.append(attrs["for"])
        if tag == "a" and attrs.get("href", "").startswith("#") and attrs["href"] != "#":
            self.anchors.append(attrs["href"][1:])


def pointer_files(pointer: dict, analysis: bool = False) -> dict[str, str]:
    ident = pointer.get("analysis_id" if analysis else "snapshot_id")
    if not isinstance(ident, str) or not re.fullmatch(r"[a-f0-9]{64}", ident):
        raise p.PipelineError("Invalid snapshot ID in release pointer")
    files = pointer.get("files", {}) if analysis else {
        name: pointer.get(key) for key, name in {"dataset": "dataset.json", "csv": "views.csv", "health": "health.json", "manifest": "manifest.json"}.items()
    }
    required = {"analysis.json", "comparisons.csv", "predictions.csv", "findings.md", "manifest.json", "protocol.md"} if analysis else {"dataset.json", "views.csv", "health.json", "manifest.json"}
    if set(files) != required:
        raise p.PipelineError("Release pointer is missing expected files")
    for name, path in files.items():
        if path != f"snapshots/{ident}/{name}":
            raise p.PipelineError(f"Unsafe download reference: {name}")
    return files


def contrast(foreground: str, background: str) -> float:
    def luminance(color):
        rgb = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        rgb = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4 for value in rgb]
        return sum(value * weight for value, weight in zip(rgb, [.2126, .7152, .0722]))
    left, right = luminance(foreground), luminance(background)
    return (max(left, right) + .05) / (min(left, right) + .05)


def check(root: Path) -> dict:
    from scripts import title_audit
    title_audit.verify(root)
    source, _ = p.current_exports(root)
    derived = a.run(root, verify=True)
    publication = p.read_json(root / "dist/publication.json")
    if publication.get("data_pointer") != source or publication.get("analysis_pointer") != derived:
        raise p.PipelineError("Publication checkpoint does not match current data and analysis")
    if publication.get("title_audit_sha256") != p.digest((root / "dist/title-audit.json").read_bytes()):
        raise p.PipelineError("Publication title audit checksum differs")
    verified_downloads = 0
    for folder, pointer, is_analysis in (("data", source, False), ("analysis", derived, True)):
        for name, relative in pointer_files(pointer, is_analysis).items():
            content = (root / "dist" / folder / relative).read_bytes()
            if p.digest(content) != pointer["files_sha256"].get(name):
                raise p.PipelineError(f"Download checksum mismatch: {folder}/{name}")
            verified_downloads += 1
    dist = root / "dist"
    for filename in ("index.html", "case-study.html"):
        page = Page()
        page.feed((dist / filename).read_text())
        if page.duplicate_ids:
            raise p.PipelineError(f"Duplicate HTML IDs in {filename}: {page.duplicate_ids}")
        if set(page.labels + page.anchors) - page.ids:
            raise p.PipelineError(f"A label or in-page link has no target in {filename}")
        for asset in page.assets:
            if not asset.startswith("./") or ".." in Path(asset).parts or not (dist / asset).is_file():
                raise p.PipelineError(f"Nonlocal or missing startup asset: {asset}")
    css = (dist / "style.css").read_text()
    if re.search(r"@import|url\([\"']?https?://", css):
        raise p.PipelineError("External runtime CSS dependency")
    if "prefers-reduced-motion:reduce" not in css or "scroll-margin-top" not in css or ":focus-visible" not in css:
        raise p.PipelineError("Required keyboard/reduced-motion CSS is missing")
    pairs = {
        "primary_text": ("#f4f1e9", "#151c21", 4.5),
        "muted_text": ("#b2bdc3", "#151c21", 4.5),
        "dim_text": ("#8c9ca5", "#151c21", 4.5),
        "pink_signal": ("#f6b8ca", "#151c21", 3),
        "mint_signal": ("#99d4c7", "#151c21", 3),
        "violet_signal": ("#b7acf2", "#151c21", 3),
        "gold_signal": ("#ead09a", "#151c21", 3),
        "control_border": ("#607782", "#1b232a", 3),
    }
    ratios = {}
    for name, (fg, bg, threshold) in pairs.items():
        if fg not in css or bg not in css:
            raise p.PipelineError(f"Audited color no longer exists in CSS: {name}")
        ratio = contrast(fg, bg)
        if ratio < threshold:
            raise p.PipelineError(f"Contrast below recorded threshold: {name}")
        ratios[name] = round(ratio, 2)
    initial = [dist / "index.html", dist / "style.css", dist / "app.mjs", dist / "model.mjs", dist / "favicon.svg", dist / "publication.json", dist / "title-audit.json", dist / "data" / source["dataset"], dist / "analysis" / derived["files"]["analysis.json"]]
    total = sum(path.stat().st_size for path in initial)
    compressed = sum(len(gzip.compress(path.read_bytes(), mtime=0)) for path in initial)
    if total > 2_500_000 or compressed > 300_000:
        raise p.PipelineError("Initial payload exceeds the 2.5 MB raw / 300 KB gzip budgets")
    return {"status": "passed", "source_snapshot_id": source["snapshot_id"], "analysis_id": derived["analysis_id"],
            "verified_download_files": verified_downloads, "initial_request_count_including_favicon": len(initial),
            "initial_bytes": total, "estimated_gzip_bytes": compressed,
            "budgets": {"raw_bytes": 2_500_000, "gzip_bytes": 300_000}, "contrast_ratios": ratios,
            "note": "Gzip is an estimate, not an assertion that the preview/host enables compression. Color-pair checks are not a complete accessibility audit."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=p.ROOT)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(check(args.root.resolve()), indent=2))
        return 0
    except (p.PipelineError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Release gate failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
