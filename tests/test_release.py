"""Release contracts, isolated failure handling, and local fault fixtures."""

from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import check_release as r
from scripts import pipeline as p
from scripts import qa_server as q
from scripts import refresh_candidate as c


class ReleaseTests(unittest.TestCase):
    def test_text_and_control_contrast_independently_known_examples(self):
        self.assertEqual(r.contrast("#000000", "#ffffff"), 21)
        self.assertEqual(r.contrast("#ffffff", "#ffffff"), 1)
        self.assertGreater(r.contrast("#607782", "#1b232a"), 3)
        self.assertLess(r.contrast("#46545e", "#1b232a"), 3)

    def test_html_duplicate_ids_and_unresolved_labels_detectable(self):
        page = r.Page()
        page.feed('<label for="missing">X</label><div id="a"></div><div id="a"></div>')
        self.assertEqual(page.duplicate_ids, ["a"])
        self.assertEqual(set(page.labels) - page.ids, {"missing"})

    def test_download_reference_rejects_traversal(self):
        pointer = p.read_json(p.ROOT / "data/current.json")
        self.assertEqual(len(r.pointer_files(pointer)), 4)
        pointer["csv"] = "../../private.csv"
        with self.assertRaisesRegex(p.PipelineError, "Unsafe"):
            r.pointer_files(pointer)

    def test_analysis_reference_requires_every_expected_file(self):
        pointer = p.read_json(p.ROOT / "analysis/current.json")
        pointer["files"].pop("predictions.csv")
        with self.assertRaisesRegex(p.PipelineError, "missing expected"):
            r.pointer_files(pointer, True)

    def test_local_qa_scenarios_do_not_change_original_bytes(self):
        body = b'{"source_snapshot_id":"original"}'
        self.assertEqual(q.fault("missing", "/data/current.json", body)[0], 503)
        status, changed = q.fault("tampered", "/data/snapshots/hash/dataset.json", body)
        self.assertEqual(status, 200)
        self.assertNotEqual(p.digest(changed), p.digest(body))
        status, stale = q.fault("stale", "/analysis/current.json", body)
        self.assertEqual(json.loads(stale)["source_snapshot_id"], "0" * 64)
        self.assertEqual(body, b'{"source_snapshot_id":"original"}')

    def test_qa_fault_does_not_affect_other_assets(self):
        self.assertEqual(q.fault("missing", "/app.mjs", b"code"), (200, b"code"))


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.root = self.parent / "source"
        for folder in ("scripts", "config", "docs", "dist", "data", "analysis"):
            (self.root / folder).mkdir(parents=True)
        self.sentinel = self.root / "data/current.json"
        self.sentinel.write_text('"original source"')

    def test_failure_leaves_source_unchanged_and_no_candidate(self):
        output = self.parent / "candidate"
        with patch.object(p, "refresh", side_effect=p.PipelineError("source unavailable")):
            with self.assertRaisesRegex(p.PipelineError, "unavailable"):
                c.create(self.root, output, date(2026, 11, 11))
        self.assertEqual(self.sentinel.read_text(), '"original source"')
        self.assertFalse(output.exists())
        self.assertFalse(list(self.parent.glob("vice-candidate-*")))

    def test_existing_output_is_never_overwritten(self):
        output = self.parent / "candidate"
        output.mkdir()
        (output / "keep.txt").write_text("keep")
        with self.assertRaisesRegex(p.PipelineError, "already exists"):
            c.create(self.root, output, date(2026, 11, 11))
        self.assertEqual((output / "keep.txt").read_text(), "keep")

    def test_output_inside_source_checkout_is_rejected(self):
        with self.assertRaisesRegex(p.PipelineError, "outside"):
            c.create(self.root, self.root / "candidate", date(2026, 11, 11))

    def test_untrusted_date_never_reaches_shell_or_collector(self):
        with patch.object(p, "refresh") as acquire:
            with self.assertRaises(p.PipelineError):
                p.parse_day("2026-11-11; touch /tmp/should-not-exist")
            acquire.assert_not_called()


if __name__ == "__main__":
    unittest.main()
