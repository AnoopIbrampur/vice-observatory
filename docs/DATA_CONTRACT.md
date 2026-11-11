# Data contract · v1

## Source

Endpoint: `https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/all-access/user/{article}/daily/{start}/{end}`.

Request dates are inclusive, formatted `YYYYMMDD00`. Observations represent UTC calendar days. Daily records use ISO `YYYY-MM-DD`. Fetch timestamps are UTC ISO timestamps, separate from the caller-selected analysis date.

Only dates strictly before the analysis date may be requested or published. Initial analysis date: 2026-11-11. The most recent requested day is 2026-11-10. This is a cutoff, not a guarantee of source publication: incomplete coverage must fail validation and preserve the preceding valid dataset.

## Validated records

Each row has `series_id`, `article`, `project`, `date`, `views`, `access`, `agent`, and `granularity`. The source API returns project `en.wikipedia` for requests to `en.wikipedia.org`; only this documented normalization is accepted.

Require the exact requested article, daily granularity, all-access, user agent category, a valid midnight timestamp, nonnegative integer views (booleans are invalid), unique dates, no dates outside the requested window, and exactly one observation per expected day. An empty response is invalid for the configured populated windows. Missing values are never converted to zero.

Configuration requires unique safe series identifiers, valid chronological windows, HTTPS evidence links, and known release kinds/statuses. The collector does not silently resolve redirects, merge title histories, or advance scheduled releases to occurred.

## Provenance and publication

Raw responses are content-addressed with SHA-256, paired with an acquisition receipt containing request URL, requested interval, fetch timestamp, HTTP status, selected non-sensitive response headers, byte count, and payload hash. The versioned dataset manifest references each receipt and its exact raw payload. Offline replay verifies hashes and rebuilds exports without accessing the network.

Fetch and validate the entire configured bundle before publishing. Store each bundle in an immutable snapshot directory identified by the manifest hash. Publish the active pointer and canonical browser dataset with atomic replacement. Snapshot-specific JSON/CSV are immutable; a failed refresh keeps the previous pointer and browser dataset. A local status file records the last attempt separately from the last successful observation. Atomic individual file replacement is not a transactional filesystem-wide update; consumers use the immutable snapshot files referenced by the pointer.

Browser dataset schema: `schema_version`, `as_of`, `collected_at`, `source`, `manifest_sha256`, `events`, `series`, and `health`. Each series contains its definition, request interval, source references, and validated observations. Phase 1 contains observations and health only; derived analytics arrive in Phase 2.

## Limits

English Wikipedia pageviews are an imperfect attention proxy, not unique readers or game usage. `agent=user` excludes requests Wikimedia identifies as bots but does not prove a human behind every request. Exact-title histories may omit requests to earlier titles or redirects; title changes can produce discontinuities. The data can be revised and publisher release dates can change. Historical re-downloads are new acquisitions, never edits to prior raw snapshots.
