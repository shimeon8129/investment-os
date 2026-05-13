# Daily Decision Dashboard v0 — 2026-05-13

## Source

- Holdings file: `/home/shimeon/investment_os/data/portfolio/current_holdings.json`
- Candidate file: `/home/shimeon/investment_os/data/candidates.json`
- Holdings as_of: `2026-05-13`

## Purpose

This dashboard summarizes current candidates and current holdings for human review.
It does not execute trades and does not change any strategy logic.

## 1. Market / Signal State

Dashboard v0 does not make a new market regime decision.
It summarizes current candidate output only.

### Candidate Signal Counts

- EARLY: 24
- READY: 14

## 2. Top Candidates

| rank | ticker | name | asset_type | close | scanner_score | signal | raw_score | raw_level | raw_price |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2467 | 2467.TW | - | 626.0 | 2 | READY | 2 | READY | 626.0 |
| 2 | 3583 | 3583.TW | - | 966.0 | 2 | READY | 2 | READY | 966.0 |
| 3 | 6187 | 萬潤 | stock | 1225.0 | 2 | READY | 2 | READY | 1225.0 |
| 4 | 6669 | 6669.TW | - | 5580.0 | 2 | READY | 2 | READY | 5580.0 |
| 5 | 2356 | 2356.TW | - | 52.8 | 2 | READY | 2 | READY | 52.8 |
| 6 | 2376 | 2376.TW | - | 313.5 | 2 | READY | 2 | READY | 313.5 |
| 7 | 2377 | 2377.TW | - | 115.5 | 2 | READY | 2 | READY | 115.5 |
| 8 | 3037 | 3037.TW | - | 892.0 | 2 | READY | 2 | READY | 892.0 |
| 9 | 2368 | 2368.TW | - | 1350.0 | 2 | READY | 2 | READY | 1350.0 |
| 10 | 3044 | 3044.TW | - | 529.0 | 2 | READY | 2 | READY | 529.0 |

## 3. Current Holdings

- Holdings as_of: `2026-05-13`
- Currency: `TWD`

| ticker | name | shares | asset_type | market |
| --- | --- | --- | --- | --- |
| 009816 | 富邦台灣TOP50 | 5000 | ETF | TW |
| 2308 | 台達電 | 20 | stock | TW |
| 2330 | 台積電 | 30 | stock | TW |
| 2345 | 智邦 | 65 | stock | TW |
| 2408 | 南亞科 | 120 | stock | TW |
| 3711 | 日月光投控 | 50 | stock | TW |
| 6830 | 汎銓 | 70 | stock | TW |

## 4. Portfolio vs Candidate Buckets

### 4.1 Held and Candidate

- 2308 台達電 — shares: 20, score: 1, signal: EARLY
- 2330 台積電 — shares: 30, score: 2, signal: READY
- 2345 智邦 — shares: 65, score: 1, signal: EARLY
- 3711 日月光投控 — shares: 50, score: 1, signal: EARLY
- 6830 汎銓 — shares: 70, score: 1, signal: EARLY

### 4.2 Held but Not Candidate

- 009816 富邦台灣TOP50 — shares: 5000; manual review required.
- 2408 南亞科 — shares: 120; manual review required.

### 4.3 Candidate but Not Held

- 2303 2303.TW — score: 2, signal: READY
- 2313 2313.TW — score: 1, signal: EARLY
- 2317 2317.TW — score: 1, signal: EARLY
- 2356 2356.TW — score: 2, signal: READY
- 2368 2368.TW — score: 2, signal: READY
- 2376 2376.TW — score: 2, signal: READY
- 2377 2377.TW — score: 2, signal: READY
- 2382 2382.TW — score: 1, signal: EARLY
- 2449 2449.TW — score: 1, signal: EARLY
- 2454 2454.TW — score: 1, signal: EARLY
- 2464 2464.TW — score: 1, signal: EARLY
- 2467 2467.TW — score: 2, signal: READY
- 3037 3037.TW — score: 2, signal: READY
- 3044 3044.TW — score: 2, signal: READY
- 3131 3131.TWO — score: 0, signal: EARLY
- 3189 3189.TW — score: 1, signal: EARLY
- 3231 3231.TW — score: 0, signal: EARLY
- 3413 3413.TW — score: 0, signal: EARLY
- 3443 3443.TW — score: 2, signal: READY
- 3583 3583.TW — score: 2, signal: READY
- ... 13 more

## 5. Risk Notes

This section is informational only.
No automatic buy/sell decision is made.

- Held but not candidate count: 2
- Candidate but not held count: 33

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
