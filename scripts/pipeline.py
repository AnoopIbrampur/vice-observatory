"""Collect, validate, publish, and replay Wikimedia observations without API keys.

Python 3.11+ and curl are the only runtime requirements. curl uses the operating
system's certificate store; TLS verification is never disabled.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Callable
from urllib.parse import quote, urlparse

ROOT = Path(__file__).resolve().parents[1]
API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
USER_AGENT = "ViceObservatory/0.1 (https://github.com/AnoopIbrampur/vice-observatory)"
SAFE_ID = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
RETRYABLE = {429, 500, 502, 503, 504}
RECORD_FIELDS = ("series_id", "article", "project", "date", "views", "access", "agent", "granularity")


class PipelineError(ValueError):
    """A failed acquisition or violated data contract; publication is withheld."""


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_bytes())
    except (OSError, ValueError) as exc:
        raise PipelineError(f"Cannot read valid JSON from {path}: {exc}") from exc


def parse_day(value: object) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise PipelineError(f"Invalid ISO calendar date: {value!r}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise PipelineError(f"Invalid calendar date: {value}") from exc


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".write-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def immutable_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".immutable-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            # Atomic create-if-absent: a killed writer cannot leave a truncated
            # content-addressed destination or overwrite an existing snapshot.
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != payload:
                raise PipelineError(f"Immutable file differs: {path}")
    finally:
        Path(temporary).unlink(missing_ok=True)


def load_config(root: Path) -> tuple[dict, dict]:
    config = read_json(root / "config/series.json")
    events = read_json(root / "config/events.json")
    validate_config(config, events)
    return config, events


def validate_config(config: object, event_config: object) -> None:
    if not isinstance(config, dict) or config.get("schema_version") != 1:
        raise PipelineError("Unsupported series configuration")
    expected = {"project": "en.wikipedia.org", "access": "all-access", "agent": "user", "granularity": "daily"}
    if any(config.get(key) != value for key, value in expected.items()):
        raise PipelineError("Unexpected source dimensions")
    if config.get("baseline_days") != [-28, -8]:
        raise PipelineError("Baseline must remain fixed at days -28 through -8")
    series = config.get("series")
    if not isinstance(series, list) or not series:
        raise PipelineError("At least one series is required")
    ids = set()
    for item in series:
        if not isinstance(item, dict):
            raise PipelineError("Series definition must be an object")
        key = item.get("id")
        if not isinstance(key, str) or not SAFE_ID.fullmatch(key) or key in ids:
            raise PipelineError("Series identifiers must be safe and unique")
        ids.add(key)
        for field in ("article", "label", "notes"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise PipelineError(f"Missing series {field}: {key}")
        if any(character in item["article"] for character in ("/", "\\", "\n", "\r", "#", "?")):
            raise PipelineError("Invalid article identifier")
        parse_day(item.get("release_date"))
        start = parse_day(item.get("start_date"))
        end = item.get("end_date")
        if end is not None and parse_day(end) < start:
            raise PipelineError("Series window is reversed")
        if item.get("release_kind") not in {"original_launch", "console_rerelease"}:
            raise PipelineError("Unrecognized release kind")
        if item.get("release_status") not in {"scheduled", "released"}:
            raise PipelineError("Unrecognized release status")
        if item.get("article_policy", "current_title") not in {"current_title", "historical_title"}:
            raise PipelineError("Unknown article title policy")
        check_https(item.get("release_source"))
    if not isinstance(event_config, dict) or event_config.get("schema_version") != 1:
        raise PipelineError("Unsupported event configuration")
    parse_day(event_config.get("checked_on"))
    events = event_config.get("events")
    if not isinstance(events, list):
        raise PipelineError("Events must be an array")
    event_ids = set()
    for event in events:
        if not isinstance(event, dict):
            raise PipelineError("Event must be an object")
        key = event.get("id")
        if not isinstance(key, str) or not SAFE_ID.fullmatch(key) or key in event_ids:
            raise PipelineError("Event identifiers must be safe and unique")
        event_ids.add(key)
        if event.get("series_id") not in ids:
            raise PipelineError("Event references an unknown series")
        parse_day(event.get("date"))
        if event.get("status") not in {"scheduled", "occurred"}:
            raise PipelineError("Unknown event status")
        if event.get("kind") not in {"announcement", "release", "rerelease", "trailer"}:
            raise PipelineError("Unknown event kind")
        for field in ("label", "verification"):
            if not isinstance(event.get(field), str) or not event[field].strip():
                raise PipelineError(f"Missing event {field}")
        check_https(event.get("source_url"))


def check_https(value: object) -> None:
    if not isinstance(value, str):
        raise PipelineError("Evidence URL must be a string")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise PipelineError("Evidence URL must be credential-free HTTPS")


def request_window(definition: dict, as_of: date) -> tuple[date, date]:
    start = parse_day(definition["start_date"])
    cutoff = as_of - timedelta(days=1)
    configured_end = definition["end_date"]
    end = min(parse_day(configured_end), cutoff) if configured_end else cutoff
    if end < start:
        raise PipelineError(f"No observable dates for {definition['id']} at {as_of}")
    return start, end


def source_url(config: dict, definition: dict, start: date, end: date) -> str:
    stamp = lambda day: day.strftime("%Y%m%d") + "00"
    return f"{API}/{config['project']}/{config['access']}/{config['agent']}/{quote(definition['article'], safe='')}/daily/{stamp(start)}/{stamp(end)}"


def validate_payload(payload: object, config: dict, definition: dict, start: date, end: date) -> list[dict]:
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise PipelineError("Source response must contain an items array")
    by_day = {}
    for item in payload["items"]:
        if not isinstance(item, dict):
            raise PipelineError("Observation must be an object")
        dimensions = {
            "article": definition["article"], "access": config["access"],
            "agent": config["agent"], "granularity": config["granularity"],
        }
        if any(item.get(key) != value for key, value in dimensions.items()):
            raise PipelineError(f"Unexpected article or dimensions for {definition['id']}")
        if item.get("project") not in {config["project"], config["project"].removesuffix(".org")}:
            raise PipelineError("Unexpected project")
        timestamp = item.get("timestamp")
        if not isinstance(timestamp, str) or not re.fullmatch(r"\d{8}00", timestamp):
            raise PipelineError("Expected a UTC midnight daily timestamp")
        day = parse_day(f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}")
        if not start <= day <= end:
            raise PipelineError(f"Observation outside requested window: {day}")
        if day in by_day:
            raise PipelineError(f"Duplicate date: {day}")
        views = item.get("views")
        if type(views) is not int or views < 0:
            raise PipelineError("Views must be a nonnegative integer, excluding booleans")
        by_day[day] = dict(zip(RECORD_FIELDS, (
            definition["id"], definition["article"], config["project"], day.isoformat(),
            views, config["access"], config["agent"], config["granularity"],
        )))
    expected = {start + timedelta(days=offset) for offset in range((end - start).days + 1)}
    missing = sorted(expected - by_day.keys())
    if missing:
        raise PipelineError(f"Incomplete {definition['id']}: {len(missing)} missing day(s), first {missing[0]}")
    return [by_day[day] for day in sorted(by_day)]


def retry_delay(headers: dict, attempt: int, now: datetime | None = None) -> float:
    raw = headers.get("retry-after")
    seconds = float(2 ** attempt)
    if raw is not None:
        try:
            seconds = max(seconds, float(raw))
        except ValueError:
            try:
                when = parsedate_to_datetime(raw)
                if when.tzinfo is None:
                    when = when.replace(tzinfo=timezone.utc)
                seconds = max(seconds, (when - (now or datetime.now(timezone.utc))).total_seconds())
            except (ValueError, TypeError, OverflowError):
                raise PipelineError("Invalid Retry-After; stopping rather than guessing")
    if not 0 <= seconds <= 60:
        raise PipelineError("Server requests a long retry delay; stop and retry later")
    return seconds


def parse_headers(text: str) -> dict:
    # curl may include proxy/redirect header blocks; retain only the final block.
    headers = {}
    for line in text.splitlines():
        if line.startswith("HTTP/"):
            headers = {}
        elif ":" in line:
            key, value = line.split(":", 1)
            headers[key.lower().strip()] = value.strip()
    return headers


def fetch(url: str) -> tuple[bytes, dict]:
    if not url.startswith(API + "/"):
        raise PipelineError("Collector only permits the configured Wikimedia endpoint")
    if not shutil.which("curl"):
        raise PipelineError("curl is required; install it or use a system that provides it")
    with tempfile.TemporaryDirectory(prefix="vice-fetch-") as directory:
        body = Path(directory) / "body"
        head = Path(directory) / "headers"
        for attempt in range(3):
            result = subprocess.run([
                "curl", "--silent", "--show-error", "--location", "--max-redirs", "3",
                "--proto", "=https", "--proto-redir", "=https", "--connect-timeout", "10",
                "--max-time", "45", "--max-filesize", "10000000", "--user-agent", USER_AGENT,
                "--dump-header", str(head), "--output", str(body), "--write-out", "%{http_code}", url,
            ], capture_output=True, text=True, timeout=50)
            if result.returncode:
                # Certificate/auth/DNS failures are not retried or worked around.
                if result.returncode in {18, 28, 52, 56} and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise PipelineError(f"curl transport failure ({result.returncode}): {result.stderr.strip()}")
            headers = parse_headers(head.read_text(errors="replace"))
            status = int(result.stdout)
            if status == 200:
                selected = {key: value for key, value in headers.items() if key in {"date", "etag", "last-modified", "content-type"}}
                return body.read_bytes(), {"http_status": status, "response_headers": selected, "fetched_at": utc_now()}
            if status in RETRYABLE and attempt < 2:
                time.sleep(retry_delay(headers, attempt))
                continue
            raise PipelineError(f"Wikimedia HTTP {status}; publication withheld")
    raise PipelineError("Acquisition exhausted retries")


def preserve_acquisition(data_dir: Path, url: str, start: date, end: date, payload: bytes, metadata: dict) -> dict:
    raw_hash = digest(payload)
    raw_path = f"raw/{raw_hash}.json"
    receipt = {
        "schema_version": 1, "url": url, "requested_start": start.isoformat(),
        "requested_end": end.isoformat(), "payload_sha256": raw_hash,
        "byte_count": len(payload), "raw_path": raw_path, **metadata,
    }
    receipt_bytes = encoded(receipt)
    receipt_hash = digest(receipt_bytes)
    receipt_path = f"receipts/{receipt_hash}.json"
    immutable_write(data_dir / raw_path, payload)
    immutable_write(data_dir / receipt_path, receipt_bytes)
    return {"raw_path": raw_path, "payload_sha256": raw_hash, "receipt_path": receipt_path, "receipt_sha256": receipt_hash}


def checked_file(data_dir: Path, relative: str, expected_hash: str, prefix: str) -> bytes:
    if not isinstance(expected_hash, str) or not HASH.fullmatch(expected_hash):
        raise PipelineError("Invalid provenance hash")
    if relative != f"{prefix}/{expected_hash}.json":
        raise PipelineError("Invalid provenance path")
    try:
        payload = (data_dir / relative).read_bytes()
    except OSError as exc:
        raise PipelineError(f"Missing provenance file: {relative}") from exc
    if digest(payload) != expected_hash:
        raise PipelineError(f"Checksum mismatch: {relative}")
    return payload


def rows_from_manifest(data_dir: Path, manifest: dict) -> list[tuple[dict, dict, list[dict], dict]]:
    if manifest.get("schema_version") != 1:
        raise PipelineError("Unsupported manifest")
    config, events = manifest["config"], manifest["event_config"]
    validate_config(config, events)
    as_of = parse_day(manifest["as_of"])
    entries = manifest["acquisitions"]
    if not isinstance(entries, list) or len(entries) != len(config["series"]):
        raise PipelineError("Manifest must acquire each configured series exactly once")
    by_id = {entry["series_id"]: entry for entry in entries}
    if set(by_id) != {definition["id"] for definition in config["series"]}:
        raise PipelineError("Manifest series do not match config")
    result = []
    for definition in config["series"]:
        entry = by_id[definition["id"]]
        start, end = request_window(definition, as_of)
        payload = checked_file(data_dir, entry["raw_path"], entry["payload_sha256"], "raw")
        receipt_bytes = checked_file(data_dir, entry["receipt_path"], entry["receipt_sha256"], "receipts")
        receipt = json.loads(receipt_bytes)
        expected = {
            "schema_version": 1, "url": source_url(config, definition, start, end),
            "requested_start": start.isoformat(), "requested_end": end.isoformat(),
            "payload_sha256": entry["payload_sha256"], "raw_path": entry["raw_path"],
            "http_status": 200, "byte_count": len(payload),
        }
        if any(receipt.get(key) != value for key, value in expected.items()):
            raise PipelineError("Receipt does not match the requested acquisition")
        try:
            timestamp = datetime.fromisoformat(receipt["fetched_at"])
            if timestamp.utcoffset() != timedelta(0):
                raise ValueError("UTC required")
        except (KeyError, TypeError, ValueError) as exc:
            raise PipelineError("Receipt requires a UTC acquisition timestamp") from exc
        rows = validate_payload(json.loads(payload), config, definition, start, end)
        result.append((definition, entry, rows, receipt))
    return result


def build_exports(data_dir: Path, manifest: dict) -> dict[str, bytes]:
    source_rows = rows_from_manifest(data_dir, manifest)
    manifest_hash = digest(encoded(manifest))
    series, health = [], []
    csv_stream = io.StringIO(newline="")
    writer = csv.DictWriter(csv_stream, fieldnames=RECORD_FIELDS, lineterminator="\n")
    writer.writeheader()
    for definition, entry, rows, receipt in source_rows:
        writer.writerows(rows)
        first, last = rows[0]["date"], rows[-1]["date"]
        series.append({
            **definition, "requested_start": receipt["requested_start"], "requested_end": receipt["requested_end"],
            "provenance": entry, "source_url": receipt["url"],
            "observations": [{"date": row["date"], "views": row["views"]} for row in rows],
        })
        health.append({
            "series_id": definition["id"], "observations": len(rows), "first_observed": first,
            "last_observed": last, "missing_days": 0, "coverage_fraction": 1.0,
            "complete_requested_window": True, "rolling": definition["end_date"] is None,
            "observation_age_days": (parse_day(manifest["as_of"]) - parse_day(last)).days,
            "fetched_at": receipt["fetched_at"], "payload_sha256": entry["payload_sha256"],
        })
    collected_at = max(receipt["fetched_at"] for _, _, _, receipt in source_rows)
    health_report = {
        "schema_version": 1, "as_of": manifest["as_of"], "collected_at": collected_at,
        "manifest_sha256": manifest_hash, "series_count": len(series),
        "observation_count": sum(item["observations"] for item in health),
        "complete": True, "series": health,
    }
    dataset = {
        "schema_version": 1, "as_of": manifest["as_of"], "collected_at": collected_at,
        "manifest_sha256": manifest_hash,
        "source": {"name": "Wikimedia Analytics API", "license": "CC0-1.0", "project": manifest["config"]["project"],
                   "access": "all-access", "agent": "user", "granularity": "daily", "timezone": "UTC"},
        "baseline_days": manifest["config"]["baseline_days"],
        "events": manifest["event_config"]["events"], "events_checked_on": manifest["event_config"]["checked_on"],
        "series": series, "health": health_report,
    }
    return {"manifest.json": encoded(manifest), "dataset.json": encoded(dataset), "views.csv": csv_stream.getvalue().encode(), "health.json": encoded(health_report)}


def publish(root: Path, manifest: dict, exports: dict[str, bytes]) -> dict:
    snapshot_id = digest(exports["manifest.json"])
    relative = f"snapshots/{snapshot_id}"
    # All content is prepared and validated before any active pointer is replaced.
    for base in (root / "data", root / "dist/data"):
        for filename, payload in exports.items():
            immutable_write(base / relative / filename, payload)
    pointer = {
        "schema_version": 1, "snapshot_id": snapshot_id, "as_of": manifest["as_of"],
        "manifest": f"{relative}/manifest.json", "dataset": f"{relative}/dataset.json",
        "csv": f"{relative}/views.csv", "health": f"{relative}/health.json",
        "files_sha256": {name: digest(payload) for name, payload in exports.items()},
    }
    # Each pointer references immutable, already-complete files. The two independent
    # consumers may briefly see different valid versions if a process stops here.
    atomic_write(root / "dist/data/current.json", encoded(pointer))
    atomic_write(root / "data/current.json", encoded(pointer))
    return pointer


def refresh(root: Path, as_of: date, fetcher: Callable = fetch) -> dict:
    if as_of > datetime.now(timezone.utc).date():
        raise PipelineError("Analysis date cannot be in the future")
    config, events = load_config(root)
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    lock = data_dir / ".refresh.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise PipelineError("A refresh lock already exists; check the running process before removing it") from exc
    os.close(fd)
    attempted_at = utc_now()
    try:
        acquisitions = []
        for definition in config["series"]:
            start, end = request_window(definition, as_of)
            url = source_url(config, definition, start, end)
            payload, metadata = fetcher(url)
            entry = preserve_acquisition(data_dir, url, start, end, payload, metadata)
            validate_payload(json.loads(payload), config, definition, start, end)
            acquisitions.append({"series_id": definition["id"], **entry})
        manifest = {"schema_version": 1, "as_of": as_of.isoformat(), "config": config, "event_config": events, "acquisitions": acquisitions}
        exports = build_exports(data_dir, manifest)
        pointer = publish(root, manifest, exports)
        atomic_write(data_dir / "status.json", encoded({"last_attempt": attempted_at, "status": "succeeded", "snapshot_id": pointer["snapshot_id"]}))
        return pointer
    except Exception as exc:
        atomic_write(data_dir / "status.json", encoded({"last_attempt": attempted_at, "status": "failed", "message": str(exc)}))
        raise
    finally:
        lock.unlink(missing_ok=True)


def current_exports(root: Path) -> tuple[dict, dict[str, bytes]]:
    pointer = read_json(root / "data/current.json")
    snapshot_id = pointer.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not HASH.fullmatch(snapshot_id):
        raise PipelineError("Invalid snapshot identifier")
    manifest_path = root / "data/snapshots" / snapshot_id / "manifest.json"
    if pointer.get("manifest") != f"snapshots/{snapshot_id}/manifest.json":
        raise PipelineError("Invalid current manifest reference")
    for field, filename in (("dataset", "dataset.json"), ("csv", "views.csv"), ("health", "health.json")):
        if pointer.get(field) != f"snapshots/{snapshot_id}/{filename}":
            raise PipelineError(f"Invalid current {field} reference")
    manifest = read_json(manifest_path)
    if digest(encoded(manifest)) != snapshot_id:
        raise PipelineError("Manifest checksum mismatch")
    exports = build_exports(root / "data", manifest)
    for name, payload in exports.items():
        if pointer.get("files_sha256", {}).get(name) != digest(payload):
            raise PipelineError(f"Export hash mismatch: {name}")
        for base in (root / "data", root / "dist/data"):
            if (base / "snapshots" / snapshot_id / name).read_bytes() != payload:
                raise PipelineError(f"Export differs from offline replay: {base}/{name}")
    if (root / "dist/data/current.json").read_bytes() != encoded(pointer):
        raise PipelineError("Browser and pipeline pointers differ")
    return pointer, exports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    acquire = commands.add_parser("refresh", help="Collect all sources and atomically publish a complete snapshot")
    acquire.add_argument("--as-of", type=parse_day, default=datetime.now(timezone.utc).date())
    commands.add_parser("verify", help="Verify current exports by replaying preserved sources without network")
    replay = commands.add_parser("replay", help="Rebuild the current snapshot's exports offline into a directory")
    replay.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        if args.command == "refresh":
            pointer = refresh(root, args.as_of)
        else:
            pointer, exports = current_exports(root)
            if args.command == "replay":
                output = args.output.resolve()
                if output == root or output.is_relative_to(root / "data") or output.is_relative_to(root / "dist"):
                    raise PipelineError("Replay output must be outside canonical data and dist directories")
                for name, payload in exports.items():
                    immutable_write(output / name, payload)
        print(json.dumps({"command": args.command, "status": "ok", "snapshot_id": pointer["snapshot_id"], "as_of": pointer["as_of"]}))
        return 0
    except (PipelineError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
