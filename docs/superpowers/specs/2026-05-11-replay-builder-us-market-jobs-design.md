# Spec: Replay Builder Auto-Integration + US Market Jobs

**Date:** 2026-05-11  
**Status:** Approved

## Problem

1. `observation_replay_builder.py` is a standalone CLI tool — never called automatically. The replay page (`replay.html`) reads `data/observations/daily/*_observation_summary.json`, but that file is never generated for new trading days, so the replay page shows only historical data.

2. No US market (美股) intraday observation pipeline exists. Taiwan market slots run Mon–Fri via systemd timers; US market hours (21:30–04:30 CST) have no coverage.

## Goals

- After every intraday slot (TW or US), the daily summary JSON and web dashboard update automatically.
- US market intraday observation runs at 3 slots per session: `us_market_open` (21:30), `us_midday` (01:00), `us_post_close_review` (04:30) CST.
- Zero risk to existing Taiwan market pipeline.
- `daily_run_us.py` is a scaffold ready for US tickers; gracefully no-ops when `data/candidates_us.json` is absent.

## Out of Scope

- Holiday/market calendar checking (both markets run Mon–Fri, no holiday guard)
- Populating `data/candidates_us.json` with actual US tickers
- Merging TW/US intraday_observation into a shared core

---

## Architecture

### Data Flow (after fix)

```
intraday_observation.py <slot> [--market tw|us]
  │
  ├─ tw (default)
  │    └─ calls daily_run.py
  │         session_date = Asia/Taipei today
  │
  └─ us
       └─ calls daily_run_us.py
            session_date = US/Eastern today  ← prevents cross-midnight date mismatch
  │
  ├─ writes data/observations/intraday/<session_date>/<HHMM>_<slot>_observation.json
  ├─ [NEW] build_summary(session_date)
  │         → data/observations/daily/<session_date>_observation_summary.json
  └─ generate_all()
       → reports/web/replay.html (now shows today's data)
```

### Systemd Timers (Taiwan CST)

| Timer | Schedule | Instance |
|-------|----------|----------|
| `investment-os-intraday-us-market-open.timer` | Mon–Fri 21:30 | `us_market_open` |
| `investment-os-intraday-us-midday.timer` | Tue–Sat 01:00 | `us_midday` |
| `investment-os-intraday-us-post-close.timer` | Tue–Sat 04:30 | `us_post_close_review` |

All three timers reuse the existing `investment-os-intraday-observation@.service`.  
`Persistent=false` on all US timers (missed runs are not retried).

---

## Component Changes

### 1. `jobs/intraday_observation.py` (modify)

- Add `--market tw|us` CLI argument via `argparse` (default: `tw`).
- When `--market us`: compute `session_date` from `datetime.now(ZoneInfo("US/Eastern")).date()`.
- When `--market tw`: `session_date` from `datetime.now(ZoneInfo("Asia/Taipei")).date()` (existing behavior, extracted to variable).
- Replace hardcoded `daily_run` subprocess call with market-aware selection (`daily_run` vs `daily_run_us`).
- After `generate_all()`, add `build_summary(str(session_date))` call (wrapped in try/except WARN).

### 2. `jobs/daily_run_us.py` (new)

- Reads `data/candidates_us.json`.
- If file absent or empty: print `[INFO] candidates_us.json not found — skipping US run` and exit 0.
- Otherwise: mirrors `daily_run.py` structure for US tickers.
- Writes to same output paths as `daily_run.py` (`data/processed/signal_snapshot.json`, `data/processed/mainline_snapshot.json`). No collision risk: US slot times (21:30, 01:00, 04:30 CST) never overlap TW slot times (08:40–14:40 CST).

### 3. `scripts/run_intraday_observation.sh` (modify)

- Detect slot prefix: if `$1` starts with `us_`, append `--market us` to the Python call.
- No change to caller interface — systemd passes slot name only.

### 4. `systemd/` (new files)

Three new timer files (see table above). All use `TimeZone=Asia/Taipei` and `Persistent=false`.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| `candidates_us.json` missing | `daily_run_us.py` exits 0; slot records `PARTIAL` |
| `build_summary()` raises | `except Exception` → print WARN, continue |
| `generate_all()` raises | existing behavior (already wrapped) |
| US slot writes to wrong date | prevented by ET-based `session_date` |
| Missed US timer (machine off) | `Persistent=false` — not retried |

---

## Immediate Fix

Before the permanent integration lands, run manually:

```bash
cd /home/shimeon/investment_os
python3 -m jobs.observation_replay_builder 2026-05-11
```

This backfills today's `data/observations/daily/2026-05-11_observation_summary.json` and makes `replay.html` show today's data.

---

## Test Plan

1. Manual backfill: run replay builder for 2026-05-11 → `replay.html` shows today's 7 slots.
2. Integration: trigger one slot manually (`scripts/run_intraday_observation.sh post_close_review`) → `data/observations/daily/2026-05-11_observation_summary.json` updates automatically.
3. US scaffold: `python3 -m jobs.daily_run_us` → prints skip message, exits 0.
4. systemd syntax: `systemd-analyze verify` on new timer files → no errors.
5. US slot date: at 01:00 CST, confirm `session_date` resolves to previous calendar day (ET Monday = CST Tuesday 01:00 still Monday ET).
