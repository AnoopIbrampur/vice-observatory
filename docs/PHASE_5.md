# Phase 5 delivery report

Completed: 2026-11-11.

## Delivered

- A confirmed owner-only production deployment of the verified dashboard and new case-study page.
- A public technical case study covering the problem, architecture, decisions, measured results, a real CI failure/fix, and remaining limitations.
- Architecture diagrams, a portfolio card, résumé bullets, ownership/AI-assistance wording, and interview talking points.
- Complete portable source and static-site ZIPs, with a release manifest identifying source revision and file hashes.
- Deployment/refresh instructions that distinguish public source publication, private Site deployment, and a future public demo.
- A final public GitHub checkpoint and `phase-5` tag.

## Deployment evidence

The native deployment completed successfully at [Vice Observatory](https://vice-observatory-anoop.poeticskink11.chatgpt.site). The existing owner-only audience was preserved. Browser inspection confirmed that the hosted application rendered verified data without an error, selecting 30 days produced 30 table rows, the incomplete index remained visibly unavailable, and the new case-study route loaded and returned to the dashboard. A [production screenshot](screenshots/deployed.jpg) was saved.

The deployed app assets are based on public commit `6e32337a02c8d2fccdd99abf7e5b4ff720d9ed50`, synchronized into Sites source commit `e2fe02e18ea01dc9d06fef07050f8237e0b7ca5c`. Final release documentation is tracked separately in the public phase checkpoint. Source and analysis identities remain the verified Phase 4 identities; no unreviewed refresh was applied.

## Verification

All **79 unit tests** pass. The release gate now inspects both HTML pages, and the loopback HTTP smoke test covers 18 assets/downloads. CI passed the application-content revision on both Python versions: [release-content run](https://github.com/AnoopIbrampur/vice-observatory/actions/runs/43062186367).

The case-study page was inspected in the browser, including a 375-pixel layout with no document overflow. Hosted dashboard controls and source/analysis verification were checked after deployment. Source ZIPs are created from tracked Git content; static ZIPs are created from the exact runtime directory and checked for safe paths, intact contents, and absent Site identity/credentials.

The case study uses measured counts and labels all initial-snapshot statistics by date. It does not invent model training, user research, sales forecasts, scheduled updates, or public demo access. Existing résumé and personal portfolio files were not modified; prepared copy is in [PORTFOLIO_COPY.md](PORTFOLIO_COPY.md).

## Access and completion boundary

All five planned build phases are delivered. The Site is a private review deployment. The repository, source history, and technical case study are public, while making the demo itself recruiter-accessible is a separate audience/hosting decision. The static package is ready for that step. No paid API key is required, and no refresh schedule is active.
