# Phase 6 — Expanded, unattended observatory

Completed 2026-11-11. No paid API keys.

- 20 exact-title series, including GTA VI and 19 historical releases; 4,545 real daily observations at the verified checkpoint. The expanded cohort/protocol was committed before added acquisition.
- 855 identical target dates across the two past-only baselines; 810 original-launch and 45 console-re-release targets reported separately. Equal-game WAPE: 19.5% yesterday versus 42.4% trailing-week. Purposive retrospective cohort; no unseen-launch performance claim.
- 26 source-linked events, searchable by text, title, event type and status. Exact window coverage and verification notes are visible, including Trailer 1 date disagreement. Shareable filters and a four-release comparison limit keep charts readable.
- Bounded title audit preserves current canonical page IDs, creation timestamps, incoming redirects and title-filtered move logs. GTA VI move warnings and Spider-Man's deliberate launch-era title/redirect are visible. Logs are not complete page-ID move chains; aliases are not merged.
- Daily GitHub Actions publication scheduled at 12:23 UTC. Isolated acquisition, matching data/analysis checkpoint, full checks, bot commit, Pages deployment and public hash readback are implemented. Failed acquisition retains the active source/analysis pointers and publishes an explicit attempt record; failed deployment retains the previous live artifact.
- Sites consumes the same public GitHub Pages checkpoint, with a verified bundled fallback and visible fallback notice. A post-deployment browser check proved the Sites app loaded cloud snapshot c2fd5742df7a1944f244a586bff8192a6952ba8041c438526c75b1b95fc34fe0 while its bundled snapshot was 3dc86465b32d1ae3d2c121d0502cbfd29b940b124143a543701c605a55e85600.

## Verification

88 tests passed (67 Python, 21 JavaScript). CI passed on Python 3.11/3.13 and Node 22: https://github.com/AnoopIbrampur/vice-observatory/actions/runs/43066759801

Initial publish succeeded: https://github.com/AnoopIbrampur/vice-observatory/actions/runs/43066759815

Actual unattended refresh, bot push, deployment and anonymous readback succeeded: https://github.com/AnoopIbrampur/vice-observatory/actions/runs/43066862434

The writer path was exercised immediately, without waiting for the next scheduled run. The saved schedule itself is enabled in the main-branch workflow; GitHub may delay scheduled runs.

10 public download hashes and the title audit were independently verified without authentication. Browser QA covered 20 release choices, rejection of a fifth selection with guidance, adding a different title, event intersections/empty states, restored shared filters, and responsive desktop/mobile layouts. The payload gate allows 2.5 MB raw / 300 KB estimated gzip after the cohort expansion; measured startup is about 1.91 MB raw / 220 KB estimated gzip across nine normal startup requests. Offline HTTP smoke now checks 20 assets/downloads.

## Public deployment

- Main demo: https://vice-observatory-anoop.poeticskink11.chatgpt.site
- Daily publication and mirror: https://anoopibrampur.github.io/vice-observatory/
- Sites version: appgprj_6af416aed3948191bfe69c871154b0bb~appgver_41127598d1088191a5b1f09a7a404ffc
- Sites deployment: appgdep_6af4a3b0b250819183a45381b72607c2

Existing phase tags and intermediate immutable snapshots are preserved. Events remain manually verified; a scheduled release never becomes an occurred event just because a date passes. Automatic refreshes refetch historical histories as well as GTA VI, so long-term archive growth remains an operational limitation.
