# Expansion release protocol

## Scope and phases
1. Freeze a 20-series cohort and audit exact article identities before pageview acquisition.
2. Collect complete histories; retain the existing -28..-8 index and -14..+30 benchmark unchanged. Add original-only and re-release scoring groups.
3. Expand the sourced event explorer with search, kind/status filters, and explicit window coverage.
4. Publish daily through GitHub Actions/Pages at 12:23 UTC; validate in isolation, retain the last good snapshot on failure, and show refresh history. The existing Sites demo reads the same published immutable snapshots, with an explicit bundled fallback.
5. Run offline tests, browser checks, cloud publication and anonymous readback; push all source to public GitHub.

## Cohort selection before added data acquisition
Purposive, source-verifiable, large console/PC games from 2017–2023: retain the original three historical examples, add 16 well-known Nintendo, Sony and Bandai Namco launches with official publisher date evidence and available English article identities. GTA VI is the unscored scheduled target. No popularity ranking, statistical sampling or representative-market claim is made. No outcome-based exclusions or parameter tuning. Entire added candidate list is in config/series.json. Collection failure withholds publication rather than silently dropping a title. Original releases and the retained GTA V re-release are labeled and scored separately. Horizon Zero Dawn uses the North American first-release date.

## Title audit boundary
Current canonical identity, page creation timestamp, incoming redirects, and visible title-filtered move logs are preserved with response hashes. These do not reconstruct all historical names, deleted logs or every move chain. Exact-title histories stay separate; aliases are not added together or treated as unique readers. A complete requested date window is not proof of complete game-attention coverage.
