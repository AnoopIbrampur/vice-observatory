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

Public source publication is authorized. The dashboard is deployed at https://vice-observatory-anoop.poeticskink11.chatgpt.site with owner-only access preserved. Its public GitHub source and portable static package are separate from that private deployment.

Public repository: https://github.com/AnoopIbrampur/vice-observatory

Completed phase tags: `phase-0`, `phase-1`, `phase-2`, `phase-3`, `phase-4`, `phase-5`. A new repository is not created for each phase; checkpoints preserve the history of this one project.
