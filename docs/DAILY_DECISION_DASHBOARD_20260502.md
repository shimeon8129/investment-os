# Daily Decision Dashboard v0 — 2026-05-02

## Source

- Holdings file: `/home/shimeon/investment_os/data/portfolio/current_holdings.json`
- Candidate file: `/home/shimeon/investment_os/data/candidates.json`
- Holdings as_of: `2026-04-29`

## Purpose

This dashboard summarizes current candidates and current holdings for human review.
It does not execute trades and does not change any strategy logic.

## 1. Market / Signal State

Dashboard v0 does not make a new market regime decision.
It summarizes current candidate output only.

### Candidate Signal Counts

- EARLY: 19
- READY: 15

## 2. Top Candidates

| rank | ticker | name | asset_type | close | scanner_score | signal | raw_score | raw_level | raw_price |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2467 | 2467.TW | - | 609.0 | 2 | READY | 2 | READY | 609.0 |
| 2 | 3583 | 3583.TW | - | 792.0 | 2 | READY | 2 | READY | 792.0 |
| 3 | 5443 | 均豪 | stock | 129.5 | 2 | READY | 2 | READY | 129.5 |
| 4 | 3680 | 家登 | stock | 537.0 | 2 | READY | 2 | READY | 537.0 |
| 5 | 2464 | 2464.TW | - | 113.5 | 2 | READY | 2 | READY | 113.5 |
| 6 | 3711 | 日月光 | stock | 478.0 | 2 | READY | 2 | READY | 478.0 |
| 7 | 2449 | 2449.TW | - | 302.5 | 2 | READY | 2 | READY | 302.5 |
| 8 | 6147 | 6147.TWO | - | 163.0 | 2 | READY | 2 | READY | 163.0 |
| 9 | 2377 | 2377.TW | - | 97.7 | 2 | READY | 2 | READY | 97.7 |
| 10 | 3037 | 3037.TW | - | 883.0 | 2 | READY | 2 | READY | 883.0 |

## 3. Current Holdings

- Holdings as_of: `2026-04-29`
- Currency: `TWD`

| ticker | name | shares | asset_type | market |
| --- | --- | --- | --- | --- |
| 009816 | 富邦台灣TOP50 | 5000 | ETF | TW |
| 00992A | 主動群益台灣科技創新 | 5000 | ETF | TW |
| 2330 | 台積電 | 50 | stock | TW |
| 2408 | 南亞科 | 120 | stock | TW |
| 2345 | 智邦 | 55 | stock | TW |
| 3017 | 奇鋐 | 20 | stock | TW |
| 3711 | 日月光 | 50 | stock | TW |
| 6830 | 汎銓 | 20 | stock | TW |

## 4. Portfolio vs Candidate Buckets

### 4.1 Held and Candidate

- 2330 台積電 — shares: 50, score: 2, signal: READY
- 3711 日月光 — shares: 50, score: 2, signal: READY
- 6830 汎銓 — shares: 20, score: 1, signal: EARLY

### 4.2 Held but Not Candidate

- 009816 富邦台灣TOP50 — shares: 5000; manual review required.
- 00992A 主動群益台灣科技創新 — shares: 5000; manual review required.
- 2345 智邦 — shares: 55; manual review required.
- 2408 南亞科 — shares: 120; manual review required.
- 3017 奇鋐 — shares: 20; manual review required.

### 4.3 Candidate but Not Held

- 2313 2313.TW — score: 0, signal: EARLY
- 2356 2356.TW — score: 1, signal: EARLY
- 2368 2368.TW — score: 1, signal: EARLY
- 2376 2376.TW — score: 1, signal: EARLY
- 2377 2377.TW — score: 2, signal: READY
- 2382 2382.TW — score: 0, signal: EARLY
- 2449 2449.TW — score: 2, signal: READY
- 2454 2454.TW — score: 2, signal: READY
- 2464 2464.TW — score: 2, signal: READY
- 2467 2467.TW — score: 2, signal: READY
- 3037 3037.TW — score: 2, signal: READY
- 3044 3044.TW — score: 1, signal: EARLY
- 3131 3131.TWO — score: 0, signal: EARLY
- 3189 3189.TW — score: 2, signal: READY
- 3231 3231.TW — score: 1, signal: EARLY
- 3413 3413.TW — score: 0, signal: EARLY
- 3443 3443.TW — score: 1, signal: EARLY
- 3583 3583.TW — score: 2, signal: READY
- 3661 3661.TW — score: 2, signal: READY
- 3680 家登 — score: 2, signal: READY
- ... 11 more

## 5. Risk Notes

This section is informational only.
No automatic buy/sell decision is made.

- Held but not candidate count: 5
- Candidate but not held count: 31

Manual interpretation:

- Held but not candidate: check whether the position still matches current trend logic.
- Candidate but not held: check whether it deserves watchlist status, not immediate entry.
- Held and candidate: check whether it deserves continued hold, add, or no action.

## 6. Manual Action Checklist

- [ ] Check whether market condition supports new entries
- [ ] Review Held and Candidate names
- [ ] Review Held but Not Candidate names
- [ ] Review Candidate but Not Held names
- [ ] Confirm no ticker-name mismatch
- [ ] Confirm no direct execution is triggered by this report
- [ ] Write manual decision notes before any trade
