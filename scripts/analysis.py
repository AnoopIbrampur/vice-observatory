"""Deterministic descriptive analysis and past-only retrospective benchmarks.

Run `python3 -m scripts.analysis build` or `python3 -m scripts.analysis verify`.
No network, model fitting, paid services, or third-party packages are used.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
import io
import json
from pathlib import Path
from statistics import fmean
import sys

from scripts import pipeline as p

METHODS = ("yesterday", "trailing_week")
ALIGN_START, ALIGN_END = -90, 90
BASELINE_START, BASELINE_END = -28, -8
EVAL_START, EVAL_END = -14, 30
SCHEMA_VERSION = 1


def days(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def observations(series: dict, as_of: date) -> dict[date, int]:
    result = {}
    for row in series["observations"]:
        day = p.parse_day(row["date"])
        if day >= as_of:
            raise p.PipelineError("Analysis received current-day or future observations")
        if day in result:
            raise p.PipelineError("Analysis received duplicate observations")
        if type(row["views"]) is not int or row["views"] < 0:
            raise p.PipelineError("Analysis requires nonnegative integer counts")
        result[day] = row["views"]
    if not result:
        raise p.PipelineError("Analysis requires observations")
    return dict(sorted(result.items()))


def window(values: dict[date, int], start: date, end: date) -> dict:
    expected = days(start, end)
    present = [values[day] for day in expected if day in values]
    complete = len(present) == len(expected) and bool(expected)
    return {
        "start": start.isoformat(), "end": end.isoformat(),
        "expected_days": len(expected), "observed_days": len(present), "complete": complete,
        "total_views": sum(present) if complete else None,
        "mean_views": fmean(present) if complete else None,
    }


def percent_change(current: int | float | None, previous: int | float | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return (current - previous) / previous * 100


def summary(values: dict[date, int]) -> dict:
    first, last = min(values), max(values)
    recent = window(values, last - timedelta(days=6), last)
    prior = window(values, last - timedelta(days=13), last - timedelta(days=7))
    peak = max(values.values())
    return {
        "observed_start": first.isoformat(), "observed_end": last.isoformat(),
        "observed_days": len(values), "latest_views": values[last],
        "trailing_7_day_mean": recent["mean_views"],
        "week_change": {"recent": recent, "previous": prior,
                        "percent": percent_change(recent["total_views"], prior["total_views"]),
                        "status": "incomplete" if not recent["complete"] or not prior["complete"] else "zero_baseline" if prior["total_views"] == 0 else "available"},
        "peak": {"views": peak, "dates": [day.isoformat() for day, count in values.items() if count == peak]},
    }


def aligned_series(series: dict, values: dict[date, int], as_of: date) -> dict:
    release = p.parse_day(series["release_date"])
    baseline = window(values, release + timedelta(days=BASELINE_START), release + timedelta(days=BASELINE_END))
    baseline["status"] = "incomplete" if not baseline["complete"] else "zero_baseline" if baseline["mean_views"] == 0 else "available"
    baseline["relative_start"], baseline["relative_end"] = BASELINE_START, BASELINE_END
    baseline["retrospective_normalization"] = True
    mean = baseline["mean_views"] if baseline["status"] == "available" else None
    first, last = min(values), max(values)
    aligned = []
    for relative in range(ALIGN_START, ALIGN_END + 1):
        day = release + timedelta(days=relative)
        count = values.get(day)
        state = "future" if day >= as_of else "observed" if day in values else "outside_coverage" if day < first or day > last else "missing"
        aligned.append({"relative_day": relative, "date": day.isoformat(), "state": state,
                        "views": count, "index_100": 100 * count / mean if count is not None and mean is not None else None})
    return {"baseline": baseline, "points": aligned}


def event_result(event: dict, values: dict[date, int]) -> dict:
    day = p.parse_day(event["date"])
    before = window(values, day - timedelta(days=7), day - timedelta(days=1))
    after = window(values, day, day + timedelta(days=6))
    status = "scheduled" if event["status"] == "scheduled" else "incomplete" if not before["complete"] or not after["complete"] else "zero_baseline" if before["mean_views"] == 0 else "available"
    return {
        **event, "analysis_status": status, "before": before, "after": after,
        "percent_change": percent_change(after["mean_views"], before["mean_views"]) if status == "available" else None,
        "interpretation": "Descriptive association only; timing does not establish causation.",
    }


def regime(relative: int) -> str:
    return "pre_launch" if relative < 0 else "launch_days" if relative <= 2 else "post_launch"


def predictions(series: dict, values: dict[date, int], as_of: date) -> tuple[list[dict], list[dict]]:
    release = p.parse_day(series["release_date"])
    scored, excluded = [], []
    for relative in range(EVAL_START, EVAL_END + 1):
        target = release + timedelta(days=relative)
        context = days(target - timedelta(days=7), target - timedelta(days=1))
        missing = [day.isoformat() for day in [*context, target] if day not in values]
        if target >= as_of or missing:
            excluded.append({"date": target.isoformat(), "relative_day": relative,
                             "reason": "future" if target >= as_of else "missing_context_or_target", "missing_dates": missing})
            continue
        yesterday, week = values[context[-1]], fmean(values[day] for day in context)
        actual = values[target]
        scored.append({
            "series_id": series["id"], "release_kind": series["release_kind"],
            "date": target.isoformat(), "relative_day": relative, "regime": regime(relative),
            "context_start": context[0].isoformat(), "context_end": context[-1].isoformat(),
            "actual_views": actual, "yesterday": yesterday, "trailing_week": week,
            "yesterday_absolute_error": abs(actual - yesterday), "trailing_week_absolute_error": abs(actual - week),
        })
    return scored, excluded


def score(rows: list[dict]) -> dict:
    actual_total = sum(row["actual_views"] for row in rows)
    metrics = {}
    for method in METHODS:
        errors = [row[f"{method}_absolute_error"] for row in rows]
        metrics[method] = {
            "mae": fmean(errors) if errors else None,
            "absolute_error_total": sum(errors),
            "wape": sum(errors) / actual_total if rows and actual_total else None,
        }
    return {"scored_days": len(rows), "actual_views_total": actual_total, "methods": metrics}


def benchmark(series_list: list[dict], value_maps: dict[str, dict], as_of: date) -> tuple[dict, list[dict]]:
    reports, all_rows = [], []
    for series in series_list:
        if series["release_status"] != "released":
            continue
        rows, excluded = predictions(series, value_maps[series["id"]], as_of)
        if not rows:
            winner = None
        else:
            scored = score(rows)["methods"]
            left, right = scored["yesterday"]["mae"], scored["trailing_week"]["mae"]
            winner = "tie" if left == right else "yesterday" if left < right else "trailing_week"
        reports.append({
            "series_id": series["id"], "label": series["label"], "release_kind": series["release_kind"],
            "evaluation_start": (p.parse_day(series["release_date"]) + timedelta(days=EVAL_START)).isoformat(),
            "evaluation_end": (p.parse_day(series["release_date"]) + timedelta(days=EVAL_END)).isoformat(),
            "expected_days": EVAL_END - EVAL_START + 1, "excluded_days": len(excluded), "exclusions": excluded,
            "overall": score(rows), "lowest_mae_method": winner,
            "regimes": {name: score([row for row in rows if row["regime"] == name]) for name in ("pre_launch", "launch_days", "post_launch")},
        })
        all_rows.extend(rows)
    macro = {}
    for method in METHODS:
        values = [report["overall"]["methods"][method]["wape"] for report in reports]
        macro[method] = {"wape": fmean(values) if values and all(value is not None for value in values) else None,
                         "eligible_series": sum(value is not None for value in values), "expected_series": len(reports)}
    return {
        "question": "Predict the next UTC day's article pageviews using only preceding observations.",
        "evaluation_relative_days": [EVAL_START, EVAL_END], "series": reports,
        "pooled": score(all_rows), "macro_average": macro,
        "excluded_series": [{"series_id": series["id"], "reason": "release_not_verified_as_occurred"} for series in series_list if series["release_status"] != "released"],
        "limitations": ["Fixed retrospective benchmark, not prospective evidence.",
                        "Three selected releases do not establish generalization to unseen launches.",
                        "Pooled MAE is dominated by series with larger pageview counts.",
                        "GTA V 2022 is a console re-release; article traffic is not platform-specific."],
    }, all_rows


def analyze(dataset: dict, manifest: dict) -> tuple[dict, list[dict]]:
    as_of = p.parse_day(dataset["as_of"])
    maps = {series["id"]: observations(series, as_of) for series in dataset["series"]}
    if len(maps) != len(dataset["series"]):
        raise p.PipelineError("Duplicate analysis series")
    result = []
    for series in dataset["series"]:
        values = maps[series["id"]]
        daily = [{"date": day.isoformat(), "views": count,
                  "trailing_7_day_mean": window(values, day - timedelta(days=6), day)["mean_views"]}
                 for day, count in values.items()]
        result.append({
            "id": series["id"], "label": series["label"], "article": series["article"],
            "release_date": series["release_date"], "release_kind": series["release_kind"],
            "release_status": series["release_status"], "notes": series["notes"],
            "summary": summary(values), "daily": daily,
            "comparison": aligned_series(series, values, as_of),
        })
    bench, rows = benchmark(dataset["series"], maps, as_of)
    return {
        "schema_version": SCHEMA_VERSION, "as_of": dataset["as_of"], "timezone": "UTC",
        "source_snapshot_id": dataset["manifest_sha256"], "analysis_manifest": manifest,
        "series": result, "events": [event_result(event, maps[event["series_id"]]) for event in dataset["events"]],
        "benchmark": bench,
        "interpretation": {"signal": "English Wikipedia exact-title article pageviews; not unique people, sales, sentiment, or players.",
                           "normalization": "Retrospective descriptive index; not a point-in-time forecast feature.",
                           "causality": "Event-window changes do not establish causal effects."},
    }, rows


def csv_bytes(rows: list[dict], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def display(value: int | float | None, decimals: int = 1) -> str:
    return "Unavailable" if value is None else f"{value:,.{decimals}f}"


def findings(result: dict) -> bytes:
    lines = ["# Phase 2 findings and retrospective benchmark", "",
             f"Analysis date: {result['as_of']} (UTC; current day excluded). Source snapshot: `{result['source_snapshot_id']}`.", "",
             "Generated from verified saved observations under the fixed [analysis protocol](https://github.com/AnoopIbrampur/vice-observatory/blob/main/docs/ANALYSIS_PROTOCOL.md). Exact protocol bytes are archived alongside each analysis snapshot. This is descriptive analysis and a retrospective benchmark, not a prospective forecast record.", "",
             "## Observed attention", "",
             "The latest value and week change below refer to each series' own final observed date, not a shared calendar date. Historical windows are deliberately fixed.", "",
             "| Series | Last observed | Daily views | Trailing 7-day mean | Change vs previous complete 7 days |",
             "| --- | --- | ---: | ---: | ---: |"]
    for item in result["series"]:
        info = item["summary"]
        change = info["week_change"]["percent"]
        lines.append(f"| {item['label']} | {info['observed_end']} | {info['latest_views']:,} | {display(info['trailing_7_day_mean'])} | {display(change)}{'%' if change is not None else ''} |")
    vi = next((item for item in result["series"] if item["id"] == "gta-vi"), None)
    if vi:
        recent, previous = vi["summary"]["week_change"]["recent"], vi["summary"]["week_change"]["previous"]
        lines.extend(["", f"GTA VI's complete-week comparison uses {recent['start']} through {recent['end']} against {previous['start']} through {previous['end']}. It measures attention to this article only."])
    lines.extend(["", "## Release comparison availability", "",
                  "Index = 100 × daily views / mean views on release-relative days -28 through -8 (21 complete dates). The normalizer is retrospective and must not be treated as a historical forecasting feature.", "",
                  "| Series | Release date | Release type | Baseline coverage | Baseline mean | Index status |",
                  "| --- | --- | --- | ---: | ---: | --- |"])
    for item in result["series"]:
        base = item["comparison"]["baseline"]
        lines.append(f"| {item['label']} | {item['release_date']} ({item['release_status']}) | {item['release_kind']} | {base['observed_days']}/{base['expected_days']} | {display(base['mean_views'])} | {base['status']} |")
    if vi:
        future_count = sum(point["state"] == "future" for point in vi["comparison"]["points"])
        lines.extend(["", f"GTA VI has {future_count} unobserved future dates in the fixed -90 to +90 comparison range. They contain nulls, not extrapolated values. Its scheduled release is not marked as having occurred."])
    lines.extend(["", "## Event-window associations", "",
                  "Compare seven days before an event against event day through day +6. Scheduled events are not assigned a measured effect. These are associations; no causal inference is supported.", "",
                  "| Event | Date | Status | Before coverage | After coverage | Mean change |",
                  "| --- | --- | --- | ---: | ---: | ---: |"])
    for event in result["events"]:
        before, after = event["before"], event["after"]
        change = event["percent_change"]
        lines.append(f"| [{event['label']}]({event['source_url']}) | {event['date']} | {event['analysis_status']} | {before['observed_days']}/7 | {after['observed_days']}/7 | {display(change)}{'%' if change is not None else ''} |")
    lines.extend(["", "## Historical forecasting benchmark", "",
                  "Fixed targets: days -14 through +30 around each historical release. Earlier dates supply context. Yesterday uses t-1; trailing-week uses t-7 through t-1. Both methods are scored on the same dates. Nothing is fitted or tuned. GTA VI is excluded because its launch window has not been observed.", "",
                  "| Series | Targets | Yesterday MAE | Trailing-week MAE | Yesterday WAPE | Trailing-week WAPE | Lower MAE |",
                  "| --- | ---: | ---: | ---: | ---: | ---: | --- |"])
    for item in result["benchmark"]["series"]:
        methods = item["overall"]["methods"]
        left, right = methods["yesterday"], methods["trailing_week"]
        as_pct = lambda value: display(100 * value) + "%" if value is not None else "Unavailable"
        lines.append(f"| {item['label']} | {item['overall']['scored_days']}/{item['expected_days']} | {display(left['mae'])} | {display(right['mae'])} | {as_pct(left['wape'])} | {as_pct(right['wape'])} | {item['lowest_mae_method']} |")
    pooled, macro = result["benchmark"]["pooled"], result["benchmark"]["macro_average"]
    lines.extend(["", f"Total scored targets: {pooled['scored_days']}. MAE is pageviews per day; WAPE is total absolute error divided by actual views, not an accuracy score.", "",
                  f"Pooled MAE: yesterday {display(pooled['methods']['yesterday']['mae'])}; trailing-week {display(pooled['methods']['trailing_week']['mae'])}. This is sensitive to the largest series.", "",
                  f"Equal-game macro WAPE: yesterday {display(100 * macro['yesterday']['wape'] if macro['yesterday']['wape'] is not None else None)}%; trailing-week {display(100 * macro['trailing_week']['wape'] if macro['trailing_week']['wape'] is not None else None)}%.", "",
                  "### Fixed regimes", "",
                  "| Series | Regime | Days | Yesterday MAE | Trailing-week MAE |",
                  "| --- | --- | ---: | ---: | ---: |"])
    for item in result["benchmark"]["series"]:
        for name, scored in item["regimes"].items():
            lines.append(f"| {item['label']} | {name} | {scored['scored_days']} | {display(scored['methods']['yesterday']['mae'])} | {display(scored['methods']['trailing_week']['mae'])} |")
    lines.extend(["", "## Interpretation and limits", "",
                  "- The score tables describe these three selected historical windows. They do not establish generalization or significance across unseen launches.",
                  "- Launch-day spikes are a different regime from ordinary traffic; see the separate launch-days scores rather than relying on an average alone.",
                  "- A smoother descriptive chart is not automatically a better next-day prediction. Report whichever method actually has lower error in each fixed window.",
                  "- GTA V 2022 is a console re-release and the underlying article covers the whole game. Platform-specific interest cannot be isolated.",
                  "- Exact-title traffic can omit earlier article titles and redirects. Early GTA VI values must not be read as total awareness.",
                  "- There is no paid inference, trained ML model, or claimed GTA VI sales forecast here.", "",
                  "Full-precision values and every scored prediction are exported beside the source manifest. See `analysis/current.json` for their immutable paths. Display rounding in this report does not alter scoring.", ""])
    return "\n".join(lines).encode()


def build_artifacts(root: Path) -> tuple[dict, dict[str, bytes]]:
    source_pointer, source_exports = p.current_exports(root)
    protocol = (root / "docs/ANALYSIS_PROTOCOL.md").read_bytes()
    manifest = {
        "schema_version": SCHEMA_VERSION, "source_snapshot_id": source_pointer["snapshot_id"],
        "as_of": source_pointer["as_of"], "protocol_sha256": p.digest(protocol),
        "engine_sha256": p.digest(Path(__file__).read_bytes()),
        "protocol_path": "docs/ANALYSIS_PROTOCOL.md",
        "comparison_relative_days": [ALIGN_START, ALIGN_END],
        "baseline_relative_days": [BASELINE_START, BASELINE_END], "benchmark_relative_days": [EVAL_START, EVAL_END],
        "methods": list(METHODS),
    }
    dataset = json.loads(source_exports["dataset.json"])
    result, prediction_rows = analyze(dataset, manifest)
    comparison_rows = [{"series_id": item["id"], "release_kind": item["release_kind"], "release_status": item["release_status"], **point}
                       for item in result["series"] for point in item["comparison"]["points"]]
    fields = ["series_id", "release_kind", "date", "relative_day", "regime", "context_start", "context_end", "actual_views", "yesterday", "trailing_week", "yesterday_absolute_error", "trailing_week_absolute_error"]
    exports = {
        "manifest.json": p.encoded(manifest), "analysis.json": p.encoded(result),
        "predictions.csv": csv_bytes(prediction_rows, fields),
        "comparisons.csv": csv_bytes(comparison_rows, ["series_id", "release_kind", "release_status", "relative_day", "date", "state", "views", "index_100"]),
        "findings.md": findings(result), "protocol.md": protocol,
    }
    analysis_id = p.digest(exports["manifest.json"])
    pointer = {"schema_version": SCHEMA_VERSION, "analysis_id": analysis_id,
               "source_snapshot_id": source_pointer["snapshot_id"], "as_of": source_pointer["as_of"],
               "files": {name: f"snapshots/{analysis_id}/{name}" for name in exports},
               "files_sha256": {name: p.digest(content) for name, content in exports.items()}}
    return pointer, exports


def run(root: Path, verify: bool = False) -> dict:
    pointer, exports = build_artifacts(root)
    for base in (root / "analysis", root / "dist/analysis"):
        for name, content in exports.items():
            path = base / pointer["files"][name]
            if verify:
                if path.read_bytes() != content:
                    raise p.PipelineError(f"Analysis replay differs: {path}")
            else:
                p.immutable_write(path, content)
    if verify:
        for base in (root / "analysis", root / "dist/analysis"):
            if (base / "current.json").read_bytes() != p.encoded(pointer):
                raise p.PipelineError("Analysis pointer stale or altered; rebuild against current sources/protocol/code")
        if (root / "docs/FINDINGS.md").read_bytes() != exports["findings.md"]:
            raise p.PipelineError("Readable findings report differs from reproducible output")
    else:
        p.atomic_write(root / "dist/analysis/current.json", p.encoded(pointer))
        p.atomic_write(root / "analysis/current.json", p.encoded(pointer))
        p.atomic_write(root / "docs/FINDINGS.md", exports["findings.md"])
    return pointer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "verify"])
    parser.add_argument("--root", type=Path, default=p.ROOT)
    args = parser.parse_args(argv)
    try:
        pointer = run(args.root.resolve(), verify=args.command == "verify")
        print(json.dumps({"command": args.command, "status": "ok", "analysis_id": pointer["analysis_id"], "source_snapshot_id": pointer["source_snapshot_id"]}))
        return 0
    except (p.PipelineError, OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Analysis failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
