# Source feasibility audit

Checked: 2026-11-11. Status: Phase 0 complete.

## Access and data rights

The Wikimedia Analytics API exposes public pageview data without an API key. Its [access policy](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/access-policy.html) specifies CC0 1.0 data, a descriptive User-Agent, and sequential requests. The collector will identify Vice Observatory and the author's public portfolio, issue one request at a time, and honor rate-limit responses. No fixed unlimited quota is assumed.

The [pageview reference](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html) states that coverage starts July 1, 2015. GTA V's original 2013 launch and April 2015 PC launch are therefore excluded. [Usage guidelines](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_API_Usage_Guidelines) require observing throttling and identifying the source provider.

## Real feasibility probes

These are actual API responses, not generated examples. Counts were checked against inclusive requested windows; full validation and committed receipts are Phase 1 deliverables.

| Series | Requested UTC dates | Expected / returned days | Result |
| --- | --- | --- | --- |
| Grand Theft Auto VI | 2023-11-01–2026-11-10 | 1,106 / 1,106 | Usable exact-title history |
| GTA V · 2022 console re-release | 2021-12-15–2022-06-13 | 181 / 181 | Usable, must label re-release |
| Red Dead Redemption 2 | 2018-07-28–2019-01-24 | 181 / 181 | Usable original console-launch window |
| Cyberpunk 2077 | 2020-09-11–2021-03-10 | 181 / 181 | Usable original-launch window |

Total: 1,649 returned daily observations across four series.

## Identity and interpretation

- The API response project is `en.wikipedia`, whereas the request uses `en.wikipedia.org`. This is an explicit permitted normalization.
- Each request targets one exact article title. We have not audited all historical aliases or combined redirect traffic. In particular, GTA VI's low early values must not be interpreted as total awareness before the article used this title. Expose this limitation and avoid first-trailer pre/post claims requiring a comparable pre-title baseline.
- Historical comparison windows are 90 days before through 90 days after launch, inclusive. GTA VI has only past observations; November 19, 2026 remains scheduled, not observed.
- Pageviews describe traffic to the whole article, not specific platforms. GTA V 2022 cannot be presented as an original-launch or platform-specific audience estimate.
- API publication can lag the current day. Fetch age and last observed date are separate; if requested recent days are unavailable, report incomplete coverage and preserve the last successful publication. Historical data may be revised.

## Primary release-date evidence

- GTA VI: [Rockstar date announcement](https://www.rockstargames.com/newswire/article/ak3ak31a49a221/grand-theft-auto-vi-is-now-set-to-launch-november-19-2026) and a [dated Take-Two press release](https://ir.take2games.com/node/32311/pdf) explicitly state November 19, 2026. The Rockstar page is JavaScript-rendered and not fully extractable by the text reader; use the readable publisher press release for the date.
- GTA V PS5/Xbox Series: [Take-Two release](https://ir.take2games.com/node/28526/pdf) dated March 15, 2022; [official Rockstar launch video](https://www.youtube.com/watch?v=lqiZdynJmag) corroborates the date.
- Red Dead Redemption 2: [Rockstar launch announcement](https://www.rockstargames.com/newswire/article/4k412883895ka4/red-dead-redemption-2-now-available), dated October 26, 2018 in indexed publisher metadata, corroborated by the [official trailer](https://www.youtube.com/watch?v=iqaipBpnVRE). Full article extraction was unavailable; do not claim its whole text was reviewed.
- Cyberpunk 2077: [directly readable publisher launch announcement](https://www.cdprojekt.com/en/media/news/cyberpunk-2077-is-out-now/), dated December 10, 2020.

The event registry starts deliberately small. Additional trailer and announcement annotations require a dated primary source before inclusion. Nothing is inferred from a pageview spike alone.

## Phase 1 decision

Proceed with these four exact-title series and the versioned [data contract](DATA_CONTRACT.md). Free source access is sufficient for the first release. Social-platform ingestion is unnecessary. Title-history reconciliation remains a documented limitation rather than an unverified correction.
