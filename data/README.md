# Data provenance

Wikimedia Analytics API daily article pageviews, `en.wikipedia.org`, `all-access`, `user`, `daily`, UTC. Provider data license: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/), per the [Wikimedia access policy](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/access-policy.html).

Start with `current.json`. Resolve each referenced filename relative to this directory. Raw response bytes and acquisition receipts are content-addressed; snapshots are immutable. Run `python3 -m scripts.pipeline verify` from the repository root to validate hashes, observations, and exported files without network access.

This directory contains actual source observations. Synthetic test fixtures are isolated in `tests/`. These counts are article pageviews, not unique people, players, purchases, or sentiment.
