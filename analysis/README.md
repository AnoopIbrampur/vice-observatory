# Derived analysis

Start with `current.json`. Resolve entries in its `files` object relative to this directory. The pointer contains the analysis ID and the exact source snapshot ID.

Each immutable snapshot includes:

- `manifest.json`: source snapshot, protocol hash, implementation hash, and fixed analysis windows.
- `analysis.json`: complete daily statistics, aligned comparisons, event-window results, and retrospective benchmark scores.
- `comparisons.csv`: 181 release-relative dates per game with explicit observed/missing/future states and optional indices.
- `predictions.csv`: one row per scored historical target with context dates, both predictions, actual views, and errors.
- `findings.md`: generated human-readable report.
- `protocol.md`: the exact protocol used for this analysis version.

Recompute with `python3 -m scripts.analysis build`; verify byte-identical reproduction with `python3 -m scripts.analysis verify`. Run from the repository root. Neither command needs network access or a paid API. All source data remains attributed to Wikimedia under CC0; derived counts describe article attention, not players or sales.

Current-day and future observations are excluded. A missing index means the fixed normalizer is incomplete or zero; it must not be shown as an index value of zero. The normalization is descriptive and retrospective; only raw past observations enter the forecasting benchmark.
