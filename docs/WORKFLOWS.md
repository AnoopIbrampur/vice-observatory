# Verification, refresh, and deployment are separate operations

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
