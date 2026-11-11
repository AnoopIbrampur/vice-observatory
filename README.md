# Vice Observatory

An independent GTA VI launch-attention observatory, built from public Wikimedia pageviews and source-linked publisher announcements. No paid APIs or API keys.

**Status:** Phase 0 complete: scope and source feasibility. The dashboard is not implemented or publicly deployed yet. Follow [phase checkpoints](docs/PHASES.md) for actual progress.

## The question

How does attention change around GTA VI announcements and launch, and how does its launch window compare with other major releases?

The measured signal is daily **English Wikipedia article pageviews**, not sales, unique people, sentiment, or active players. Event annotations describe timing; they do not establish causation. Future GTA VI launch outcomes remain unobserved.

## What is planned

- An interactive attention explorer with daily values, trailing averages, verified event annotations, and accessible data tables.
- Release-aligned historical comparisons in raw and indexed units.
- Downloadable data, source provenance, freshness reporting, and reproducible analysis.
- An evaluation of simple past-only forecasting baselines, including failures.

See the [full project plan](PROJECT_PLAN.md), [source audit](docs/SOURCE_AUDIT.md), and [data contract](docs/DATA_CONTRACT.md).

## Sources and credit

Pageviews are provided by the [Wikimedia Analytics API](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/), whose data is available under CC0 1.0. Code is MIT-licensed. Publisher announcements are linked as evidence; their text and artwork are not republished as project assets. This is an independent portfolio project by [Anoop Ibrampur](https://anoopibrampur.github.io/), unaffiliated with Rockstar Games, Take-Two Interactive, CD PROJEKT RED, or Wikimedia.
