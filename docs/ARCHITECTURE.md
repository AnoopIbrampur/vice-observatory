# Architecture

Current expansion: 20 series, 4,545 daily observations at the November 11 checkpoint, 855 fixed retrospective targets, 26 sourced events, 88 tests, title-audit evidence and daily GitHub Actions/Pages publication with explicit last-good retention. No paid API keys. See [expansion protocol](EXPANSION.md) and [operations](OPERATIONS.md). Earlier measurements below describe the initial release.

```mermaid
flowchart LR
    W[Wikimedia Analytics API] --> I[Python + curl collector]
    I --> R[Immutable raw payloads and receipts]
    R --> V[Date, dimension, coverage and hash validation]
    V --> D[Versioned source snapshot]
    P[Fixed analysis protocol] --> A[Descriptive analysis and past-only benchmark]
    D --> A
    A --> S[Versioned analysis and CSV exports]
    D --> B[Browser SHA-256 and source-ID checks]
    S --> B
    B --> U[Static dashboard: SVG charts and data tables]
```

## Release and refresh

```mermaid
flowchart LR
    G[Public GitHub source] --> C[CI: two Python versions + Node]
    C --> Q[Release gate + HTTP smoke checks]
    G --> M[Manual refresh dispatch]
    M --> T[Isolated checkout: collect, analyze, validate]
    T --> F[Candidate artifact]
    F --> R[Review and apply to source]
    R --> G
    Q --> K[Package exact verified source]
    K --> H[Private Sites deployment]
```

The review/apply and package/deploy arrows are explicit operations, not unattended hooks. CI does not deploy. Manual refresh does not commit. Source and derived data pointers must identify the same source version before the browser displays results.

## Boundaries

- No database, user account system, paid API, inference service, external font, or runtime chart dependency is needed.
- Collection alone uses an external API. A saved dashboard loads from same-origin static files.
- The source repository and Sites source repository are separate. The latter carries the deployment manifest; the portable public source omits Site identity and credentials.
- Source observations use UTC days. Acquisition time, analysis cutoff, and scheduled release dates are distinct fields.
- Raw and analysis snapshots are immutable; current pointers are replaced atomically per consumer. A source refresh requires analysis regeneration.
- The index is retrospective descriptive normalization. It is never a forecasting input.
