# Data operations

## Expansion release: current operating path

The daily publication now runs in `.github/workflows/publish.yml` at **12:23 UTC**, on main pushes (publish only), and manual dispatch (refresh by default). GitHub may delay scheduled runs. Pages is enabled with the Actions publishing source. No user-supplied API key or paid service is needed.

An isolated candidate collects source data and the bounded MediaWiki title audit, rebuilds analysis, records a checkpoint and passes the release gate. Only then are artifacts overlaid, tested on the workflow runner, committed and uploaded to Pages. Acquisition failure records `failed_retained_last_good` with unchanged active source/analysis pointers; the last good data and failure record can still deploy, and the workflow ends failed to surface the problem. A later test, commit or deployment failure leaves the previous live artifact in place. Push races fail safely instead of force-pushing.

`dist/publication.json` is a single checkpoint containing both immutable pointers, the title-audit checksum and the last 30 attempt records. The browser verifies the matching bundle before rendering. The public Sites demo reads this checkpoint from GitHub Pages, including all matching downloads. If retrieval or integrity checks fail, it shows its complete bundled snapshot with an explicit fallback notice. A runtime fallback never silently mixes remote and local data. Code/UI updates still require a Sites deployment.

Manual current refresh: `python3 -m scripts.publication refresh`. Rebuild without acquisition: analysis build → publication record → check_release. Changing the audit or either pointer requires regenerating the publication checkpoint. Automated tests and `python -m scripts.verify_publication <public-base-url>` verify published download hashes. Use Actions run status to distinguish validated attempts from successful deployments.

All 20 pageview histories are currently refetched daily, including fixed historical windows, to retain fresh acquisition evidence. This increases immutable archive size over time; monitor repository growth before long-term use. Events are manually verified source entries and are not inferred to have occurred merely because a scheduled date passed. No automatic news ingestion or prospective ML claim is made.

The sections below preserve the initial release workflow where relevant.


## Local dashboard

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory dist
```

Open `http://127.0.0.1:8765/`. The buildless browser application reads only same-origin static snapshots; use HTTPS or localhost for Web Crypto. It verifies dataset/analysis SHA-256 values and matching source identities before display. Source/analysis mismatches or failed requests show an error rather than a partially populated dashboard.

The dashboard provides a saved view, not a live feed. Its query parameters preserve ranges and comparison filters; invalid values receive safe defaults. A pending 20/21-day GTA VI baseline is an explicit unavailable index, while raw data remains selectable.

Frontend checks use Node 22+ with no installed packages: `node --test tests/dashboard.test.mjs`. Browser QA and screenshots are documented in the phase reports. The verified owner-only production deployment and portable hosting instructions are in [DEPLOYMENT.md](DEPLOYMENT.md).

## Requirements and entry points

Use Python 3.11+ and curl. Run commands from the repository root. There are no pip dependencies, API keys, or paid services. Acquisition requires network access to Wikimedia; tests, verification, and replay do not.

```sh
python3 -m scripts.pipeline refresh --as-of 2026-11-11
python3 -m scripts.pipeline verify
python3 -m scripts.pipeline replay --output /tmp/vice-observatory-replay
python3 -m unittest discover -s tests -v
```

An analysis date sets the cutoff: only earlier UTC days are requested. Backfills are allowed; future analysis dates are rejected. Omitting `--as-of` selects the current UTC date, which may differ from a user's local date near midnight.

## What refresh does

1. Validate configured sources and evidence links, and obtain a single-writer lock.
2. Request each of the four Wikimedia histories sequentially with a project-identifying User-Agent.
3. Preserve exact raw response bytes and an acquisition receipt with SHA-256 hashes.
4. Require the complete requested daily interval and exact dimensions for every series.
5. Re-read preserved inputs, verify provenance, and build JSON, CSV, and a coverage report.
6. Write immutable snapshot files before replacing either active pointer atomically.
7. Record a local success/failure status and release the lock.

The first release re-downloads four small histories rather than implementing premature incremental merging. A repeated response reuses the same raw content hash; each acquisition retains its own receipt. Fetching twice can create different snapshot IDs because acquisition timestamps differ. Offline replay of one manifest is deterministic and produces identical bytes.

`data/current.json` serves pipeline consumers and `dist/data/current.json` serves the future browser app. Resolve pointer paths relative to their respective directories. Each pointer references a complete immutable version. The two pointer replacements are individually atomic, not a distributed transaction: a process interruption between them can leave different valid versions. `verify` detects this mismatch. A subsequent successful refresh republishes matching pointers.

Raw files and receipts include only public API responses and selected non-sensitive response headers. `.openai/`, credentials, and local attempt status are excluded from Git.

## Failure behavior

- Missing dates, duplicate rows, invalid timestamps, changed dimensions, malformed JSON, and non-integer/negative counts fail validation. Missing dates are never replaced with zeros.
- HTTP 429 and selected transient server failures retry at most twice. Retry-After seconds and dates are respected. Delays over 60 seconds stop the command instead of retrying too early. Authentication, blocking, and certificate errors are not bypassed.
- A failed acquisition or validation does not replace active dataset pointers. Preserved partial acquisitions can remain for diagnosis; they are not a published successful bundle.
- `data/status.json` records the latest local attempt. It is ignored by Git because it can contain machine-specific errors. It must not be confused with the last successful dataset's `health.json`.
- A hard process termination can leave `data/.refresh.lock`. Before removing this one lock file, confirm no collector is still running. No automatic stale-lock deletion is performed.
- If Wikimedia has not published yesterday yet, the strict refresh fails. Retry after source publication or explicitly choose an earlier analysis date; do not relabel old observations as current.
- If a checksum fails, preserve the affected file for inspection. Restore a known-good version from Git or fetch a new valid snapshot. Do not edit checksums to suppress the failure.

## Verification and replay

`verify` rebuilds all exports from the current manifest's exact preserved sources, checks payload and receipt hashes, validates the observations again, and compares regenerated bytes with both stored copies. A replay never calls the API. `replay --output ...` additionally writes the four regenerated files into a separate directory without overwriting different existing content.

## Refresh is separate from deployment

### Rebuild analysis after a successful data refresh

```sh
python3 -m scripts.pipeline verify
python3 -m scripts.analysis build
python3 -m scripts.analysis verify
```

Analysis is an offline step over the exact verified source snapshot. `analysis/current.json` and `dist/analysis/current.json` identify the analysis version and its `source_snapshot_id`. A source refresh, protocol edit, or analysis-code edit requires rebuilding; `scripts.analysis verify` detects stale or altered artifacts. The dashboard must also compare source IDs before displaying derived numbers.

Analysis exports include complete daily statistics, release-aligned comparison records, every historical benchmark prediction, full-precision scores, the generated findings report, and the exact protocol. `docs/FINDINGS.md` is a readable copy of the generated report and is verified too. Never edit the generated report to change a result; change a justified rule in the protocol, document the reason, and rebuild. Historical analysis snapshots remain immutable.

The fixed normalization baseline can be incomplete even when source coverage is complete: GTA VI needs all 21 dates from release-relative day -28 through -8. As of the initial November 11 snapshot, only 20 are observed. Leave the index unavailable until all required source observations exist. This is distinct from an ingestion failure.

Refreshing local data changes files only. Pushing them updates the public source repository and runs CI; deployment is still a separate explicit operation. The [manual refresh workflow](WORKFLOWS.md) has been tested on GitHub and emits an isolated validated candidate artifact. No cron job or scheduled refresh is active. Phase 5's owner-only deployment is recorded in [DEPLOYMENT.md](DEPLOYMENT.md).

Keep public GitHub phase commits/tags separate from private Site publication. The existing `.openai/hosting.json` is local deployment identity, not a secret and not part of this public source checkpoint.
