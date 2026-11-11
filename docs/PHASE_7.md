# Phase 7 — Portfolio integration and event investigations

## Scope
Accepted in chat: feature Vice Observatory on the existing portfolio and implement a source-linked event investigation. No paid APIs.

## Delivery phases
1. Add event selection, 29-day context, fixed before/after summaries, source evidence, nearby events and shareable investigation links. Preserve backend scoring rules and incomplete/scheduled exclusions.
2. Add a featured portfolio card, screenshot and project case study with a responsive architecture diagram and explicit methodological limits. Preserve the existing portfolio design.
3. Run offline checks and browser QA for complete, incomplete, scheduled, unknown and historical events. Push both public repositories, publish GitHub Pages and the existing public Site, then verify the live pages.

## Implementation
The browser derives a 29-calendar-day context from the already verified analysis payload. It reuses the backend event result for percentage changes and never recomputes or relaxes the seven-day windows. Missing, out-of-coverage and future dates remain null. Every event has a shareable investigation link; overlapping catalogued events link to their own investigations. The panel stays in document flow, moves keyboard focus to its heading when opened, supports browser history, and returns focus to the event or filter when closed.

The portfolio feature links directly into the launch-trailer investigation and a dedicated case study. The case study includes a responsive four-stage architecture diagram, operational fallback behavior, retrospective benchmark results, source/redirect limitations, and AI-assisted implementation attribution. No prospective forecasting claim is added.

## Verification
95 offline tests passed (67 Python, 28 JavaScript), including event calendar windows, unknown IDs, future/null/zero distinctions, scheduled and incomplete exclusions, nearby-event selection, and query-state round trips. The release gate and 21-asset HTTP smoke passed. Local browser QA verified complete, incomplete, scheduled and unknown investigations; link opening with Enter; heading/return focus; copy-link feedback; and portfolio/card/architecture layouts at desktop and 375px widths. Mobile gutters use whole pixels, and versioned module/CSS URLs avoid combining cached code across releases. Cloud publication/readback will be recorded after deployment.
