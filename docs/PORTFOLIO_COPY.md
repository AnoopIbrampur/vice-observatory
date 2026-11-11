# Portfolio and interview copy

The live demo is now public and recruiter-accessible at https://vice-observatory-anoop.poeticskink11.chatgpt.site. The repository and case study are also public. No scheduled updates are active.

## Portfolio card

**Vice Observatory — GTA VI launch-attention analytics**

A source-linked dashboard exploring how attention changes around major game launches. Preserves real Wikimedia observations, aligns historical release windows, and evaluates next-day baselines without future-data leakage. Ships with reproducible exports, browser integrity checks, and two-version CI.

**Evidence:** 1,649 observations in the initial snapshot · 135 retrospective benchmark targets · 79 passing tests.

**Stack:** Python · JavaScript · SVG · GitHub Actions.

**Links:** [live demo](https://vice-observatory-anoop.poeticskink11.chatgpt.site) · [case study](https://github.com/AnoopIbrampur/vice-observatory/blob/main/docs/CASE_STUDY.md) · [source](https://github.com/AnoopIbrampur/vice-observatory)

For a shorter stack label, use “Python · JavaScript · GitHub Actions.” Do not add SQL, a trained ML model, or a database to the stack: none was used.

## Résumé bullets

- Built a GTA VI launch-attention dashboard over 1,649 public Wikimedia observations, with immutable source provenance, release-aligned comparisons, accessible data tables, and CSV/JSON exports.
- Evaluated two past-only forecasting baselines on 135 historical targets; shipped 79 tests and Python 3.11/3.13 CI, resolving a cross-version floating-point issue that broke deterministic replay.

The counts refer to the November 11, 2026 release snapshot. Update them only after a verified data/analysis refresh. If space allows only one bullet, use the first and link the case study.

## Ownership and AI assistance

Project owner: Anoop Ibrampur. Implementation was AI-assisted with Codex. Present the technical decisions, public verification evidence, and limitations clearly; avoid implying that a model was trained, users were studied, or telemetry was collected when those activities did not occur.

## A 45-second project explanation

“I wanted to turn GTA VI launch discussion into something measurable, so I created an observatory around daily Wikipedia article views. The interesting part was making the evidence inspectable: preserved raw inputs, explicit missing/future values, a fixed comparison baseline, and a browser that checks source and analysis versions before displaying numbers. I compared yesterday's count with a trailing-week predictor on three historical releases; yesterday was better overall, but I kept the regime where that wasn't true. CI also caught a Python-version difference in floating-point totals, which led to a more reproducible calculation.”

## Questions worth being able to answer

- **Why pageviews?** Free historical access and reproducibility. They are an attention proxy, not unique people, sales, players, or sentiment.
- **Why is GTA VI's indexed curve unavailable at first?** The fixed baseline needs 21 dates; only 20 were observed at the cutoff. Changing the baseline after seeing the gap would change the comparison.
- **How is leakage prevented?** A forecast for day t uses t-1 or t-7 through t-1. The descriptive trailing mean includes t and is kept separate. Tests mutate future outcomes and check earlier forecasts.
- **Why not add an LLM?** The core tasks are collection, validation, transparent arithmetic, and visualization. Paid inference adds neither a necessary data source nor a better-evidenced conclusion here.
- **What did CI catch?** Different float accumulation between Python versions, fixed with accurate summation and a regression example.
- **What is still limited?** Exact-title history, three selected comparisons, the re-release/original distinction, retrospective evaluation, and no scheduled refresh.
