# Market Context Gate v0.2 — Spec

Branch: add-daily-decision-dashboard-v0-20260426_2057
Status: Draft
Date: 2026-05-02

---

## Purpose

Investment OS can and should run every day — including weekends and holidays.

The market calendar is **not** a simple on/off switch for skipping runs. It is a
context layer that determines:

- What the market's current status is (open, closed, holiday, weekend)
- What session phase we are in (pre-market, regular, post-market, closed)
- What the latest fully settled trading day is for each market
- What data vintage to use (`data_as_of_date`)
- What data mode the pipeline should operate in
- What pipeline policy applies for this run

**Key principle: market closed does not mean no data.**
It means use the latest valid trading day. Reports and snapshots should always
reflect the most recent available data, clearly labeled with the data vintage.

---

## Required Fields per Market Context Record

| Field | Type | Description |
|-------|------|-------------|
| `run_at` | ISO datetime | Wall-clock time when the pipeline executed |
| `market` | string | Market identifier: `TW`, `US` |
| `timezone` | string | IANA timezone for this market |
| `local_date` | ISO date | `run_at` converted to market local date |
| `local_time` | HH:MM | `run_at` converted to market local time |
| `today_status` | enum | Session status for `local_date` (see below) |
| `session_phase` | enum | Intraday phase at `run_at` (see below) |
| `latest_full_trading_day` | ISO date | Most recent date with complete OHLCV data |
| `data_as_of_date` | ISO date | Date the pipeline should treat as "today" for data |
| `data_mode` | enum | How data should be sourced (see below) |
| `pipeline_policy` | enum | What the pipeline should do with this context (see below) |
| `report_label` | string | Human-readable label for report headers |

---

## Status Enum

| Value | Meaning |
|-------|---------|
| `OPEN` | Regular full trading session |
| `OPEN_EARLY_CLOSE` | Trading session with early close (e.g. day before holiday) |
| `CLOSED_WEEKEND` | Saturday or Sunday |
| `CLOSED_HOLIDAY` | Weekday market holiday per calendar |

---

## Session Phase Enum

| Value | Meaning |
|-------|---------|
| `PRE_MARKET` | Before regular session open |
| `REGULAR_SESSION` | Inside regular trading hours |
| `POST_MARKET` | After regular close, same trading day |
| `CLOSED` | Market is closed (weekend, holiday, or outside all sessions) |

---

## Data Mode Enum

| Value | Meaning |
|-------|---------|
| `FULL_DAILY` | Today is a full trading day and close data is available |
| `PREVIOUS_FULL_DAILY` | Market closed; use previous full trading day's close data |
| `INTRADAY_LATEST` | Regular session in progress; use latest available tick/bar |
| `CLOSED_NO_NEW_DATA` | Market closed and no newer data is available than last run |

---

## Pipeline Policy Enum

| Value | Meaning |
|-------|---------|
| `RUN_WITH_LATEST_AVAILABLE` | Run full pipeline using `data_as_of_date` close data |
| `RUN_INTRADAY_CONTEXT` | Run pipeline with intraday-aware data; label output clearly |
| `REPORT_ONLY` | Do not re-run pipeline; re-render report from last snapshot |

---

## Worked Examples

### Example 1 — Saturday in Taipei (2026-05-02, Asia/Taipei)

```
run_at:                  2026-05-02T00:32:00+08:00
market:                  TW
timezone:                Asia/Taipei
local_date:              2026-05-02
local_time:              00:32
today_status:            CLOSED_WEEKEND
session_phase:           CLOSED
latest_full_trading_day: 2026-05-01   ← last Friday with full OHLCV
data_as_of_date:         2026-05-01
data_mode:               PREVIOUS_FULL_DAILY
pipeline_policy:         RUN_WITH_LATEST_AVAILABLE
report_label:            "Data as of 2026-05-01 (TW market closed — weekend)"
```

TW data from Friday 2026-05-01 close is valid and complete. Pipeline should run
using that data. The report must say "Data as of 2026-05-01" — not "no data".

---

### Example 2 — Same wall-clock, US market (2026-05-01, America/New_York)

The same pipeline run at 00:32 Taipei time is 12:32 on 2026-05-01 New York time.

```
run_at:                  2026-05-02T00:32:00+08:00
market:                  US
timezone:                America/New_York
local_date:              2026-05-01
local_time:              12:32
today_status:            OPEN
session_phase:           REGULAR_SESSION
latest_full_trading_day: 2026-04-30   ← yesterday's settled close
data_as_of_date:         2026-04-30   (or intraday 2026-05-01 if intraday feed)
data_mode:               INTRADAY_LATEST
pipeline_policy:         RUN_INTRADAY_CONTEXT
report_label:            "Data as of 2026-05-01 intraday (US session open)"
```

US has newer market activity than TW on the same run. The two markets may have
different `data_as_of_date` values within the same pipeline run. Each market
context record is independent.

---

### Example 3 — TW Holiday (2026-05-01, Labour Day)

```
run_at:                  2026-05-01T07:00:00+08:00
market:                  TW
timezone:                Asia/Taipei
local_date:              2026-05-01
local_time:              07:00
today_status:            CLOSED_HOLIDAY
session_phase:           CLOSED
latest_full_trading_day: 2026-04-30
data_as_of_date:         2026-04-30
data_mode:               PREVIOUS_FULL_DAILY
pipeline_policy:         RUN_WITH_LATEST_AVAILABLE
report_label:            "Data as of 2026-04-30 (TW market closed — holiday)"
```

---

### Example 4 — TW Regular Session

```
run_at:                  2026-05-04T10:00:00+08:00
market:                  TW
timezone:                Asia/Taipei
local_date:              2026-05-04
local_time:              10:00
today_status:            OPEN
session_phase:           REGULAR_SESSION
latest_full_trading_day: 2026-05-01
data_as_of_date:         2026-05-01   ← last settled close (today not yet closed)
data_mode:               INTRADAY_LATEST
pipeline_policy:         RUN_INTRADAY_CONTEXT
report_label:            "Data as of 2026-05-01 close + 2026-05-04 intraday"
```

---

## Design Notes

### Market closed ≠ no data

When `today_status` is `CLOSED_WEEKEND` or `CLOSED_HOLIDAY`:

- `latest_full_trading_day` is the most recent weekday with complete OHLCV.
- `data_as_of_date` is set to `latest_full_trading_day`.
- `pipeline_policy` is `RUN_WITH_LATEST_AVAILABLE` — pipeline runs normally.
- The report label must state the data vintage explicitly.

Do **not** set `pipeline_policy` to skip or suppress the pipeline solely because
the market calendar shows a non-trading day. Skipping is only appropriate when
data is genuinely unavailable (e.g. first run ever, upstream feed outage).

### Per-market independence

TW and US are evaluated independently. A single pipeline run may have:

- TW: `CLOSED_WEEKEND` + `data_as_of_date=2026-05-01`
- US: `OPEN` + `REGULAR_SESSION` + `data_as_of_date=2026-05-01 intraday`

The pipeline must label each market's data vintage separately in the snapshot
and report.

### Sensitive data rule applies here

`latest_full_trading_day` resolution must not trigger removal or mutation of
universe, watchlist, or portfolio files. If a ticker has no data for the
`data_as_of_date`, classify it as `data_warning`, surface it in the report,
and do not auto-remove. See `00_PROJECT_BRAIN.md` Sensitive Investment Data
Protection Rule.

---

## Current Implementation Status (v0.1 → v0.2 gap)

| Capability | v0.1 (current) | v0.2 (this spec) |
|------------|----------------|-----------------|
| Weekend detection | ✅ `CLOSED_WEEKEND` | ✅ already done |
| Holiday detection | ✅ `CLOSED_HOLIDAY` | ✅ already done |
| Session phase | ❌ not implemented | 🔲 future |
| `latest_full_trading_day` | ❌ not computed | 🔲 future |
| `data_as_of_date` in snapshot | ❌ not present | 🔲 future |
| Per-market data mode | ❌ not present | 🔲 future |
| `pipeline_policy` field | ❌ not present | 🔲 future |
| Report label with vintage | ❌ not present | 🔲 future |

v0.1 correctly classifies open/closed status and skips pipeline on closed days.
v0.2 will allow the pipeline to run on closed days using the last valid data,
and will surface data vintage clearly in all outputs.

---

## Implementation Sequence (post-MVP)

1. Add `latest_full_trading_day(market, date)` to `utils/market_calendar.py`
2. Add `data_as_of_date`, `data_mode`, `pipeline_policy`, `report_label` to
   `get_market_context()` output
3. Update `jobs/daily_run.py` to pass `data_as_of_date` to `pipeline_main_v1`
4. Update `pipeline/main_v1.py` to accept and use `data_as_of_date`
5. Update snapshot and report to include per-market data vintage labels

Do not implement any of the above until MVP branch is merged to main.

---

*End of spec*
