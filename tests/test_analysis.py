"""Independent arithmetic, leakage checks, missing-date handling, and replay."""

from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import analysis as a
from scripts import pipeline as p
from test_pipeline import fixture, response


RELEASE = date(2020, 6, 1)


def sample_series(released=True):
    series = {
        "id": "sample", "label": "Sample", "article": "Sample", "release_date": RELEASE.isoformat(),
        "release_kind": "original_launch", "release_status": "released" if released else "scheduled", "notes": "Synthetic test fixture.",
    }
    values = {RELEASE + timedelta(days=i): 100 + i for i in range(-90, 91)}
    return series, values


class ArithmeticTests(unittest.TestCase):
    def test_hand_calculated_rolling_week_change(self):
        values = {date(2020, 1, i): i for i in range(1, 15)}
        result = a.summary(values)
        self.assertEqual(result["trailing_7_day_mean"], 11)
        self.assertEqual(result["week_change"]["recent"]["total_views"], 77)
        self.assertEqual(result["week_change"]["previous"]["total_views"], 28)
        self.assertEqual(result["week_change"]["percent"], 175)

    def test_window_requires_calendar_dates_not_last_seven_rows(self):
        values = {date(2020, 1, i): i for i in range(1, 15) if i != 10}
        result = a.summary(values)
        self.assertIsNone(result["trailing_7_day_mean"])
        self.assertEqual(result["week_change"]["status"], "incomplete")
        self.assertIsNone(result["week_change"]["percent"])

    def test_zero_denominators_are_unavailable(self):
        values = {date(2020, 1, i): 0 for i in range(1, 15)}
        result = a.summary(values)
        self.assertEqual(result["trailing_7_day_mean"], 0)
        self.assertEqual(result["week_change"]["status"], "zero_baseline")
        self.assertIsNone(result["week_change"]["percent"])
        self.assertIsNone(a.percent_change(10, 0))

    def test_all_peak_ties_retained(self):
        result = a.summary({date(2020, 1, 1): 50, date(2020, 1, 2): 50, date(2020, 1, 3): 0})
        self.assertEqual(result["peak"], {"views": 50, "dates": ["2020-01-01", "2020-01-02"]})

    def test_event_hand_calculation_and_noncausal_label(self):
        values = {RELEASE + timedelta(days=i): 10 if i < 0 else 25 for i in range(-7, 7)}
        event = {"date": RELEASE.isoformat(), "status": "occurred"}
        result = a.event_result(event, values)
        self.assertEqual(result["before"]["mean_views"], 10)
        self.assertEqual(result["after"]["mean_views"], 25)
        self.assertEqual(result["percent_change"], 150)
        self.assertIn("does not establish causation", result["interpretation"])

    def test_scheduled_event_never_auto_promoted_even_with_full_windows(self):
        _, values = sample_series()
        result = a.event_result({"date": RELEASE.isoformat(), "status": "scheduled"}, values)
        self.assertEqual(result["analysis_status"], "scheduled")
        self.assertIsNone(result["percent_change"])

    def test_partial_event_window_reports_counts_and_no_effect(self):
        _, values = sample_series()
        values.pop(RELEASE + timedelta(days=3))
        result = a.event_result({"date": RELEASE.isoformat(), "status": "occurred"}, values)
        self.assertEqual(result["after"]["observed_days"], 6)
        self.assertEqual(result["analysis_status"], "incomplete")
        self.assertIsNone(result["percent_change"])


class ComparisonTests(unittest.TestCase):
    def test_fixed_21_day_normalizer_hand_calculation(self):
        series, values = sample_series()
        result = a.aligned_series(series, values, RELEASE + timedelta(days=91))
        # The arithmetic sequence 72..92 has mean 82.
        self.assertEqual(result["baseline"]["mean_views"], 82)
        self.assertEqual(result["baseline"]["observed_days"], 21)
        self.assertEqual(len(result["points"]), 181)
        launch = result["points"][90]
        self.assertEqual(launch["relative_day"], 0)
        self.assertEqual(launch["date"], RELEASE.isoformat())
        self.assertAlmostEqual(launch["index_100"], 10000 / 82)

    def test_twenty_of_twenty_one_baseline_days_is_unavailable(self):
        series, values = sample_series(released=False)
        as_of = RELEASE - timedelta(days=8)
        values = {day: count for day, count in values.items() if day < as_of}
        result = a.aligned_series(series, values, as_of)
        self.assertEqual(result["baseline"]["observed_days"], 20)
        self.assertEqual(result["baseline"]["status"], "incomplete")
        self.assertTrue(all(point["index_100"] is None for point in result["points"]))
        self.assertTrue(all(point["views"] is None for point in result["points"] if point["state"] == "future"))
        self.assertEqual(sum(point["state"] == "future" for point in result["points"]), 99)

    def test_zero_baseline_never_yields_infinity(self):
        series, values = sample_series()
        for relative in range(-28, -7):
            values[RELEASE + timedelta(days=relative)] = 0
        result = a.aligned_series(series, values, RELEASE + timedelta(days=91))
        self.assertEqual(result["baseline"]["status"], "zero_baseline")
        self.assertTrue(all(point["index_100"] is None for point in result["points"]))

    def test_missing_and_outside_coverage_are_different_from_future(self):
        series, values = sample_series()
        values.pop(RELEASE)
        values.pop(RELEASE - timedelta(days=90))
        result = a.aligned_series(series, values, RELEASE + timedelta(days=91))
        self.assertEqual(result["points"][0]["state"], "outside_coverage")
        self.assertEqual(result["points"][90]["state"], "missing")
        self.assertEqual(result["points"][-1]["state"], "observed")


class ForecastTests(unittest.TestCase):
    def test_linear_series_independently_calculated_mae_and_wape(self):
        series, values = sample_series()
        rows, excluded = a.predictions(series, values, RELEASE + timedelta(days=91))
        self.assertEqual(len(rows), 45)
        self.assertEqual(excluded, [])
        result = a.score(rows)
        # Values 86..130 average 108; previous day errs by 1, previous week by 4.
        self.assertEqual(result["actual_views_total"], 4860)
        self.assertEqual(result["methods"]["yesterday"]["mae"], 1)
        self.assertEqual(result["methods"]["trailing_week"]["mae"], 4)
        self.assertAlmostEqual(result["methods"]["yesterday"]["wape"], 1 / 108)
        self.assertAlmostEqual(result["methods"]["trailing_week"]["wape"], 4 / 108)

    def test_future_mutation_does_not_change_earlier_predictions(self):
        series, values = sample_series()
        original, _ = a.predictions(series, values, RELEASE + timedelta(days=91))
        changed = deepcopy(values)
        changed[RELEASE + timedelta(days=20)] = 1000000
        modified, _ = a.predictions(series, changed, RELEASE + timedelta(days=91))
        self.assertEqual([row for row in original if row["relative_day"] < 20], [row for row in modified if row["relative_day"] < 20])
        for left, right in zip(original, modified):
            if left["relative_day"] == 20:
                self.assertEqual(left["yesterday"], right["yesterday"])
                self.assertEqual(left["trailing_week"], right["trailing_week"])
                self.assertNotEqual(left["actual_views"], right["actual_views"])

    def test_missing_context_excludes_same_targets_for_both_methods(self):
        series, values = sample_series()
        values.pop(RELEASE)
        rows, excluded = a.predictions(series, values, RELEASE + timedelta(days=91))
        self.assertEqual([row["relative_day"] for row in excluded], list(range(0, 8)))
        self.assertEqual(len(rows), 37)
        self.assertTrue(all("yesterday" in row and "trailing_week" in row for row in rows))

    def test_forecast_context_strictly_precedes_target(self):
        series, values = sample_series()
        rows, _ = a.predictions(series, values, RELEASE + timedelta(days=91))
        for row in rows:
            self.assertLess(row["context_end"], row["date"])
            self.assertEqual((p.parse_day(row["date"]) - p.parse_day(row["context_end"])).days, 1)

    def test_regimes_and_scheduled_release_exclusion(self):
        series, values = sample_series()
        scheduled = {**series, "id": "future", "release_status": "scheduled"}
        report, rows = a.benchmark([series, scheduled], {"sample": values, "future": values}, RELEASE + timedelta(days=91))
        self.assertEqual(len(report["series"]), 1)
        regimes = report["series"][0]["regimes"]
        self.assertEqual([regimes[key]["scored_days"] for key in ["pre_launch", "launch_days", "post_launch"]], [14, 3, 28])
        self.assertEqual(report["excluded_series"][0]["series_id"], "future")
        self.assertEqual(report["pooled"]["scored_days"], 45)

    def test_zero_actual_totals_and_empty_scores_are_explicit(self):
        series, values = sample_series()
        values = {day: 0 for day in values}
        report, _ = a.benchmark([series], {series["id"]: values}, RELEASE + timedelta(days=91))
        self.assertIsNone(report["macro_average"]["yesterday"]["wape"])
        self.assertEqual(report["series"][0]["lowest_mae_method"], "tie")
        self.assertIsNone(a.score([])["methods"]["yesterday"]["mae"])

    def test_macro_metric_weights_games_equally(self):
        first, values = sample_series()
        second = {**first, "id": "b"}
        other = {day: count * 100 for day, count in values.items()}
        report, _ = a.benchmark([first, second], {"sample": values, "b": other}, RELEASE + timedelta(days=91))
        self.assertAlmostEqual(report["macro_average"]["yesterday"]["wape"], 1 / 108)
        self.assertEqual(report["pooled"]["methods"]["yesterday"]["mae"], 50.5)

    def test_observation_guard_rejects_future_duplicates_and_boolean_counts(self):
        for rows in [
            [{"date": "2020-01-04", "views": 1}],
            [{"date": "2020-01-01", "views": 1}, {"date": "2020-01-01", "views": 1}],
            [{"date": "2020-01-01", "views": True}],
        ]:
            with self.subTest(rows=rows), self.assertRaises(p.PipelineError):
                a.observations({"observations": rows}, date(2020, 1, 4))


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        config, events, self.payload = fixture()
        (self.root / "config").mkdir()
        (self.root / "docs").mkdir()
        (self.root / "config/series.json").write_bytes(p.encoded(config))
        (self.root / "config/events.json").write_bytes(p.encoded(events))
        (self.root / "docs/ANALYSIS_PROTOCOL.md").write_text("Synthetic test protocol.\n")
        p.refresh(self.root, date(2020, 1, 4), fetcher=lambda _: response(self.payload))

    def test_build_is_deterministic_and_verifies_without_network(self):
        with patch.object(p, "fetch", side_effect=AssertionError("Unexpected network")):
            first = a.run(self.root)
            second = a.run(self.root)
            self.assertEqual(first, second)
            self.assertEqual(a.run(self.root, verify=True), first)
        parsed = json.loads((self.root / "analysis" / first["files"]["analysis.json"]).read_bytes())
        self.assertEqual(parsed["source_snapshot_id"], first["source_snapshot_id"])
        self.assertEqual(parsed["benchmark"]["excluded_series"][0]["series_id"], "sample")

    def test_changed_protocol_requires_new_analysis_and_preserves_old_snapshot(self):
        original = a.run(self.root)
        (self.root / "docs/ANALYSIS_PROTOCOL.md").write_text("Changed test protocol.\n")
        with self.assertRaises((OSError, p.PipelineError)):
            a.run(self.root, verify=True)
        rebuilt = a.run(self.root)
        self.assertNotEqual(original["analysis_id"], rebuilt["analysis_id"])
        self.assertTrue((self.root / "analysis" / original["files"]["analysis.json"]).exists())

    def test_source_tampering_stops_analysis_before_publication(self):
        a.run(self.root)
        pointer = (self.root / "analysis/current.json").read_bytes()
        next((self.root / "data/raw").glob("*.json")).write_bytes(b"{}")
        with self.assertRaisesRegex(p.PipelineError, "Checksum"):
            a.run(self.root)
        self.assertEqual((self.root / "analysis/current.json").read_bytes(), pointer)

    def test_new_source_snapshot_marks_previous_analysis_stale(self):
        original = a.run(self.root)
        fourth = {**self.payload["items"][-1], "timestamp": "2020010400", "views": 120}
        self.payload["items"].append(fourth)
        p.refresh(self.root, date(2020, 1, 5), fetcher=lambda _: response(self.payload))
        with self.assertRaises((OSError, p.PipelineError)):
            a.run(self.root, verify=True)
        rebuilt = a.run(self.root)
        self.assertNotEqual(original["source_snapshot_id"], rebuilt["source_snapshot_id"])
        self.assertNotEqual(original["analysis_id"], rebuilt["analysis_id"])
        self.assertEqual(a.run(self.root, verify=True), rebuilt)

    def test_public_prediction_tampering_is_detected(self):
        pointer = a.run(self.root)
        path = self.root / "dist/analysis" / pointer["files"]["predictions.csv"]
        path.write_bytes(b"tampered")
        with self.assertRaisesRegex(p.PipelineError, "differs"):
            a.run(self.root, verify=True)


if __name__ == "__main__":
    unittest.main()
