# Phase checkpoints

One public repository is used for the entire project. Each completed phase gets a descriptive commit and an annotated `phase-N` tag; future phases are not marked complete in advance.

| Phase | Status | Evidence |
| --- | --- | --- |
| 0 · Scope and source feasibility | Complete | Four real source probes, source audit, versioned source/event registry, data contract |
| 1 · Reproducible data foundation | Complete | 1,649 real observations, raw payloads and receipts, atomic publication, byte-identical offline replay, 29 passing tests; [verification](PHASE_1.md) |
| 2 · Analysis and evaluation | Next | Past-only features, normalized comparisons, benchmark report |
| 3 · Dashboard and interaction | Planned | Responsive application with real data and accessible charts |
| 4 · Reliability and release verification | Planned | Browser QA, CI, operating instructions |
| 5 · Deployment and portfolio package | Planned | Verified deployment, case study, screenshots, portfolio copy |

Public source publication is authorized. The registered Site remains private; its deployment is separate from GitHub source checkpoints. No production dashboard exists yet.

Public repository: https://github.com/AnoopIbrampur/vice-observatory

Completed phase tags: `phase-0`, `phase-1`. A new repository is not created for each phase; checkpoints preserve the history of this one project.
