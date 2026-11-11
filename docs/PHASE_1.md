# Phase 1 verification report

Completed: 2026-11-11. Analysis cutoff: 2026-11-11, excluding that UTC day. All observations are real Wikimedia API responses; no generated data is mixed into the published datasets. Synthetic examples exist only in tests.

## Delivered

- Standard-library Python collector using system curl with certificate verification, sequential requests, bounded retries, and rate-limit handling.
- Versioned source and event definitions, strict per-day validation, raw payload preservation, SHA-256 acquisition receipts, and immutable snapshot manifests.
- Validated CSV and JSON exports plus a per-series completeness report.
- Publication through atomic active-pointer replacement after all sources validate.
- Offline verification and byte-identical export replay.
- 29 passing tests covering contract violations, tampering, safe retries, interrupted writes, and failed-refresh preservation.

## Collected data

| Series | First day | Last day | Observations | Missing days in requested window |
| --- | --- | --- | ---: | ---: |
| GTA VI | 2023-11-01 | 2026-11-10 | 1,106 | 0 |
| GTA V · 2022 console re-release | 2021-12-15 | 2022-06-13 | 181 | 0 |
| Red Dead Redemption 2 | 2018-07-28 | 2019-01-24 | 181 | 0 |
| Cyberpunk 2077 | 2020-09-11 | 2021-03-10 | 181 | 0 |
| **Total** | | | **1,649** | **0** |

Initial manifest SHA-256:

```text
73ecfa4562de20fb39627963ab85f8e2cf666ba825697af6c90de454f5590415
```

The browser-ready dataset is 137,442 bytes in this snapshot. Daily view data is CC0, provided by Wikimedia. Complete requested coverage is a data-integrity property; it does not prove comprehensive attention measurement or historical title coverage.

## Verification actually run

```sh
python3 -m unittest discover -s tests -v
python3 -m scripts.pipeline verify
python3 -m scripts.pipeline replay --output <separate-directory>
```

Outcome: all 29 tests passed. `verify` re-read the preserved payloads and receipts without network access. The offline-replayed manifest, dataset, CSV, and health report matched the committed snapshot byte for byte. CSV record count independently checked against the JSON health total: 1,649.

Fault-injection tests establish that an unavailable later series, an empty response, or an HTML error page cannot replace preceding valid active pointers; raw or public CSV tampering is detected; an interrupted immutable write does not leave a partial destination; a requested future analysis date is rejected; and an existing collector lock is respected.

## Remaining limits

- No dashboard, derived trend statistics, forecast results, hosted deployment, or scheduled refresh is claimed in Phase 1.
- Exact Wikipedia article titles are used. Earlier aliases and redirects have not been merged; the source audit explains why early GTA VI observations need caution.
- GTA V's comparison is a console re-release, not the original 2013 launch. Pageviews are not platform-specific.
- As of the cutoff, GTA VI's launch date remains scheduled. No launch-day or later observation is present.
- Source publication can lag. A later failed refresh preserves valid data but does not make it fresh; operating notes explain the distinction.

Next phase: implement and evaluate descriptive statistics and release-aligned comparisons under the fixed, past-only analysis rules.
