# Vice Observatory

An independent GTA VI launch-attention observatory, built from public Wikimedia pageviews and source-linked publisher announcements. No paid APIs or API keys.

**Status:** Phases 0 and 1 complete: source audit and reproducible data foundation. **1,649 actual daily observations across four series**, with preserved raw responses, checksummed acquisition receipts, CSV/JSON exports, and offline replay. The dashboard is not implemented or publicly deployed yet. Follow [phase checkpoints](docs/PHASES.md) for actual progress.

## The question

How does attention change around GTA VI announcements and launch, and how does its launch window compare with other major releases?

The measured signal is daily **English Wikipedia article pageviews**, not sales, unique people, sentiment, or active players. Event annotations describe timing; they do not establish causation. Future GTA VI launch outcomes remain unobserved.

## What is planned

- An interactive attention explorer with daily values, trailing averages, verified event annotations, and accessible data tables.
- Release-aligned historical comparisons in raw and indexed units.
- Downloadable data, source provenance, freshness reporting, and reproducible analysis.
- An evaluation of simple past-only forecasting baselines, including failures.

See the [full project plan](PROJECT_PLAN.md), [source audit](docs/SOURCE_AUDIT.md), [data contract](docs/DATA_CONTRACT.md), and [Phase 1 verification report](docs/PHASE_1.md).

## Run and reproduce

Requirements: **Python 3.11+** and **curl** on your PATH. No pip packages, API keys, account, or paid services are required. curl uses verified TLS and your system's certificate trust store.

```sh
git clone https://github.com/AnoopIbrampur/vice-observatory.git
cd vice-observatory

# Tests run without network access; test data is synthetic and clearly isolated.
python3 -m unittest discover -s tests -v

# Verify the committed real-data snapshot without network access.
python3 -m scripts.pipeline verify

# Rebuild identical JSON/CSV from preserved responses into a separate directory.
python3 -m scripts.pipeline replay --output /tmp/vice-observatory-replay

# Optional: acquire a new snapshot using real network requests.
python3 -m scripts.pipeline refresh --as-of 2026-11-11
```

Without `--as-of`, refresh uses the current UTC date and requests only earlier days. A recent day may not yet be published by Wikimedia; incomplete source responses fail rather than filling gaps with zero. See [operations](docs/OPERATIONS.md) for failure recovery and refresh behavior.

## Inspect the data

[`data/current.json`](data/current.json) is the current version pointer. Its `dataset`, `csv`, `health`, and `manifest` fields resolve relative to `data/`. Each references an immutable snapshot directory. Browser-ready copies are in `dist/data/`; they are ready for the dashboard, not an already-deployed application.

- `data/raw/`: exact Wikimedia response bytes, named by SHA-256.
- `data/receipts/`: request URLs, requested intervals, acquisition times, selected response headers, and payload checksums.
- `data/snapshots/`: versioned manifest, validated dataset, CSV, and coverage report.
- `config/`: explicit article identities, release dates, source evidence, and event status.
- `scripts/pipeline.py`: collection, validation, atomic publication, and offline replay.
- `tests/`: fault injection and end-to-end checks for provenance and safe publication.

Initial snapshot: GTA VI from November 1, 2023 through November 10, 2026 (1,106 days), and 181-day historical windows for GTA V's 2022 console re-release, Red Dead Redemption 2, and Cyberpunk 2077. No GTA VI launch-day or post-launch observation is fabricated.

No scheduled refresh or automatic hosted-site deployment has been enabled. Phase 4 will document and verify the operating workflow.

## Sources and credit

Pageviews are provided by the [Wikimedia Analytics API](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/), whose data is available under CC0 1.0. Code is MIT-licensed. Publisher announcements are linked as evidence; their text and artwork are not republished as project assets. This is an independent portfolio project by [Anoop Ibrampur](https://anoopibrampur.github.io/), unaffiliated with Rockstar Games, Take-Two Interactive, CD PROJEKT RED, or Wikimedia.
