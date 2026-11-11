# Phase checkpoints

One public repository is used for the entire project. Each completed phase gets a descriptive commit and an annotated `phase-N` tag; future phases are not marked complete in advance.

| Phase | Status | Evidence |
| --- | --- | --- |
| 0 · Scope and source feasibility | Complete | Four real source probes, source audit, versioned source/event registry, data contract |
| 1 · Reproducible data foundation | Complete | 1,649 real observations, raw payloads and receipts, atomic publication, byte-identical offline replay, 29 passing tests; [verification](PHASE_1.md) |
| 2 · Analysis and evaluation | Complete | Fixed protocol, 724 aligned points, 135 scored targets, 53 passing tests, deterministic analysis replay; [verification](PHASE_2.md), [findings](FINDINGS.md) |
| 3 · Dashboard and interaction | Complete | Responsive dashboard, keyboard inspection, shared views, downloads, browser QA, 65 passing tests; [verification](PHASE_3.md) |
| 4 · Reliability and release verification | Complete | 79 tests, passing two-version GitHub CI, validated cloud refresh artifact, HTTP/integrity/contrast/keyboard checks; [verification](PHASE_4.md) |
| 5 · Deployment and portfolio package | Complete | Confirmed owner-only deployment, hosted case study, portable archives, architecture and portfolio copy; [verification](PHASE_5.md) |

The dashboard at https://vice-observatory-anoop.poeticskink11.chatgpt.site is now public following an explicit audience-change request after Phase 5. Anonymous access and data hashes were verified. Phase reports and original release archives retain the history of the initial owner-only deployment.

Public repository: https://github.com/AnoopIbrampur/vice-observatory

Completed phase tags: `phase-0`, `phase-1`, `phase-2`, `phase-3`, `phase-4`, `phase-5`. A new repository is not created for each phase; checkpoints preserve the history of this one project.

## Phase 6 — Expanded observatory
20 series (19 historical releases), 26 sourced events, 855 fixed benchmark targets, bounded title audit, daily publication with last-good retention, and cloud readback. See [expansion protocol](EXPANSION.md). Existing phase tags remain immutable.

## Phase 7 — Portfolio feature and event investigations
Source-linked event investigations and integration into the existing public portfolio, including a dedicated architecture/case-study page. See [verification report](PHASE_7.md).
