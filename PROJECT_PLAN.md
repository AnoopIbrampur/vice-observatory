# Vice Observatory — project plan

Status: Phases 0 and 1 complete. Source audit and reproducible data foundation are implemented; analysis and dashboard phases remain. See `docs/PHASES.md` for checkpoints and `docs/PHASE_1.md` for verification evidence.

## Objective

Build a polished, reproducible GTA VI launch-attention observatory that Anoop can delegate to Codex and confidently explain to employers. A visitor should be able to see how attention changes around verified announcements, compare launch windows, inspect the underlying observations, and understand the limits of each conclusion.

The core requires no paid API, no API key, and no gameplay recordings. Codex owns research, implementation, tests, analysis, documentation, and deployment preparation. Anoop owns product direction and final portfolio positioning. External account access or a request to change the publication audience may require Anoop's involvement.

## Product boundaries

The primary measured signal is daily English Wikipedia article pageviews, with Wikimedia's user agent category and all access types. This is an attention proxy. It is not unique people, sales, player counts, sentiment, or evidence that an announcement caused a spike. It does not fully remove automated traffic.

The first release includes:

- GTA VI attention explorer with date ranges, daily observations, a trailing average, verified event annotations, and accessible underlying data.
- Historical launch comparison, aligned by days relative to the relevant release and shown in both raw and normalized units.
- Source-linked event timeline distinguishing announcement dates from the launch dates they describe, and scheduled events from observed events.
- A small set of derived descriptive findings, each backed by an explicit calculation and sample window.
- Data health, last-observed and last-fetched timestamps, stale-data states, source provenance, and CSV/JSON export.
- Methodology, a portfolio case study, an architecture diagram, reproducible scripts, meaningful tests, and a deployment-ready static site.

Excluded from the first release: paid social APIs, Reddit scraping, universal social sentiment, sales forecasts, a chatbot, account creation, user tracking, gameplay capture, and speculative predictions trained on one launch. Additional sources must first pass the source audit rather than becoming promises in the interface.

## Proposed architecture

Use a small, static HTML/CSS/JavaScript application and a Python standard-library data pipeline. This avoids a hosted database, paid inference, a backend service, and unnecessary deployment dependencies. Render interactive charts with accessible SVG, semantic controls, and tabular equivalents.

Flow: Wikimedia endpoints → preserved raw response and request metadata → validated daily observations → derived statistics and evaluation → compact site JSON/CSV → static dashboard.

Keep analysis functions separate from networking and presentation. Store source definitions and verified events as versioned data. A refresh command should write outputs atomically only after validation succeeds; a failed fetch must preserve the last valid snapshot and report its age.

Directory structure:

```text
dist/                  deployable site and compact published data
scripts/               collection, validation, analysis, export
tests/                 calculation, ingestion, and regression tests
docs/                  methodology, source audit, case study, decisions
data/raw/              immutable fetched snapshots and provenance
data/processed/        validated records and analysis outputs
.github/workflows/     reproducible CI and manually dispatched refresh
.openai/hosting.json   private Site identity and static output configuration
```

Raw-data storage size and repository placement will be decided after the historical fetch. Do not put credentials or the attached résumé into the project.

## Phase 0 — scope and source feasibility

Work:

1. Record the product scope, zero-paid-API constraint, and decisions in project documentation.
2. Check Wikimedia's current access policy, attribution requirements, coverage, publication lag, and rate limits.
3. Probe the GTA VI series and candidate historical comparisons. Confirm article names, redirects, date continuity, and endpoint semantics.
4. Verify event dates against primary publisher sources. Build a source registry with URLs, date checked, and event status.
5. Select comparisons only when the data supports them. Candidates are GTA V's March 2022 console re-release, Red Dead Redemption 2's October 2018 launch, and Cyberpunk 2077's December 2020 launch. Explicitly distinguish a re-release from an original launch. GTA V's 2013 launch predates the pageview API's expected coverage and must not be represented with invented history.

Deliverables: source audit, approved data schema, event registry, and final first-release specification.

Complete when: a real sample is validated for every included series; source access and limitations are documented; unsupported comparisons are removed or explicitly unavailable.

Current evidence: a 41-day GTA VI response for October 1–November 10, 2026 was retrieved successfully. This establishes initial access, not completeness of all proposed history. An empty static project and private Site registration also exist.

## Phase 1 — reproducible data foundation

Work:

1. Implement bounded downloads, a descriptive User-Agent, timeouts, polite retries for transient failures, and rate-limit handling.
2. Save raw payloads with request URL, UTC fetch time, response metadata when available, and content checksum.
3. Validate article identity, date parsing, nonnegative integer counts, duplicate dates, completeness, and future-date exclusion. Missing observations remain missing; they never silently become zero.
4. Fetch enough GTA VI history for relevant announcement windows and fixed historical launch windows for comparisons.
5. Generate normalized daily records, a data-health report, and compact public JSON/CSV.

Deliverables: working collection command, real datasets, provenance manifest, validation report, and ingestion tests.

Complete when: another run can reproduce derived outputs from preserved inputs; rerunning is safe; partial or malformed responses cannot overwrite valid data; published dates and coverage agree with the source.

## Phase 2 — analysis and evaluation

Work:

1. Define daily views, trailing 7-day mean, complete-week percentage change, and peak day with explicit handling of missing data and zero denominators.
2. Align comparison series on each verified release date. Offer absolute pageviews and an index where the fixed pre-launch baseline is 100.
3. Fix the normalization baseline before inspecting comparative results: candidate baseline is mean views on days -28 through -8, requiring full coverage and a positive mean. Document any necessary change before interpreting results.
4. Show only observed dates for GTA VI. Leave its future launch/post-launch region empty and labeled; never extrapolate an apparent observed curve.
5. Describe event-window changes without claiming causation. Document page-title changes, differing audience sizes, release types, and platform effects.
6. Evaluate a modest statistical question: on held-out historical dates, how well do yesterday's views and a trailing-week mean predict next-day attention? Use past-only inputs, a chronological split, MAE, and per-game results. Hold this benchmark separate from descriptive charts. If neither method is useful around launches, report that finding rather than add an unearned ML claim.

Deliverables: analysis functions, independently checked example calculations, descriptive findings, and a benchmark report with date ranges and failure cases.

Complete when: every displayed number is reproducible; future observations cannot affect earlier features; historical results are separated from GTA VI's not-yet-observed launch outcomes; comparisons carry appropriate caveats.

## Phase 3 — dashboard and interaction

Work:

1. Establish a dark editorial visual system with restrained pink/cyan accents, clear typography, and readable chart labels. Use original design rather than copied Rockstar artwork.
2. Build the overview with source freshness, available coverage, latest complete daily value, and complete-week change.
3. Build the attention explorer with ranges, daily/average controls, verified event annotations, keyboard-operable inspection, and an equivalent data table.
4. Build launch comparison with series selection, raw/indexed views, an explained baseline, and visible missing/future regions.
5. Add the event timeline, methodology, data health, downloads, and an author/case-study link.
6. Persist shareable selections in URL parameters, with safe defaults for invalid input.

Deliverables: complete responsive application using real pipeline outputs, design notes, and screenshots.

Complete when: each control works; charts and tables match; links and downloads resolve; date and timezone labels are unambiguous; keyboard users can obtain the same information as pointer users; there is no fabricated activity, decorative fake telemetry, or unsupported live badge.

## Phase 4 — reliability and release verification

Work:

1. Test data invariants, normalization, rolling windows, date alignment, missing dates, zero denominators, future-date handling, and malformed fetches.
2. Verify key interactions in a browser, including shareable URLs, comparison controls, downloads, and error/empty states.
3. Inspect desktop and narrow mobile layouts, keyboard focus, contrast, reduced motion, and horizontal overflow.
4. Measure payload sizes and basic loading behavior. Keep routine use independent of third-party runtime requests by shipping a valid snapshot.
5. Add CI checks and a manually dispatched refresh workflow. A daily schedule is a separate optional operating decision; an unused workflow is not described as an active automated service.
6. Record the actual refresh/deployment path. Refreshing repository data alone must not be described as refreshing the hosted Site unless that publication step is connected and verified.

Deliverables: test results, browser QA notes, verified screenshots, CI configuration, and operating instructions.

Complete when: checks pass; browser inspection reveals no material layout or interaction defects; freshness accurately describes the deployed snapshot; failures preserve valid data and remain visible.

## Phase 5 — deployment and portfolio package

Work:

1. Publish the verified site privately through the registered Sites project, preserve its audience, and confirm successful deployment.
2. Prepare a portable source archive with clear local-run, refresh, test, and deployment instructions. Keep Sites-specific state identifiable so the project can also move to GitHub Pages.
3. Write the case study: question, audience, architecture, data quality problems, evaluation, results, trade-offs, limitations, and next steps.
4. Prepare a concise portfolio card and résumé bullet using actual measured results, with a short explanation Anoop can use in interviews.
5. Document how to make the site recruiter-accessible. A private deployment is a review artifact; public access or adding it to the existing portfolio is a separate audience/content change and will not be silently assumed.

Deliverables: working private URL, source archive, case study, architecture diagram, screenshots, and suggested portfolio copy.

Complete when: deployment is confirmed; source runs from documented commands; case-study numbers match pipeline results; access limitations and any remaining operating steps are explicit.

## Execution and review rhythm

Work sequentially through these phases, sharing findings and phase completion in chat. Source feasibility and correct analysis precede visual claims. Do not require Anoop to write code, collect gameplay, label clips, or administer a paid service. Ask only when a real product choice, missing external access, or audience decision blocks dependent work; continue independent authorized work where possible.

The initial release is finished when an employer can open the intended shareable version, understand its question, interact with real data, inspect the evidence, and reproduce the analysis. The first private release is ready for review before that public-sharing step.
