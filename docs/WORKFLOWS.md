# Verification, refresh, and deployment are separate operations

## Expansion release: current operating path

The daily publication now runs in `.github/workflows/publish.yml` at **12:23 UTC**, on main pushes (publish only), and manual dispatch (refresh by default). GitHub may delay scheduled runs. Pages is enabled with the Actions publishing source. No user-supplied API key or paid service is needed.

An isolated candidate collects source data and the bounded MediaWiki title audit, rebuilds analysis, records a checkpoint and passes the release gate. Only then are artifacts overlaid, tested on the workflow runner, committed and uploaded to Pages. Acquisition failure records `failed_retained_last_good` with unchanged active source/analysis pointers; the last good data and failure record can still deploy, and the workflow ends failed to surface the problem. A later test, commit or deployment failure leaves the previous live artifact in place. Push races fail safely instead of force-pushing.

`dist/publication.json` is a single checkpoint containing both immutable pointers, the title-audit checksum and the last 30 attempt records. The browser verifies the matching bundle before rendering. The public Sites demo reads this checkpoint from GitHub Pages, including all matching downloads. If retrieval or integrity checks fail, it shows its complete bundled snapshot with an explicit fallback notice. A runtime fallback never silently mixes remote and local data. Code/UI updates still require a Sites deployment.

Manual current refresh: `python3 -m scripts.publication refresh`. Rebuild without acquisition: analysis build → publication record → check_release. Changing the audit or either pointer requires regenerating the publication checkpoint. Automated tests and `python -m scripts.verify_publication <public-base-url>` verify published download hashes. Use Actions run status to distinguish validated attempts from successful deployments.

All 20 pageview histories are currently refetched daily, including fixed historical windows, to retain fresh acquisition evidence. This increases immutable archive size over time; monitor repository growth before long-term use. Events are manually verified source entries and are not inferred to have occurred merely because a scheduled date passed. No automatic news ingestion or prospective ML claim is made.

The sections below preserve the initial release workflow where relevant.


## Continuous integration

`.github/workflows/ci.yml` runs on main-branch pushes, pull requests, and manual dispatch. Each matrix job uses Node 22 and one of Python 3.11/3.13. It runs all unit tests, JavaScript syntax checks, the deterministic release gate, and a loopback HTTP smoke check. After GitHub's runner/setup downloads, the checks need no external data API or paid service. No third-party package installation is needed.

Both workflows use `contents: read`, disable persisted checkout credentials, and pin official Actions to full SHAs. An Actions update requires resolving the official release revision again and rerunning CI. No personal access token or repository secret is required for these workflows. GitHub provides its own scoped workflow credentials.

```sh
python3 -m unittest discover -s tests
node --test tests/dashboard.test.mjs
python3 -m scripts.check_release
python3 -m scripts.smoke_http
```

`smoke_http` starts a short-lived loopback server, verifies served bytes, and shuts it down. In a restricted local environment, it may require permission to bind a local socket. CI does not use a browser automation framework; browser QA is performed separately and recorded in phase reports.

## Manually dispatched refresh

`.github/workflows/refresh.yml` has only `workflow_dispatch`; it has no scheduled trigger. GitHub documents [manual dispatch](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow) and [workflow-token permissions](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token).

From this repository, Codex can run:

```sh
gh workflow run refresh.yml -f as_of=2026-11-11
gh run list --workflow refresh.yml
```

Use an ISO UTC analysis date; omitting `as_of` selects the runner's current UTC day. Inputs enter Python through an environment variable and strict date parsing, never as interpolated shell commands. The collector requests only earlier days. If Wikimedia has not published a requested day, the run fails rather than filling it with zero or replacing the last valid publication.

The workflow:

1. Validates the checked-out source and analysis.
2. Copies the required source folders to an isolated temporary checkout.
3. Collects all configured public Wikimedia histories and validates exact dates/dimensions.
4. Rebuilds derived analysis and the readable findings report against the new source identity.
5. Runs the complete release gate against the candidate.
6. Uploads `vice-refresh-candidate-<run-id>` as an Actions artifact with seven-day retention.

The workflow does not commit, push, deploy, modify main, or require Anoop to operate the website. Codex can inspect the result, download the artifact into a fresh scratch directory, overlay it onto an isolated copy of the matching project, and independently verify it. If a refresh is later requested for publication, Codex can apply the reviewed data/analysis changes to the project, rerun all checks, and push them under the existing project authorization.

A failed candidate leaves the original checkout and active source publication unchanged. Existing candidate directories are not overwritten. Candidate output must be outside the source checkout. The artifact's `CANDIDATE.json` records its as-of date, source/analysis identities, release-gate report, and explicit `pushed: false` / `deployed: false` values.

For a local candidate:

```sh
python3 -m scripts.refresh_candidate --as-of 2026-11-11 --output /tmp/vice-refresh-candidate
```

Use a new output directory each time. Acquisition needs Wikimedia network access; independent replay and verification do not.

## When a hosted application updates

A successful candidate run is not a data publication. A GitHub push is not a Site deployment. The supported path is:

**collect candidate → verify/review → apply matching source and analysis files → test/release gate → commit/push → package/deploy that exact version → confirm deployment success.**

Production publication is Phase 5. No deployment hook, public Site audience change, or cron schedule was added in Phase 4. Until that work is explicitly implemented, the app continues to identify itself as a saved snapshot with no scheduled refresh.

## Local failure-state QA

```sh
python3 -m scripts.qa_server --port 8765
```

Open the normal page at `http://127.0.0.1:8765/`. The following deliberate fixtures are served only by this development server:

- `/__qa__/missing/`: HTTP 503 for the source pointer.
- `/__qa__/tampered/`: modified dataset bytes that fail integrity verification.
- `/__qa__/stale/`: a source/analysis identity mismatch.

These scenarios alter responses in memory, not saved data. The server binds only to loopback and is not part of `dist/`. Stop it after browser QA. Screenshots and results are documented in the phase reports.
