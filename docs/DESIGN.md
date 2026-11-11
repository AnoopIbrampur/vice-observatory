# Dashboard design

Direction: a dark editorial observatory, with ink surfaces, warm white typography, a pink GTA VI signal, and mint/violet/gold comparison accents. Original typography and CSS orbital artwork avoid depending on copied game assets, remote imagery, fonts, or API keys.

The UI/UX skill's initial gaming search favored a 3D marketing showcase, which did not fit the analytical task. A narrower dashboard search supported restrained surfaces and filtering; the final editorial direction is project-specific design judgment. Its chart guidance supported line charts, distinct patterns, and tabular alternatives. No marketing conversion flows or ornamental 3D dependencies were adopted.

## Hierarchy

1. Overview: saved-snapshot identity, latest complete daily count, trailing mean, complete-week change, and schedule-relative date context.
2. Attention explorer: visible date and series controls, responsive SVG axes, a keyboard/pointer date inspector, source event annotations, and the same observations in a table.
3. Comparisons: explicit raw/index units, release selectors, an original-launch filter, baseline availability, release-relative axes, and a full table including null future observations.
4. Timeline: publisher evidence, distinct scheduled/observed status, and descriptive event-window changes.
5. Method and exports: the benchmark's limitations, coverage, snapshot identities, and portable data.

## Interaction and accessibility decisions

- Native labeled selects and checkboxes; no custom menu implementation.
- A native slider exposes inspected values via `aria-valuetext`; arrow keys and Home reach dates without using a chart pointer.
- Chart series have distinct dash patterns as well as colors. Patterns are repeated beside release selectors. Charts include titles/descriptions and adjacent expandable tables.
- The SVG coordinate system adapts to available width, retaining readable axis text on small screens. Long-history date axes include years.
- Shareable query parameters preserve selected ranges, measures, releases, event filters, and comparison scale; invalid parameters fall back safely.
- Missing or future values break chart paths. Incomplete indices and zero denominators are unavailable, never zero-filled.
- Visible keyboard focus, a skip link, reduced-motion CSS, native expandable details, and scrollable tables support basic keyboard access. This is not a claim of full accessibility conformance or a substitute for assistive-technology testing in Phase 4.
- SHA-256 validation and source/analysis identity checks occur before display. Errors withhold the dashboard and offer retry/source access.
- Snapshot dates are explicit. The page does not describe saved observations as a live feed, and its scheduled-launch interval is labeled relative to the snapshot date.

## Runtime

Buildless static HTML, CSS, and browser ES modules. No package installation, external chart library, paid API, analytics tracker, or hosted backend is needed. The browser requests only local static assets and saved JSON. HTTPS or localhost is required for Web Crypto and loading modules; opening `index.html` directly with `file://` is unsupported.
