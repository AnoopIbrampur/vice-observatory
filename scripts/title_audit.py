"""Preserve a bounded MediaWiki identity audit; never merge alias pageviews."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time
from urllib.parse import urlencode

from scripts import pipeline as p

LIMITATION = ("Current redirects and title-filtered move logs are a bounded audit, not a complete "
              "historical title reconstruction. Logs can include unrelated former occupants of a title. Aliases are not merged. Counts remain exact-title pageviews.")


def fetch(params):
    url = "https://en.wikipedia.org/w/api.php?" + urlencode(params)
    result = subprocess.run(["curl", "--disable", "--silent", "--show-error", "--fail", "--max-time", "45",
                             "--retry", "2", "--retry-delay", "2", "--user-agent", p.USER_AGENT, url], capture_output=True, check=True)
    value = json.loads(result.stdout)
    if "error" in value:
        raise p.PipelineError("MediaWiki rejected title audit")
    return url, result.stdout, value


def collect(root: Path):
    config, _ = p.load_config(root)
    entries = []
    for series in config["series"]:
        params = dict(action="query", format="json", redirects=1, titles=series["article"],
                      prop="info|redirects", rdlimit=500)
        evidence, redirects, pages = [], [], []
        while True:
            url, raw, value = fetch(params)
            sha = p.digest(raw)
            p.immutable_write(root / "data/title-audit/raw" / (sha + ".json"), raw)
            evidence.append(dict(url=url, sha256=sha))
            pages = list(value.get("query", {}).get("pages", {}).values())
            if len(pages) != 1 or "missing" in pages[0]:
                raise p.PipelineError(f"Cannot resolve article: {series['id']}")
            redirects.extend(item["title"] for item in pages[0].get("redirects", []))
            if "continue" not in value:
                break
            params.update(value["continue"])
        page = pages[0]
        # Fetch creation separately: continuation responses need not include revisions.
        url, raw, value = fetch(dict(action="query", format="json", pageids=page["pageid"],
                                    prop="revisions", rvdir="newer", rvlimit=1, rvprop="timestamp"))
        sha = p.digest(raw)
        p.immutable_write(root / "data/title-audit/raw" / (sha + ".json"), raw)
        evidence.append(dict(url=url, sha256=sha))
        created = next(iter(value["query"]["pages"].values()))["revisions"][0]["timestamp"]
        moves, continuation = [], {}
        while True:
            url, raw, value = fetch(dict(action="query", format="json", list="logevents", letype="move",
                                        letitle=page["title"], lelimit=500, **continuation))
            sha = p.digest(raw)
            p.immutable_write(root / "data/title-audit/raw" / (sha + ".json"), raw)
            evidence.append(dict(url=url, sha256=sha))
            moves.extend(value.get("query", {}).get("logevents", []))
            if "continue" not in value:
                break
            continuation = value["continue"]
        canonical = page["title"].replace(" ", "_")
        flags = []
        if canonical != series["article"]:
            flags.append("configured_title_is_redirect")
        if created[:10] > series["start_date"]:
            flags.append("page_created_after_requested_start")
        if any(series["start_date"] <= event["timestamp"][:10] <= (series["end_date"] or "9999-12-31") for event in moves):
            flags.append("visible_move_in_requested_window")
        entries.append(dict(series_id=series["id"], configured_article=series["article"], canonical_article=canonical,
                            page_id=page["pageid"], created_at=created, incoming_redirects=sorted(set(redirects)),
                            visible_move_logs=moves, flags=flags, evidence=evidence))
        time.sleep(.1)
    report = dict(schema_version=1, checked_at=p.utc_now(), limitation=LIMITATION, series=entries)
    p.atomic_write(root / "data/title-audit/current.json", p.encoded(report))
    p.atomic_write(root / "dist/title-audit.json", p.encoded(report))
    return report


def verify(root):
    report = p.read_json(root / "data/title-audit/current.json")
    config, _ = p.load_config(root)
    if {s["id"]: s["article"] for s in config["series"]} != {s["series_id"]: s["configured_article"] for s in report["series"]}:
        raise p.PipelineError("Title audit does not match the configured cohort")
    if (root / "dist/title-audit.json").read_bytes() != p.encoded(report):
        raise p.PipelineError("Browser title audit differs")
    for entry in report["series"]:
        definition = next(s for s in config["series"] if s["id"] == entry["series_id"])
        if "configured_title_is_redirect" in entry["flags"] and definition.get("article_policy") != "historical_title":
            raise p.PipelineError(f"Configure the canonical title before collecting: {entry['series_id']}")
        for evidence in entry["evidence"]:
            sha = evidence["sha256"]
            if not p.HASH.fullmatch(sha) or p.digest((root / "data/title-audit/raw" / (sha + ".json")).read_bytes()) != sha:
                raise p.PipelineError("Title audit evidence checksum failed")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["collect", "verify"])
    args = parser.parse_args()
    report = collect(p.ROOT) if args.command == "collect" else verify(p.ROOT)
    print(json.dumps({"series": len(report["series"]), "flags": {s["series_id"]: s["flags"] for s in report["series"] if s["flags"]}}, indent=2))
