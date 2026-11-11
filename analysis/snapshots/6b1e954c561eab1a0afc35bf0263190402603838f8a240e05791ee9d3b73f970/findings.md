# Phase 2 findings and retrospective benchmark

Analysis date: 2026-11-11 (UTC; current day excluded). Source snapshot: `73ecfa4562de20fb39627963ab85f8e2cf666ba825697af6c90de454f5590415`.

Generated from verified saved observations under the fixed [analysis protocol](https://github.com/AnoopIbrampur/vice-observatory/blob/main/docs/ANALYSIS_PROTOCOL.md). Exact protocol bytes are archived alongside each analysis snapshot. This is descriptive analysis and a retrospective benchmark, not a prospective forecast record.

## Observed attention

The latest value and week change below refer to each series' own final observed date, not a shared calendar date. Historical windows are deliberately fixed.

| Series | Last observed | Daily views | Trailing 7-day mean | Change vs previous complete 7 days |
| --- | --- | ---: | ---: | ---: |
| Grand Theft Auto VI | 2026-11-10 | 64,375 | 35,803.0 | 67.3% |
| GTA V · 2022 console re-release | 2022-06-13 | 4,124 | 4,720.6 | 7.9% |
| Red Dead Redemption 2 | 2019-01-24 | 11,805 | 13,517.6 | -12.3% |
| Cyberpunk 2077 | 2021-03-10 | 5,294 | 5,533.0 | -4.5% |

GTA VI's complete-week comparison uses 2026-11-04 through 2026-11-10 against 2026-10-28 through 2026-11-03. It measures attention to this article only.

## Release comparison availability

Index = 100 × daily views / mean views on release-relative days -28 through -8 (21 complete dates). The normalizer is retrospective and must not be treated as a historical forecasting feature.

| Series | Release date | Release type | Baseline coverage | Baseline mean | Index status |
| --- | --- | --- | ---: | ---: | --- |
| Grand Theft Auto VI | 2026-11-19 (scheduled) | original_launch | 20/21 | Unavailable | incomplete |
| GTA V · 2022 console re-release | 2022-03-15 (released) | console_rerelease | 21/21 | 6,655.8 | available |
| Red Dead Redemption 2 | 2018-10-26 (released) | original_launch | 21/21 | 23,087.4 | available |
| Cyberpunk 2077 | 2020-12-10 (released) | original_launch | 21/21 | 31,726.2 | available |

GTA VI has 99 unobserved future dates in the fixed -90 to +90 comparison range. They contain nulls, not extrapolated values. Its scheduled release is not marked as having occurred.

## Event-window associations

Compare seven days before an event against event day through day +6. Scheduled events are not assigned a measured effect. These are associations; no causal inference is supported.

| Event | Date | Status | Before coverage | After coverage | Mean change |
| --- | --- | --- | ---: | ---: | ---: |
| [November 2026 launch date announced](https://www.rockstargames.com/newswire/article/ak3ak31a49a221/grand-theft-auto-vi-is-now-set-to-launch-november-19-2026) | 2025-11-06 | available | 7/7 | 7/7 | 261.6% |
| [GTA VI scheduled launch](https://ir.take2games.com/node/32311/pdf) | 2026-11-19 | scheduled | 0/7 | 0/7 | Unavailable |
| [GTA V PS5 / Xbox Series console re-release](https://ir.take2games.com/node/28526/pdf) | 2022-03-15 | available | 7/7 | 7/7 | 12.4% |
| [Red Dead Redemption 2 console launch](https://www.rockstargames.com/newswire/article/4k412883895ka4/red-dead-redemption-2-now-available) | 2018-10-26 | available | 7/7 | 7/7 | 155.9% |
| [Cyberpunk 2077 launch](https://www.cdprojekt.com/en/media/news/cyberpunk-2077-is-out-now/) | 2020-12-10 | available | 7/7 | 7/7 | 88.7% |

## Historical forecasting benchmark

Fixed targets: days -14 through +30 around each historical release. Earlier dates supply context. Yesterday uses t-1; trailing-week uses t-7 through t-1. Both methods are scored on the same dates. Nothing is fitted or tuned. GTA VI is excluded because its launch window has not been observed.

| Series | Targets | Yesterday MAE | Trailing-week MAE | Yesterday WAPE | Trailing-week WAPE | Lower MAE |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| GTA V · 2022 console re-release | 45/45 | 460.2 | 551.7 | 6.8% | 8.2% | yesterday |
| Red Dead Redemption 2 | 45/45 | 12,475.5 | 26,768.0 | 17.2% | 36.9% | yesterday |
| Cyberpunk 2077 | 45/45 | 21,961.6 | 42,590.8 | 26.9% | 52.1% | yesterday |

Total scored targets: 135. MAE is pageviews per day; WAPE is total absolute error divided by actual views, not an accuracy score.

Pooled MAE: yesterday 11,632.4; trailing-week 23,303.5. This is sensitive to the largest series.

Equal-game macro WAPE: yesterday 17.0%; trailing-week 32.4%.

### Fixed regimes

| Series | Regime | Days | Yesterday MAE | Trailing-week MAE |
| --- | --- | ---: | ---: | ---: |
| GTA V · 2022 console re-release | pre_launch | 14 | 429.9 | 436.8 |
| GTA V · 2022 console re-release | launch_days | 3 | 1,940.7 | 1,677.3 |
| GTA V · 2022 console re-release | post_launch | 28 | 316.8 | 488.5 |
| Red Dead Redemption 2 | pre_launch | 14 | 12,557.2 | 17,995.2 |
| Red Dead Redemption 2 | launch_days | 3 | 65,165.3 | 127,901.4 |
| Red Dead Redemption 2 | post_launch | 28 | 6,789.4 | 20,318.7 |
| Cyberpunk 2077 | pre_launch | 14 | 16,914.6 | 34,934.3 |
| Cyberpunk 2077 | launch_days | 3 | 133,079.3 | 148,065.0 |
| Cyberpunk 2077 | post_launch | 28 | 12,579.6 | 35,118.2 |

## Interpretation and limits

- The score tables describe these three selected historical windows. They do not establish generalization or significance across unseen launches.
- Launch-day spikes are a different regime from ordinary traffic; see the separate launch-days scores rather than relying on an average alone.
- A smoother descriptive chart is not automatically a better next-day prediction. Report whichever method actually has lower error in each fixed window.
- GTA V 2022 is a console re-release and the underlying article covers the whole game. Platform-specific interest cannot be isolated.
- Exact-title traffic can omit earlier article titles and redirects. Early GTA VI values must not be read as total awareness.
- There is no paid inference, trained ML model, or claimed GTA VI sales forecast here.

Full-precision values and every scored prediction are exported beside the source manifest. See `analysis/current.json` for their immutable paths. Display rounding in this report does not alter scoring.
