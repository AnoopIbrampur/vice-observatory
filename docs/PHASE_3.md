# Phase 3 verification report

Completed: 2026-11-11. The dashboard uses the unchanged, verified Phase 1 source and Phase 2 analysis snapshots. This phase delivers the static application; production publication remains Phase 5.

## Delivered

- Original dark editorial design, responsive layout, and locally rendered vector artwork.
- GTA VI daily/mean explorer with 30/90/365-day and full-history filters, verified event annotations, keyboard/pointer date inspection, and a matching data table.
- Indexed/raw release comparison, individual release selection, original-launch filtering, explicit incomplete-baseline states, and a complete aligned data table.
- GTA VI/all-release timeline, publisher links, schedule status, and qualified event-window changes.
- Methodology, actual benchmark results, coverage and freshness information, source/analysis identities, and snapshot-specific CSV/JSON/findings downloads.
- Shareable URL state and a copy-link button with a manual-copy fallback.
- Browser SHA-256 checks and stale-analysis protection before any observations are displayed; visible loading/error states.

## Automated verification

```sh
node --check dist/app.mjs
node --check dist/model.mjs
node --test tests/dashboard.test.mjs
python3 -m unittest discover -s tests
python3 -m scripts.pipeline verify
python3 -m scripts.analysis verify
```

All **65 tests** pass: 53 Python data/analysis tests and 12 Node dashboard tests. JavaScript syntax checks and the two provenance/replay verifications also pass. Dashboard tests cover invalid URL state, empty selection round trips, calendar filtering, original/re-release selection, incomplete indices, null path breaks, HTML escaping and safe evidence URLs, real snapshot integrity, tampered payload rejection, source/analysis mismatch, unsafe snapshot paths, and failed HTTP requests.

Node 22+ is used for the built-in test runner and Web Crypto tests. Running the dashboard itself requires only a modern browser and a static HTTP server.

## Browser verification actually performed

Local static preview returned HTTP 200 and loaded the real dashboard successfully.

- Selecting “Last 30 days” produced exactly 30 observation-table rows and updated the URL.
- A keyboard left-arrow action moved inspection from November 10 to November 9, with the displayed count changing from 64,375 to 43,270.
- Switching to raw comparison and enabling original launches removed GTA V's re-release from the plotted lines and disabled its selector while preserving the saved selection.
- A shared full-history / mean-only / no-release / all-events URL restored 1,106 observation rows, five timeline events, and the explicit empty comparison message.
- Home on the date slider selected November 1, 2023. Its unavailable trailing mean was labeled and the chart marker was hidden rather than drawn at zero.
- The observations CSV link downloaded successfully through the browser.
- Desktop (1440×1000), mobile (375×812), small phone (320×740), and landscape (812×375) layouts were inspected. No document-level horizontal overflow was detected at these sizes. The explicit viewport override was reset afterward.
- Saved final desktop and mobile screenshots are in [screenshots](screenshots/). They are verification artifacts, not synthetic mockups.

## Known boundaries

No production URL, active scheduled refresh, automated browser CI, or comprehensive accessibility audit is claimed. Reduced-motion behavior is implemented in CSS; separate screen-reader/device testing remains useful. Clipboard-write success was not independently asserted; the manual-copy fallback is provided. Only the observations download was exercised as a browser download; all download links point to the versioned files already verified by the data/analysis tooling.

Next: Phase 4 broadens reliability checks and adds CI/operating workflows. Phase 5 publishes the site and packages the portfolio case study.
