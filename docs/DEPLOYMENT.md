# Deployment and portable hosting

## Current deployment

The verified application is deployed at:

**https://vice-observatory-anoop.poeticskink11.chatgpt.site**

Audience: **public**. Anyone with the URL can open the dashboard and case study without an owner login. Public access was explicitly requested after the initial Phase 5 owner-only deployment. Anonymous HTTP requests verified both pages, source/analysis identity matching, and payload checksums without cookies or authorization. The [GitHub repository](https://github.com/AnoopIbrampur/vice-observatory), [case study](CASE_STUDY.md), and source package are also public.

The deployed runtime was prepared from GitHub commit `6e32337a02c8d2fccdd99abf7e5b4ff720d9ed50`. The separate Sites source commit is `e2fe02e18ea01dc9d06fef07050f8237e0b7ca5c`. Later public documentation/release-packaging commits do not change these deployed application assets. The deployment contains the dashboard, a static case-study page, and verified saved data/analysis.

Native deployment reported success, and browser inspection confirmed the actual hosted dashboard, successful integrity checks, a working 30-day filter, the pending 20/21-day index notice, and navigation to the case study and back. No authentication bypass was created. See [deployment evidence](verification/deployment.json).

## Two source repositories

The public GitHub repository is the portable project and phase history. It omits `.openai/`, credentials, local process state, and Git authentication configuration.

The private Sites source checkout contains the deployment manifest for the existing Site and a record of the public source revision. Source synchronization and packaging use the supported Sites helper; the deployed archive is built from its exact pushed source commit. Credentials enter that helper through hidden stdin and are never written into the project or portable packages.

## Portable static package

The release's static ZIP contains the contents of `dist/`, including all runtime modules, styles, case-study HTML, version pointers, and referenced immutable snapshots. It contains no Site ID, credentials, dependency install, or build requirement. Extract it and serve the directory over HTTPS or localhost.

The complete source ZIP is a Git archive of the final public phase checkpoint, with scripts, tests, provenance, documentation, and static assets. It does not contain `.git`, `.openai`, caches, or untracked scratch files. A separate release manifest records archive checksums and the public commit identity.

For local use after extracting the source archive:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory dist
```

Open `http://127.0.0.1:8765/`. The browser requires HTTP on localhost or HTTPS for module loading and Web Crypto; `file://` is unsupported.

## Recruiter-accessible hosting

The Site now has an explicitly authorized public audience, so the live URL is suitable for a portfolio card or recruiter message. The original Phase 5 ZIPs and phase report preserve the earlier private-review checkpoint; current access is public. The user's existing personal portfolio has not been edited.

## Future data publications

Manual refresh remains separate from publication. Build an isolated candidate, verify it, apply reviewed source/analysis changes, rerun the full test and release gate, commit/push, package the same verified runtime, deploy, and confirm success. The hosted app does not update merely because CI or the candidate workflow succeeds. No schedule or unattended deployment hook is active.
