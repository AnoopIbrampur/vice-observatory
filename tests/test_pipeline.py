"""Fault injection and end-to-end reproducibility checks; no network needed."""

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import pipeline as p


def fixture():
    config = {
        "schema_version": 1, "project": "en.wikipedia.org", "access": "all-access",
        "agent": "user", "granularity": "daily", "baseline_days": [-28, -8],
        "series": [{
            "id": "sample", "label": "Sample game", "article": "Sample_Game",
            "start_date": "2020-01-01", "end_date": None, "release_date": "2020-02-01",
            "release_kind": "original_launch", "release_status": "scheduled",
            "release_source": "https://example.org/launch", "notes": "Synthetic test fixture, never a published observation.",
        }],
    }
    events = {"schema_version": 1, "checked_on": "2020-01-04", "events": []}
    payload = {"items": [{
        "project": "en.wikipedia", "article": "Sample_Game", "access": "all-access",
        "agent": "user", "granularity": "daily", "timestamp": f"2020010{day}00", "views": count,
    } for day, count in [(1, 0), (2, 30), (3, 80)]]}
    return config, events, payload


def response(payload):
    return p.encoded(payload), {
        "http_status": 200, "response_headers": {"content-type": "application/json"},
        "fetched_at": "2026-11-11T10:00:00.000000+00:00",
    }


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.config, self.events, self.payload = fixture()
        self.definition = self.config["series"][0]
        self.start, self.end = date(2020, 1, 1), date(2020, 1, 3)

    def validate(self):
        return p.validate_payload(self.payload, self.config, self.definition, self.start, self.end)

    def test_out_of_order_rows_sort_without_changing_counts_or_zero(self):
        self.payload["items"].reverse()
        rows = self.validate()
        self.assertEqual([row["views"] for row in rows], [0, 30, 80])
        self.assertEqual(rows[0]["project"], "en.wikipedia.org")

    def test_missing_day_is_rejected_not_zero_filled(self):
        self.payload["items"].pop(1)
        with self.assertRaisesRegex(p.PipelineError, "missing day"):
            self.validate()

    def test_duplicate_date_is_rejected_even_with_same_value(self):
        self.payload["items"].append(deepcopy(self.payload["items"][0]))
        with self.assertRaisesRegex(p.PipelineError, "Duplicate"):
            self.validate()

    def test_negative_float_boolean_and_string_counts_are_rejected(self):
        for value in [-1, 2.5, True, "30", None]:
            with self.subTest(value=value):
                self.payload["items"][0]["views"] = value
                with self.assertRaises(p.PipelineError):
                    self.validate()

    def test_future_or_out_of_range_observation_is_rejected(self):
        self.payload["items"][0]["timestamp"] = "2020010400"
        with self.assertRaisesRegex(p.PipelineError, "outside"):
            self.validate()

    def test_invalid_or_nonmidnight_timestamp_is_rejected(self):
        for timestamp in ["2020023000", "2020010101", "20200101", 2020010100]:
            with self.subTest(timestamp=timestamp):
                self.payload["items"][0]["timestamp"] = timestamp
                with self.assertRaises(p.PipelineError):
                    self.validate()

    def test_each_wrong_source_dimension_is_rejected(self):
        for field, value in [("project", "fr.wikipedia"), ("article", "Different_Game"), ("agent", "all-agents"), ("access", "desktop"), ("granularity", "monthly")]:
            with self.subTest(field=field):
                payload = deepcopy(self.payload)
                payload["items"][0][field] = value
                with self.assertRaises(p.PipelineError):
                    p.validate_payload(payload, self.config, self.definition, self.start, self.end)

    def test_empty_or_malformed_response_rejected(self):
        for payload in [None, [], {}, {"items": []}, {"items": "not an array"}, {"items": [None]}]:
            with self.subTest(payload=payload), self.assertRaises(p.PipelineError):
                p.validate_payload(payload, self.config, self.definition, self.start, self.end)

    def test_duplicate_config_ids_and_unsafe_ids_rejected(self):
        for key in ["../sample", "sample"]:
            config = deepcopy(self.config)
            duplicate = deepcopy(config["series"][0])
            duplicate["id"] = key
            config["series"].append(duplicate)
            with self.assertRaises(p.PipelineError):
                p.validate_config(config, self.events)

    def test_baseline_cannot_silently_change(self):
        self.config["baseline_days"] = [-7, -1]
        with self.assertRaisesRegex(p.PipelineError, "Baseline"):
            p.validate_config(self.config, self.events)

    def test_https_evidence_required(self):
        for url in ["http://example.org", "https://name:secret@example.org", "not a url"]:
            with self.subTest(url=url), self.assertRaises(p.PipelineError):
                p.check_https(url)

    def test_rolling_window_excludes_current_day(self):
        self.assertEqual(p.request_window(self.definition, date(2020, 1, 4)), (self.start, self.end))

    def test_fixed_window_is_capped_at_cutoff(self):
        self.definition["end_date"] = "2020-01-10"
        self.assertEqual(p.request_window(self.definition, date(2020, 1, 4))[1], self.end)


class TransportTests(unittest.TestCase):
    def test_retry_after_seconds_and_http_date_respected(self):
        now = datetime(2020, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(p.retry_delay({"retry-after": "12"}, 0, now), 12)
        self.assertEqual(p.retry_delay({"retry-after": "Wed, 01 Jan 2020 00:00:30 GMT"}, 0, now), 30)

    def test_long_throttle_stops_rather_than_retrying_early(self):
        with self.assertRaisesRegex(p.PipelineError, "long retry"):
            p.retry_delay({"retry-after": "120"}, 0)

    def test_headers_ignore_earlier_proxy_and_redirect_blocks(self):
        headers = p.parse_headers("HTTP/1.1 200 Connection established\r\nX-Proxy: hidden\r\n\r\nHTTP/2 200\r\nContent-Type: application/json\r\nETag: abc\r\n")
        self.assertEqual(headers, {"content-type": "application/json", "etag": "abc"})

    def test_non_wikimedia_fetch_stops_before_network(self):
        with self.assertRaises(p.PipelineError):
            p.fetch("https://example.org/data")

    def test_429_retries_and_403_does_not(self):
        def simulated(statuses):
            def run(command, **kwargs):
                status = statuses.pop(0)
                Path(command[command.index("--dump-header") + 1]).write_text(f"HTTP/2 {status}\nRetry-After: 3\n")
                Path(command[command.index("--output") + 1]).write_bytes(b'{}')
                return type("Result", (), {"returncode": 0, "stdout": str(status), "stderr": ""})()
            return run
        with patch.object(p.shutil, "which", return_value="/usr/bin/curl"), patch.object(p.time, "sleep") as sleep:
            with patch.object(p.subprocess, "run", side_effect=simulated([429, 200])) as run:
                payload, metadata = p.fetch(p.API + "/test")
                self.assertEqual(run.call_count, 2)
                sleep.assert_called_once_with(3)
                self.assertEqual(metadata["http_status"], 200)
            with patch.object(p.subprocess, "run", side_effect=simulated([403])) as run:
                with self.assertRaisesRegex(p.PipelineError, "403"):
                    p.fetch(p.API + "/test")
                self.assertEqual(run.call_count, 1)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config, self.events, self.payload = fixture()
        self.write_config()

    def write_config(self):
        (self.root / "config").mkdir(exist_ok=True)
        (self.root / "config/series.json").write_bytes(p.encoded(self.config))
        (self.root / "config/events.json").write_bytes(p.encoded(self.events))

    def acquire(self):
        return p.refresh(self.root, date(2020, 1, 4), fetcher=lambda url: response(self.payload))

    def test_full_refresh_replays_exact_json_csv_and_manifest_without_network(self):
        pointer = self.acquire()
        with patch.object(p, "fetch", side_effect=AssertionError("Offline replay used network")):
            verified, exports = p.current_exports(self.root)
        self.assertEqual(verified, pointer)
        self.assertEqual(json.loads(exports["health.json"])["observation_count"], 3)
        self.assertIn(b"2020-01-01,0", exports["views.csv"])
        self.assertEqual(json.loads(exports["dataset.json"])["series"][0]["release_status"], "scheduled")

    def test_repeat_with_same_receipts_is_idempotent(self):
        first = self.acquire()
        self.assertEqual(first, self.acquire())
        self.assertEqual(len(list((self.root / "data/snapshots").iterdir())), 1)

    def test_later_series_failure_preserves_both_active_pointers(self):
        self.acquire()
        old = (self.root / "data/current.json").read_bytes()
        browser_old = (self.root / "dist/data/current.json").read_bytes()
        extra = deepcopy(self.config["series"][0])
        extra.update(id="second", article="Second_Game")
        self.config["series"].append(extra)
        self.write_config()
        def acquire(url):
            if "Second_Game" in url:
                raise p.PipelineError("source unavailable")
            return response(self.payload)
        with self.assertRaisesRegex(p.PipelineError, "unavailable"):
            p.refresh(self.root, date(2020, 1, 4), fetcher=acquire)
        self.assertEqual((self.root / "data/current.json").read_bytes(), old)
        self.assertEqual((self.root / "dist/data/current.json").read_bytes(), browser_old)
        self.assertEqual(json.loads((self.root / "data/status.json").read_bytes())["status"], "failed")
        self.assertFalse((self.root / "data/.refresh.lock").exists())
        p.current_exports(self.root)

    def test_incomplete_and_html_response_never_replace_good_data(self):
        self.acquire()
        old = (self.root / "data/current.json").read_bytes()
        for invalid in [b'{"items": []}', b'<html>service unavailable</html>']:
            with self.subTest(payload=invalid), self.assertRaises(ValueError):
                p.refresh(self.root, date(2020, 1, 4), fetcher=lambda url: (invalid, response(self.payload)[1]))
            self.assertEqual((self.root / "data/current.json").read_bytes(), old)

    def test_tampered_raw_payload_detected(self):
        self.acquire()
        raw = next((self.root / "data/raw").glob("*.json"))
        raw.write_bytes(b'{"items": []}')
        with self.assertRaisesRegex(p.PipelineError, "Checksum"):
            p.current_exports(self.root)

    def test_tampered_public_csv_detected(self):
        pointer = self.acquire()
        path = self.root / "dist/data" / pointer["csv"]
        path.write_bytes(path.read_bytes().replace(b",80,", b",8000,"))
        with self.assertRaisesRegex(p.PipelineError, "differs"):
            p.current_exports(self.root)

    def test_existing_refresh_lock_is_respected(self):
        (self.root / "data").mkdir()
        (self.root / "data/.refresh.lock").touch()
        with self.assertRaisesRegex(p.PipelineError, "lock"):
            self.acquire()

    def test_bad_export_reference_detected_even_if_pointers_match(self):
        pointer = self.acquire()
        pointer["csv"] = "../../unrelated.csv"
        for base in (self.root / "data", self.root / "dist/data"):
            (base / "current.json").write_bytes(p.encoded(pointer))
        with self.assertRaisesRegex(p.PipelineError, "Invalid current csv"):
            p.current_exports(self.root)

    def test_interrupted_immutable_write_leaves_no_destination(self):
        path = self.root / "atomic.json"
        with patch.object(p.os, "link", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                p.immutable_write(path, b"complete payload")
        self.assertFalse(path.exists())
        self.assertFalse(list(self.root.glob(".immutable-*")))

    def test_future_analysis_date_rejected_before_fetch(self):
        future = datetime.now(timezone.utc).date() + timedelta(days=1)
        with self.assertRaisesRegex(p.PipelineError, "future"):
            p.refresh(self.root, future, fetcher=lambda url: self.fail("future request"))

    def test_immutable_files_cannot_be_rewritten(self):
        path = self.root / "immutable.json"
        p.immutable_write(path, b"first")
        with self.assertRaisesRegex(p.PipelineError, "Immutable"):
            p.immutable_write(path, b"second")
        self.assertEqual(path.read_bytes(), b"first")


if __name__ == "__main__":
    unittest.main()
