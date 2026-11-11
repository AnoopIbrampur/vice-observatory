# Phase 2 analysis protocol · v1

Written before computing Phase 2 results. This is a fixed retrospective evaluation protocol, not a prospective prediction record and not an external preregistration. Historical outcomes already exist. The local protocol commit precedes implementation and result generation; all of it will be public at the Phase 2 checkpoint.

## Inputs and provenance

Analyze the verified Phase 1 manifest and exact-title daily observations. Do not refetch data, change event dates, merge aliases, select comparisons based on performance, or change normalization after seeing results. Generated outputs must identify the source snapshot and the digest of this protocol. No parameter tuning or learned model is involved.

## Descriptive calculations

- Daily views: the recorded count for one UTC date. Missing dates are missing, never zero.
- Trailing 7-day mean at date t: mean of the seven calendar dates t-6 through t, only if all seven exist. It includes t because it describes observed attention, not a forecast.
- Complete-week change: compare the latest seven observed consecutive calendar dates with the immediately preceding seven. Compute `(recent_sum - prior_sum) / prior_sum * 100`. Return unavailable when either week is incomplete or the prior sum is zero. These are rolling complete 7-day blocks, not Monday–Sunday weeks.
- Peak: maximum daily count within the stated observed interval. Return every tied peak date; do not invent a unique winner.
- Event windows: mean of days -7 through -1 versus days 0 through +6 relative to the event. Require complete windows; otherwise report unavailable with observed/expected day counts. Scheduled events remain unobserved even if the calendar later passes their date, until evidence verifies occurrence. Event changes are descriptive associations, not causal estimates.

## Release-aligned comparisons

- Plot days -90 through +90, inclusive, relative to each series' versioned release date.
- Preserve raw views and a daily index of `100 * views / baseline_mean`.
- Baseline mean: all 21 calendar dates -28 through -8, inclusive. Require all 21 dates and a positive mean. Missing/zero baseline means the index is unavailable, not infinite or zero-filled.
- The index is a retrospective descriptive transformation. For points earlier than day -8, the normalizer can contain later observations; it is not a point-in-time feature and must never be used in forecasting evaluation. Record the baseline end date and availability explicitly.
- Represent each requested alignment date with its observation or null and an explicit state. Future dates, dates outside acquired coverage, and missing historical observations are different states. Do not fill or extrapolate GTA VI's launch/post-launch curve.
- A scheduled release retains that label. GTA V 2022 remains a console re-release and may be hidden by a future original-launch-only UI control; it is never relabeled as the 2013 release.
- Raw totals and indices measure different quantities. Comparing indices does not identify which title had the largest audience, sales, or player base.

## Forecast benchmark

Question: how well do two fixed, simple methods predict the next day's pageviews around historical launches?

Expansion protocol (2026-11-11), fixed before acquiring the added histories: include all 19 configured historical released series. GTA VI is excluded because its launch window is not observed. The GTA V re-release is included and labeled separately.

- Evaluation targets: release-relative days -14 through +30 inclusive, exactly 45 per complete historical series.
- Before the evaluation interval, source dates -90 through -15 supply past context. No future target or post-launch value may enter a prediction for an earlier date.
- Yesterday baseline for target t: observed pageviews on t-1.
- Trailing-week baseline for target t: mean observed pageviews on t-7 through t-1. This excludes the target date, unlike the descriptive trailing mean.
- Both methods must use the same target dates. Include a target only when the target and all preceding seven calendar dates exist. Report exclusions and expected counts; never silently vary denominators by model.
- Primary score: mean absolute error (MAE), in pageviews/day, separately for each game and method. Do not round predictions before scoring.
- Secondary scale-normalized score: total absolute error divided by total actual views (WAPE). Zero total actual views makes it unavailable. This is a scale-adjusted diagnostic, not accuracy or confidence.
- Report aggregate pooled MAE with its scale limitation and a macro-average WAPE giving each game equal weight. Do not declare a universal winner from a pooled number alone.
- Report three fixed regimes: pre-launch (-14 to -1), launch days (0 to +2), and post-launch (+3 to +30). They use the same prediction rows as the full window.
- No significance claim or generalization to unseen game launches is supported by this purposive cohort. Post-launch observations are retrospectively evaluated, never prospective evidence.

## Validation and publication

Use small independently calculated examples, missing-date and zero-denominator cases, alignment boundary checks, future-mutation tests proving earlier predictions stay unchanged, and deterministic export replay. Re-read and verify Phase 1 provenance before analysis. Outputs include JSON, per-day prediction CSV, release-aligned CSV, a generated findings/benchmark report, and a versioned analysis pointer. Analysis pointers must identify their source snapshot; a data refresh makes previous analysis stale until explicitly regenerated.

Do not mark Phase 2 complete until tests pass, outputs reproduce exactly, documented calculations match an independent check, and the checkpoint is pushed to the same public repository.
