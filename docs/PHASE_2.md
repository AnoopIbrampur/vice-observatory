# Phase 2 verification report

Completed: 2026-11-11. Input: the unchanged, verified Phase 1 snapshot. No fresh API requests or paid services were needed.

## Delivered

- Calendar-based daily and trailing-week attention statistics, complete-week changes, tied-peak handling, and source-linked event windows.
- 181 release-aligned dates per series (724 total), with raw counts, fixed-baseline indices when available, and distinct missing/out-of-coverage/future states.
- A fixed retrospective next-day benchmark on 45 targets per historical release, 135 targets total. Both methods see only preceding observations and use identical evaluation targets.
- Full per-game MAE and WAPE, equal-game macro WAPE, pooled scores, and fixed pre-launch / launch-days / post-launch breakdowns.
- Reproducible JSON, comparison CSV, prediction CSV, findings report, and exact protocol bytes, published through source-linked immutable analysis snapshots.

## Protocol and provenance

The [analysis protocol](ANALYSIS_PROTOCOL.md) was committed in `6dcb9fa` before analysis implementation or results were generated. It is a fixed retrospective protocol, not an external preregistration or a prediction made before historical outcomes existed.

The normalization mean uses exactly release-relative days -28 through -8. Evaluation targets are exactly -14 through +30. Yesterday uses t-1, and trailing-week uses t-7 through t-1. No parameters were tuned or learned. The index is a retrospective descriptive transformation and is excluded from forecasting inputs.

Each analysis manifest identifies its source snapshot, protocol hash, and implementation hash. The current analysis ID is:

```text
668d329664b5b808625ac6b919068f8003305363ca414f01195178b1d1718507
```

The source snapshot remains:

```text
73ecfa4562de20fb39627963ab85f8e2cf666ba825697af6c90de454f5590415
```

## Verification actually run

```sh
python3 -m unittest discover -s tests -v
python3 -m scripts.pipeline verify
python3 -m scripts.analysis build
python3 -m scripts.analysis verify
```

All **53 tests** pass: the existing 29 ingestion/provenance tests plus 24 analysis tests. Analysis verification recomputes every artifact without network access and compares bytes, including the report and both pipeline/browser copies. Repeated builds produce the same analysis ID and identical exports.

Analysis tests cover independently calculated rolling means and percentage changes, missing calendar dates, zero denominators, tied peaks, scheduled-event preservation, normalization boundaries, zero/missing baselines, null future dates, hand-calculated forecast errors, target exclusions, macro weighting, source/protocol changes, output tampering, and mutation of future outcomes without changing earlier forecasts.

An additional independent check used CSV source records and 40-digit Decimal arithmetic rather than the analysis functions. It reconstructed **all 135 predictions**, recomputed per-game MAE to an absolute tolerance of 1e-9, and checked GTA VI's weekly totals and null launch/post-launch values. The recent week totals 250,621 views; the previous week totals 149,783; the calculated change is 67.3227268782% before display rounding.

## Results and implications

The [generated findings report](FINDINGS.md) contains full scores and event-window associations. Yesterday-only prediction has lower overall MAE for all three historical releases. Equal-game macro WAPE is 17.0% for yesterday versus 32.4% for trailing-week; those are error ratios, not accuracy percentages. The trailing-week method does better during GTA V's three-day re-release regime, which the report preserves rather than hiding behind the overall result.

GTA VI's normalization baseline is only 20/21 observed dates at the saved cutoff. Its indexed curve is correctly unavailable; no alternative baseline was selected to force a result. Raw observations remain available. All 99 future dates in its -90 to +90 comparison window have null observations. Its scheduled launch is excluded from the retrospective forecasting benchmark.

## Remaining work

Phase 3 will turn these verified outputs into the responsive dashboard and accessible chart interactions. No website, automated refresh, causal effect, prospective forecast, or sales prediction is claimed by this checkpoint. The three selected historical windows and exact-title traffic limits still constrain interpretation.
