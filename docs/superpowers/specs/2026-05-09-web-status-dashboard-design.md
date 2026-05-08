# Design: Investment OS Web Status Dashboard

**Date:** 2026-05-09
**Status:** Approved
**Author:** shimeon

---

## Overview

A multi-page static HTML dashboard that presents daily pipeline results and accumulated observation data, accessible remotely via Tailscale VPN. Pages are generated after each pipeline run and served by a persistent HTTP server.

---

## Goals

- View today's pipeline result, market state, top candidates, and P1 audit from any Tailscale-connected device
- Browse historical observation runs in a table
- Review intraday replay data by date
- No authentication required (Tailscale provides the security boundary)
- Simple, CLI-readable layout — no heavy UI frameworks

---

## Architecture

### File Layout

```
reports/web/
├── status.html       — today's result
├── history.html      — accumulated observation table
└── replay.html       — intraday replay by date

reporting/web_report_generator.py  — reads JSON → writes HTML files

~/.config/systemd/user/investment-os-web.service  — HTTP server (always on)
```

### Data Sources

| HTML Page     | Primary Source                                          |
|---------------|---------------------------------------------------------|
| status.html   | `data/processed/signal_snapshot.json`                  |
|               | `data/processed/mainline_snapshot.json`                |
|               | `reports/observation/YYYY-MM-DD_observation_summary.md` |
| history.html  | All `reports/observation/*_observation_summary.md`     |
| replay.html   | `data/observations/daily/*_observation_summary.json`   |

### Trigger Points

- `jobs/observation_daily.py` — calls generator at the end of each 16:00 run
- `jobs/intraday_observation.py` — calls generator at the end of each intraday slot

Both call `reporting.web_report_generator` as a module import (not subprocess).

---

## HTTP Server

- **Binary:** `python3 -m http.server`
- **Bind:** Tailscale IP `100.92.154.55`, port `8080`
- **Serve root:** `reports/web/`
- **Managed by:** `~/.config/systemd/user/investment-os-web.service`
- **Start on boot:** `systemctl --user enable investment-os-web`

Tailscale IP is read at service start from `ip addr show tailscale0`. If the interface is not up, the service fails gracefully and can be restarted manually.

---

## Pages

### Navigation Bar (all pages)

```
Investment OS  |  今日狀態  |  歷史記錄  |  Replay
                                         最後更新: YYYY-MM-DD HH:MM
```

Active page is highlighted. All pages link to each other.

---

### status.html — 今日結果

Sections (top to bottom):

1. **系統狀態** — PASS / FAIL badge, run timestamp, data mode (OBSERVATION)
2. **市場概況** — market state, score, VIX, TW/US calendar status
3. **Top 候選** — table: rank / ticker / name / score / signal / P1 result
4. **Pipeline 子程序** — table: label / status (PASS/FAIL/SKIPPED)
5. **Regression Check** — import errors, schema errors, missing outputs

If market is closed (CLOSED_WEEKEND / CLOSED_HOLIDAY): show a single banner "市場休市" with the status and skip candidates/P1 sections.

---

### history.html — 歷史觀測記錄

One row per past observation run, newest first.

| 日期 | 狀態 | 市場狀態 | Score | VIX | Top 1 候選 | 觀測類型 |
|------|------|----------|-------|-----|-----------|---------|

Each row is expandable (HTML `<details>`) to show the full subprocess results for that day.

Data sourced by parsing all `reports/observation/*_observation_summary.md` files.

---

### replay.html — Intraday Replay

1. **Date selector** — `<select>` populated from available dates in `data/observations/daily/`
2. **Slot table** — for selected date: slot / time / top 1 ticker / P1 result / market state
3. **Persistence ranking** — table of tickers sorted by appearance count, with warn_l1_l4_pass flag
4. **Next-day watchlist** — from `next_day_watchlist` in the daily observation summary JSON

If no replay data exists for today, show "本日尚無 Replay 資料".

---

## HTML Style

- No external CSS frameworks or CDN dependencies (fully offline-capable)
- Inline `<style>` block in each page: monospace font, dark-friendly neutral colors, minimal decoration
- Color coding: green for PASS, red for FAIL, yellow/orange for WARN, grey for SKIP/CLOSED
- Responsive enough to read on mobile (single-column flow, no fixed widths)

---

## Generator Module

**`reporting/web_report_generator.py`**

```
generate_all()            — entry point, calls all three generators
generate_status_page()    — writes reports/web/status.html
generate_history_page()   — writes reports/web/history.html
generate_replay_page()    — writes reports/web/replay.html
_nav_bar(active)          — returns nav HTML string
_badge(status)            — returns colored span for PASS/FAIL/WARN
```

No external dependencies beyond Python stdlib + existing project utils.

---

## Integration Points

### observation_daily.py

At end of `main()`, after writing observation summary:
```python
from reporting.web_report_generator import generate_all
generate_all()
```

### intraday_observation.py

At end of `main()`, after writing slot JSON:
```python
from reporting.web_report_generator import generate_all
generate_all()
```

Errors in `generate_all()` are caught and logged but do NOT cause the observation run to fail.

---

## Systemd Service

**`scripts/start_web_server.sh`** — 動態取得 Tailscale IP 後啟動 server：

```bash
#!/bin/bash
TS_IP=$(ip addr show tailscale0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
if [ -z "$TS_IP" ]; then
  echo "tailscale0 not available" >&2
  exit 1
fi
exec python3 -m http.server 8080 --bind "$TS_IP"
```

**`~/.config/systemd/user/investment-os-web.service`**

```ini
[Unit]
Description=Investment OS Web Dashboard — HTTP server on Tailscale
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/shimeon/investment_os/reports/web
ExecStart=/home/shimeon/investment_os/scripts/start_web_server.sh
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
```

Access URL: `http://<tailscale-ip>:8080/status.html`（目前 IP：`100.92.154.55`）

---

## Out of Scope

- Authentication / login
- Telegram notifications (next iteration)
- Real-time WebSocket updates (static HTML only)
- Historical price charts or graphics

---

## Acceptance Criteria

- [ ] `reports/web/` directory created and all three HTML files present after first run
- [ ] Navigation bar on all three pages links correctly
- [ ] `status.html` reflects latest `signal_snapshot.json` data
- [ ] `history.html` shows one row per past observation run
- [ ] `replay.html` shows correct slot data for available dates
- [ ] HTTP server starts on boot, accessible at `http://100.92.154.55:8080/status.html`
- [ ] Generator errors do not break pipeline runs
- [ ] Pages render correctly in mobile browser
