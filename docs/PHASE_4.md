# Phase 4 verification report

Completed: 2026-11-11. This phase adds release reliability, real GitHub CI, an isolated manual-refresh workflow, and broader browser verification. Production deployment remains Phase 5.

## Delivered

- Read-only GitHub CI for pushes, pull requests, and manual dispatch, testing Python 3.11 and 3.13 with Node 22.
- Official Actions pinned to verified full commit SHAs, with checkout credentials not persisted.
- An offline release gate verifying source/analysis replay, all ten versioned download files, HTML targets, local startup dependencies, recorded contrast pairs, and payload budgets.
- A loopback HTTP smoke test verifying 17 served assets/downloads, including all ten snapshot file hashes.
- A manual refresh workflow that collects and validates in an isolated directory, then uploads a candidate artifact. It has no repository write permission and does not push or deploy.
- Additional guards for download paths and version association, plus a 15-second browser-request timeout.
- More visible interactive-control borders and scroll spacing for keyboard focus.
- Local-only outage/tamper/stale fixtures that alter HTTP responses without altering saved project files. They are not included in the deployed `dist/` bundle.

## Automated results

All **79 unit tests** pass: 64 Python and 15 Node tests. Syntax checks, offline release verification, and HTTP smoke verification pass independently.

Verified GitHub runs:

- [Two-version CI success](https://github.com/AnoopIbrampur/vice-observatory/actions/runs/43059519440): both Python 3.11 / Node 22 and Python 3.13 / Node 22 completed successfully on the fixed implementation.
- [Manual refresh success](https://github.com/AnoopIbrampur/vice-observatory/actions/runs/43059772528): the current pinned Actions collected, validated, and uploaded a candidate successfully.

The candidate was downloaded and independently replayed locally against the same implementation. Its source ID was `71dfd78e1d02baf55d7af20b59e887b7704cc599b824056fb65084562d0e091b`; its analysis ID was `d5e88e1af1b5a1be736ea3a86d4df268ab0ac3fe4a3fe4b45680baaa666eb3b7`. It was deliberately not applied to main or deployed. The public dashboard source still uses source snapshot `73ecfa4562de20fb39627963ab85f8e2cf666ba825697af6c90de454f5590415`.

## A real CI finding and fix

The first matrix run passed on Python 3.13 but failed byte-identical analysis verification on Python 3.11. Python changed floating-point `sum` accumulation in 3.12, exposing tiny differences in absolute-error totals. The analysis now uses `math.fsum` for floating error totals and exact integer addition for integer totals. A large/small-magnitude regression case guards the fix.

This changed the analysis implementation identity, so a new immutable analysis snapshot was built: `6b1e954c561eab1a0afc35bf0263190402603838f8a240e05791ee9d3b73f970`. Prior snapshots remain intact. The generated human-readable findings report is byte-identical to Phase 2's report; no analysis windows, normalization rules, outcome selection, or displayed conclusions changed. Both supported Python versions now verify the same current artifacts.

## Browser results

- A deliberate HTTP 503 showed an error and withheld the dashboard. Retry reproduced the visible error without rendering partial numbers.
- A deliberately changed payload failed SHA-256 validation; a deliberately mismatched analysis pointer showed a source/analysis mismatch. Both withheld the dashboard.
- Returning to the valid URL restored the real charts and cleared the error state.
- Home/arrow-key inspection updated the selected date. Tab reached the observation-table summary, and Space opened its 30-row table. After scrolling settled, focus was visible at approximately y=524, below the sticky header's y=91 lower edge in a 900-pixel viewport.
- The copy-view button displayed successful “View link copied” feedback. Clipboard contents were not read.
- Full-history / mean-only mode produced 1,106 data-table rows. Indexed comparison preserved the explicit GTA VI 20/21-baseline notice.
- Clearing every selected release produced the explicit empty message and zero chart paths. Restoring selections restored the valid chart.
- The 375-pixel mobile layout, including the open table, had no document-level horizontal overflow. Phase 3's desktop/small-phone/landscape checks remain documented separately.
- The browser parsed the `prefers-reduced-motion: reduce` block disabling smooth scrolling and transitions. The available browser tools did not expose media emulation, and the user's operating-system preference was not changed. This verifies rule acceptance, not a forced-preference or screen-reader audit.
- Screenshots: [keyboard-visible chart/table](screenshots/phase-4-keyboard.jpg) and [integrity error state](screenshots/phase-4-integrity-error.jpg).

## Payload and contrast evidence

The release gate measured **559,978 raw startup bytes** across nine expected startup requests including the favicon. Estimated gzip size is **69,096 bytes**; this is an estimate, not a claim that the local server or eventual host enables compression. The budgets are 1.2 MB raw and 300 KB estimated gzip. No external runtime scripts, fonts, chart libraries, or API requests are required to load a saved snapshot. No Lighthouse or browser-timing score is claimed.

Recorded text contrast against the panel background is 15.25:1 for primary text, 8.98:1 for muted text, and 6.08:1 for dim text. Signal colors exceed 8:1. The old control border was approximately 2.04:1; the new border is 3.38:1 against the control surface. These are checks of the specified pairs and basic keyboard behavior, not a complete accessibility conformance claim.

See the machine-readable [release-gate evidence](verification/phase-4-release.json) and [workflow operations](WORKFLOWS.md).

## Completion boundary

The source and analysis are verified, CI has actually run successfully, manual refresh has actually produced and preserved a validated artifact, and browser failure/keyboard states have been inspected. There is no schedule, automatic push, production deployment, or complete assistive-technology audit implied by this phase. Phase 5 publishes the verified application and completes the portfolio package.
