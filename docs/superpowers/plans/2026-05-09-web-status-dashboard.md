# Web Status Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a multi-page static HTML dashboard after each pipeline run, served via HTTP on the Tailscale interface so the user can check daily results and accumulated data from any connected device.

**Architecture:** A single generator module (`reporting/web_report_generator.py`) reads existing JSON/Markdown data files and writes three HTML pages to `reports/web/`. Functions accept data as parameters so they can be tested without touching production files. A persistent systemd service runs `python3 -m http.server` bound to the Tailscale IP. Both `jobs/observation_daily.py` and `jobs/intraday_observation.py` call `generate_all()` at the end of each run; errors are caught and logged without failing the observation.

**Tech Stack:** Python 3 stdlib only (json, re, pathlib, datetime). pytest for tests. systemd user service for HTTP server.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `reporting/web_report_generator.py` | CSS, helpers, all three page generators, `generate_all()` |
| Create | `tests/test_web_report_generator.py` | Unit tests for every generator function |
| Create | `scripts/start_web_server.sh` | Detects Tailscale IP, starts http.server on port 8080 |
| Create | `~/.config/systemd/user/investment-os-web.service` | Keeps HTTP server alive |
| Modify | `jobs/observation_daily.py` | Call `generate_all()` at end of `main()` |
| Modify | `jobs/intraday_observation.py` | Call `generate_all()` at end of `main()` |

---

## Task 1: Scaffolding — CSS, helpers, and shared HTML utilities

**Files:**
- Create: `reporting/web_report_generator.py`
- Create: `tests/test_web_report_generator.py`

- [ ] **Step 1.1: Write failing tests for scaffolding helpers**

Create `tests/test_web_report_generator.py`:

```python
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reporting.web_report_generator import _nav_bar, _badge, _html_page, _load_json


def test_nav_bar_marks_active():
    html = _nav_bar("status")
    assert 'class="active"' in html
    assert "今日狀態" in html
    assert "歷史記錄" in html
    assert "Replay" in html


def test_nav_bar_active_link_is_not_href():
    html = _nav_bar("history")
    # active page should have class="active"
    assert 'href="history.html" class="active"' in html


def test_badge_pass_green():
    html = _badge("PASS")
    assert "green" in html
    assert "PASS" in html


def test_badge_fail_red():
    html = _badge("FAIL")
    assert "red" in html


def test_badge_unknown_grey():
    html = _badge("UNKNOWN")
    assert "grey" in html


def test_html_page_has_structure():
    body = "<p>test</p>"
    html = _html_page("Test Title", "status", body)
    assert "<!DOCTYPE html>" in html
    assert "Test Title" in html
    assert "<p>test</p>" in html
    assert "Investment OS" in html  # nav bar present


def test_load_json_missing_returns_empty(tmp_path):
    result = _load_json(tmp_path / "nonexistent.json")
    assert result == {}


def test_load_json_reads_file(tmp_path):
    p = tmp_path / "test.json"
    p.write_text('{"key": "value"}', encoding="utf-8")
    assert _load_json(p) == {"key": "value"}
```

- [ ] **Step 1.2: Run tests to verify they fail**

```bash
cd /home/shimeon/investment_os
python3 -m pytest tests/test_web_report_generator.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'reporting.web_report_generator'`

- [ ] **Step 1.3: Create `reporting/web_report_generator.py` with helpers**

```python
#!/usr/bin/env python3
"""Investment OS — Web Status Dashboard generator."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "reports" / "web"
SIGNAL_SNAPSHOT = ROOT / "data" / "processed" / "signal_snapshot.json"
MAINLINE_SNAPSHOT = ROOT / "data" / "processed" / "mainline_snapshot.json"
OBSERVATION_DIR = ROOT / "reports" / "observation"
DAILY_REPORT_DIR = ROOT / "reports" / "daily"
INTRADAY_DAILY_DIR = ROOT / "data" / "observations" / "daily"
INTRADAY_SLOT_DIR = ROOT / "data" / "observations" / "intraday"

_CSS = """
body{font-family:monospace;background:#1a1a1a;color:#d4d4d4;margin:0;padding:0}
nav{background:#2a2a2a;padding:10px 20px;border-bottom:1px solid #444;display:flex;align-items:center;gap:20px;flex-wrap:wrap}
.brand{font-weight:bold;color:#fff;margin-right:10px}
nav a{color:#aaa;text-decoration:none}
nav a.active{color:#fff;border-bottom:2px solid #5af}
nav a:hover{color:#fff}
.ts{margin-left:auto;color:#666;font-size:.85em}
main{padding:20px;max-width:960px}
h1{color:#ccc;margin-bottom:4px}
h2{color:#aaa;border-bottom:1px solid #333;padding-bottom:4px;margin-top:24px}
table{border-collapse:collapse;width:100%;margin-bottom:16px}
th{text-align:left;color:#888;border-bottom:1px solid #333;padding:4px 8px}
td{padding:4px 8px;border-bottom:1px solid #222}
.badge{padding:2px 8px;border-radius:3px;font-size:.85em}
.green{background:#1a3d1a;color:#5f5}
.red{background:#3d1a1a;color:#f55}
.orange{background:#3d2a00;color:#fa5}
.grey{background:#2a2a2a;color:#888}
details>summary{cursor:pointer;color:#aaa;padding:4px 8px}
details[open]{background:#222;padding:8px;margin-bottom:8px}
.banner{background:#2a2a2a;color:#888;padding:20px;text-align:center;margin:20px 0;border:1px solid #333}
select{background:#2a2a2a;color:#d4d4d4;border:1px solid #444;padding:4px 8px}
"""


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _nav_bar(active: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    pages = [("status", "status.html", "今日狀態"),
             ("history", "history.html", "歷史記錄"),
             ("replay", "replay.html", "Replay")]
    links = ""
    for key, href, label in pages:
        cls = ' class="active"' if key == active else ""
        links += f'<a href="{href}"{cls}>{label}</a> '
    return f'<nav><span class="brand">Investment OS</span>{links}<span class="ts">最後更新: {now}</span></nav>'


def _badge(status: str) -> str:
    s = (status or "").upper()
    color = {"PASS": "green", "FAIL": "red", "WARN": "orange",
             "SKIPPED": "grey", "SKIP": "grey", "UNKNOWN": "grey"}.get(s, "grey")
    return f'<span class="badge {color}">{status}</span>'


def _html_page(title: str, active: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Investment OS</title>
<style>{_CSS}</style>
</head>
<body>
{_nav_bar(active)}
<main>{body}</main>
</body>
</html>"""
```

- [ ] **Step 1.4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_web_report_generator.py -v 2>&1 | tail -15
```

Expected: `7 passed`

- [ ] **Step 1.5: Commit**

```bash
git add reporting/web_report_generator.py tests/test_web_report_generator.py
git commit -m "feat(web): add web report generator scaffolding with helpers"
```

---

## Task 2: `generate_status_page()`

**Files:**
- Modify: `reporting/web_report_generator.py`
- Modify: `tests/test_web_report_generator.py`

- [ ] **Step 2.1: Write failing tests**

Append to `tests/test_web_report_generator.py`:

```python
from reporting.web_report_generator import generate_status_page

_SIGNAL = {
    "date": "2026-05-08",
    "generated_at": "2026-05-08 16:00:11",
    "status": "PASS",
    "market_status": "OPEN",
    "data_mode": "OBSERVATION",
    "market_context": {"markets": {"TW": {"status": "OPEN"}, "US": {"status": "OPEN"}}},
    "checks": [
        {"label": "daily_decision_dashboard", "status": "PASS"},
        {"label": "pipeline_main_v1", "status": "PASS"},
    ],
    "watchlist_count": 27,
    "holdings_count": 7,
}

_MAINLINE = {
    "market_state": "RANGE",
    "market_score": 0.007,
    "vix_value": 17.2,
    "ranked": [
        {"ticker": "2464.TW", "name": "盟立", "sector": "Equipment",
         "signal": "BUY", "score": 151.4},
        {"ticker": "2356.TW", "name": "英業達", "sector": "Server",
         "signal": "BUY", "score": 145.5},
    ],
    "decisions": {
        "2464.TW": {"action": "BUY", "reason": "REDUCED_BY_MARKET", "position_size": 0.1},
    },
}


def test_generate_status_page_creates_file(tmp_path):
    generate_status_page(web_dir=tmp_path, signal=_SIGNAL, mainline=_MAINLINE)
    assert (tmp_path / "status.html").exists()


def test_generate_status_page_contains_status_badge(tmp_path):
    generate_status_page(web_dir=tmp_path, signal=_SIGNAL, mainline=_MAINLINE)
    html = (tmp_path / "status.html").read_text()
    assert "PASS" in html
    assert "green" in html


def test_generate_status_page_contains_candidates(tmp_path):
    generate_status_page(web_dir=tmp_path, signal=_SIGNAL, mainline=_MAINLINE)
    html = (tmp_path / "status.html").read_text()
    assert "2464.TW" in html
    assert "盟立" in html
    assert "151.4" in html


def test_generate_status_page_contains_decisions(tmp_path):
    generate_status_page(web_dir=tmp_path, signal=_SIGNAL, mainline=_MAINLINE)
    html = (tmp_path / "status.html").read_text()
    assert "REDUCED_BY_MARKET" in html


def test_generate_status_page_market_closed_shows_banner(tmp_path):
    closed_signal = {**_SIGNAL, "market_status": "CLOSED_WEEKEND"}
    generate_status_page(web_dir=tmp_path, signal=closed_signal, mainline={})
    html = (tmp_path / "status.html").read_text()
    assert "休市" in html
    assert "2464.TW" not in html


def test_generate_status_page_contains_checks(tmp_path):
    generate_status_page(web_dir=tmp_path, signal=_SIGNAL, mainline=_MAINLINE)
    html = (tmp_path / "status.html").read_text()
    assert "daily_decision_dashboard" in html
    assert "pipeline_main_v1" in html
```

- [ ] **Step 2.2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_web_report_generator.py -k "status" -v 2>&1 | tail -10
```

Expected: `ImportError` or `6 failed`

- [ ] **Step 2.3: Implement `generate_status_page()`**

Add to `reporting/web_report_generator.py`:

```python
def generate_status_page(
    web_dir: Path = WEB_DIR,
    signal: dict | None = None,
    mainline: dict | None = None,
) -> None:
    web_dir.mkdir(parents=True, exist_ok=True)
    if signal is None:
        signal = _load_json(SIGNAL_SNAPSHOT)
    if mainline is None:
        mainline = _load_json(MAINLINE_SNAPSHOT)

    status = signal.get("status", "UNKNOWN")
    generated_at = signal.get("generated_at", "N/A")
    data_mode = signal.get("data_mode", "N/A")
    market_status = signal.get("market_status", "UNKNOWN")
    market_closed = market_status in ("CLOSED_WEEKEND", "CLOSED_HOLIDAY", "MARKET_CLOSED")

    markets = (signal.get("market_context") or {}).get("markets", {})
    tw_s = (markets.get("TW") or {}).get("status", "N/A")
    us_s = (markets.get("US") or {}).get("status", "N/A")

    m_state = mainline.get("market_state", "N/A")
    m_score = mainline.get("market_score", "N/A")
    vix = mainline.get("vix_value", "N/A")
    if isinstance(vix, float):
        vix = f"{vix:.2f}"

    ranked = mainline.get("ranked", [])
    decisions = mainline.get("decisions", {})
    checks = signal.get("checks", [])

    body = f"<h1>今日狀態 {_badge(status)}</h1>"
    body += f"<p>執行時間: {generated_at} &nbsp;|&nbsp; 模式: {data_mode}</p>"

    if market_closed:
        body += f'<div class="banner">市場休市 ({tw_s})</div>'
    else:
        body += "<h2>市場概況</h2>"
        body += ("<table><tr><th>市場狀態</th><th>Score</th><th>VIX</th>"
                 "<th>TW</th><th>US</th></tr>"
                 f"<tr><td>{m_state}</td><td>{m_score}</td><td>{vix}</td>"
                 f"<td>{tw_s}</td><td>{us_s}</td></tr></table>")

        body += "<h2>Top 候選</h2>"
        body += ("<table><tr><th>Rank</th><th>Ticker</th><th>Name</th>"
                 "<th>Score</th><th>Signal</th></tr>")
        for i, r in enumerate(ranked[:10], 1):
            body += (f"<tr><td>{i}</td><td>{r.get('ticker','')}</td>"
                     f"<td>{r.get('name','')}</td><td>{r.get('score','')}</td>"
                     f"<td>{r.get('signal','')}</td></tr>")
        body += "</table>"

        if decisions:
            body += "<h2>Decisions</h2>"
            body += "<table><tr><th>Ticker</th><th>Action</th><th>Position</th><th>Reason</th></tr>"
            for ticker, d in decisions.items():
                pct = f"{d.get('position_size', 0)*100:.0f}%" if d.get('position_size') else "N/A"
                body += (f"<tr><td>{ticker}</td><td>{d.get('action','')}</td>"
                         f"<td>{pct}</td><td>{d.get('reason','')}</td></tr>")
            body += "</table>"

    body += "<h2>Pipeline 子程序</h2>"
    body += "<table><tr><th>子程序</th><th>狀態</th></tr>"
    for c in checks:
        body += f"<tr><td>{c.get('label','')}</td><td>{_badge(c.get('status','UNKNOWN'))}</td></tr>"
    body += "</table>"

    (web_dir / "status.html").write_text(_html_page("今日狀態", "status", body), encoding="utf-8")
```

- [ ] **Step 2.4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_web_report_generator.py -k "status" -v 2>&1 | tail -10
```

Expected: `6 passed`

- [ ] **Step 2.5: Commit**

```bash
git add reporting/web_report_generator.py tests/test_web_report_generator.py
git commit -m "feat(web): add generate_status_page"
```

---

## Task 3: `generate_history_page()`

**Files:**
- Modify: `reporting/web_report_generator.py`
- Modify: `tests/test_web_report_generator.py`

- [ ] **Step 3.1: Write failing tests**

Append to `tests/test_web_report_generator.py`:

```python
from reporting.web_report_generator import generate_history_page

_OBS_SUMMARY_MD = """\
# Investment OS Observation Summary - 2026-05-08

## Final Status

PASS

## Market Gate

- TW market status: OPEN

## Stable Observation Record

- Counts as stable observation record: YES
- Type: OPEN-day PASS
- Reason: All subprocesses PASS

*Generated at: 2026-05-08 16:00:11*
"""

_DAILY_REPORT_MD = """\
# Investment OS Daily Report - 2026-05-08

## Human Summary

- Market state: **RANGE** | Score: 0.0070 | VIX: 17.20

**Top 3 candidates:**

1. 2464.TW 盟立 — Score: 151.40 | Signal: BUY
"""


def test_generate_history_page_creates_file(tmp_path):
    obs_dir = tmp_path / "observation"
    daily_dir = tmp_path / "daily"
    obs_dir.mkdir(); daily_dir.mkdir()
    (obs_dir / "2026-05-08_observation_summary.md").write_text(_OBS_SUMMARY_MD)
    (daily_dir / "2026-05-08_daily_report.md").write_text(_DAILY_REPORT_MD)

    generate_history_page(web_dir=tmp_path, obs_dir=obs_dir, daily_dir=daily_dir)
    assert (tmp_path / "history.html").exists()


def test_generate_history_page_shows_row(tmp_path):
    obs_dir = tmp_path / "observation"
    daily_dir = tmp_path / "daily"
    obs_dir.mkdir(); daily_dir.mkdir()
    (obs_dir / "2026-05-08_observation_summary.md").write_text(_OBS_SUMMARY_MD)
    (daily_dir / "2026-05-08_daily_report.md").write_text(_DAILY_REPORT_MD)

    generate_history_page(web_dir=tmp_path, obs_dir=obs_dir, daily_dir=daily_dir)
    html = (tmp_path / "history.html").read_text()
    assert "2026-05-08" in html
    assert "PASS" in html
    assert "RANGE" in html
    assert "17.20" in html
    assert "2464.TW" in html


def test_generate_history_page_empty_dir(tmp_path):
    obs_dir = tmp_path / "observation"
    obs_dir.mkdir()
    generate_history_page(web_dir=tmp_path, obs_dir=obs_dir, daily_dir=tmp_path / "daily")
    html = (tmp_path / "history.html").read_text()
    assert "歷史記錄" in html
    assert "尚無資料" in html
```

- [ ] **Step 3.2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_web_report_generator.py -k "history" -v 2>&1 | tail -10
```

Expected: `3 failed`

- [ ] **Step 3.3: Implement `generate_history_page()`**

Add to `reporting/web_report_generator.py`:

```python
def _parse_obs_summary(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    date = re.search(r"Observation Summary - (\d{4}-\d{2}-\d{2})", text)
    status = re.search(r"## Final Status\s+(\w+)", text)
    stable_type = re.search(r"- Type: (.+)", text)
    generated = re.search(r"\*Generated at: (.+)\*", text)
    # Extract subprocess results for expandable detail
    subproc_lines = re.findall(r"- (\w[\w_]+): (PASS|FAIL|UNKNOWN|SKIPPED[^)]*)", text)
    return {
        "date": date.group(1) if date else path.stem[:10],
        "status": status.group(1) if status else "UNKNOWN",
        "stable_type": stable_type.group(1).strip() if stable_type else "N/A",
        "generated_at": generated.group(1).strip() if generated else "N/A",
        "subproc": subproc_lines,
    }


def _parse_daily_report(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    market = re.search(r"Market state: \*\*(\w+)\*\*", text)
    score = re.search(r"Score: ([\d.]+)", text)
    vix = re.search(r"VIX: ([\d.]+)", text)
    top1 = re.search(r"1\. (\S+) (.+?) —", text)
    return {
        "market_state": market.group(1) if market else "N/A",
        "score": score.group(1) if score else "N/A",
        "vix": vix.group(1) if vix else "N/A",
        "top1": f"{top1.group(1)} {top1.group(2)}" if top1 else "N/A",
    }


def generate_history_page(
    web_dir: Path = WEB_DIR,
    obs_dir: Path = OBSERVATION_DIR,
    daily_dir: Path = DAILY_REPORT_DIR,
) -> None:
    web_dir.mkdir(parents=True, exist_ok=True)

    obs_files = sorted(obs_dir.glob("*_observation_summary.md"), reverse=True)

    body = "<h1>歷史觀測記錄</h1>"

    if not obs_files:
        body += '<div class="banner">尚無資料</div>'
        (web_dir / "history.html").write_text(_html_page("歷史記錄", "history", body), encoding="utf-8")
        return

    body += ("<table><tr><th>日期</th><th>狀態</th><th>市場狀態</th>"
             "<th>Score</th><th>VIX</th><th>Top 1 候選</th><th>觀測類型</th></tr>")

    for obs_path in obs_files:
        obs = _parse_obs_summary(obs_path)
        date = obs["date"]
        daily_path = daily_dir / f"{date}_daily_report.md"
        daily = _parse_daily_report(daily_path)

        # Build expandable subprocess detail
        detail = ""
        if obs["subproc"]:
            rows = "".join(
                f"<tr><td>{lbl}</td><td>{_badge(st)}</td></tr>"
                for lbl, st in obs["subproc"]
            )
            detail = (f"<details><summary>子程序詳情</summary>"
                      f"<table>{rows}</table></details>")

        body += (f"<tr><td>{date}</td><td>{_badge(obs['status'])}</td>"
                 f"<td>{daily.get('market_state','N/A')}</td>"
                 f"<td>{daily.get('score','N/A')}</td>"
                 f"<td>{daily.get('vix','N/A')}</td>"
                 f"<td>{daily.get('top1','N/A')}</td>"
                 f"<td>{obs['stable_type']}{detail}</td></tr>")
    body += "</table>"

    (web_dir / "history.html").write_text(_html_page("歷史記錄", "history", body), encoding="utf-8")
```

- [ ] **Step 3.4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_web_report_generator.py -k "history" -v 2>&1 | tail -10
```

Expected: `3 passed`

- [ ] **Step 3.5: Commit**

```bash
git add reporting/web_report_generator.py tests/test_web_report_generator.py
git commit -m "feat(web): add generate_history_page"
```

---

## Task 4: `generate_replay_page()`

**Files:**
- Modify: `reporting/web_report_generator.py`
- Modify: `tests/test_web_report_generator.py`

- [ ] **Step 4.1: Write failing tests**

Append to `tests/test_web_report_generator.py`:

```python
from reporting.web_report_generator import generate_replay_page

_DAILY_OBS_JSON = {
    "date": "2026-05-08",
    "total_slots": 3,
    "status_counts": {"PASS": 3},
    "top_persistence": [{"ticker": "2356.TW", "appearances": 3}],
    "warn_l1_l4_pass": [{"ticker": "2356.TW", "name": "英業達",
                          "warn_reason": "RANGE market", "score": 145.5}],
    "next_day_watchlist": [{"ticker": "2356.TW", "name": "英業達",
                             "appearances": 3, "last_rank": 2,
                             "last_score": 145.5, "last_p1": "ENTRY_REDUCED"}],
}

_SLOT_JSON = {
    "date": "2026-05-08",
    "slot": "market_open",
    "run_time": "09:15:00",
    "runtime_status": "PASS",
    "market": {"market_state": "RANGE"},
    "candidates": [
        {"ticker": "2356.TW", "name": "英業達", "rank": 1,
         "score": 145.5, "signal": "BUY", "p1_result": "ENTRY_REDUCED",
         "L0": "WARN", "L1": "PASS", "L2": "PASS", "L3": "PASS", "L4": "PASS",
         "block_reason": None, "warn_reason": "RANGE market"},
    ],
}


def test_generate_replay_page_creates_file(tmp_path):
    daily_dir = tmp_path / "daily"
    slot_dir = tmp_path / "intraday" / "2026-05-08"
    daily_dir.mkdir(parents=True); slot_dir.mkdir(parents=True)
    (daily_dir / "2026-05-08_observation_summary.json").write_text(
        json.dumps(_DAILY_OBS_JSON), encoding="utf-8")
    (slot_dir / "0915_market_open_observation.json").write_text(
        json.dumps(_SLOT_JSON), encoding="utf-8")

    generate_replay_page(web_dir=tmp_path, daily_obs_dir=daily_dir, slot_dir=tmp_path / "intraday")
    assert (tmp_path / "replay.html").exists()


def test_generate_replay_page_shows_watchlist(tmp_path):
    daily_dir = tmp_path / "daily"
    slot_dir = tmp_path / "intraday" / "2026-05-08"
    daily_dir.mkdir(parents=True); slot_dir.mkdir(parents=True)
    (daily_dir / "2026-05-08_observation_summary.json").write_text(
        json.dumps(_DAILY_OBS_JSON), encoding="utf-8")
    (slot_dir / "0915_market_open_observation.json").write_text(
        json.dumps(_SLOT_JSON), encoding="utf-8")

    generate_replay_page(web_dir=tmp_path, daily_obs_dir=daily_dir, slot_dir=tmp_path / "intraday")
    html = (tmp_path / "replay.html").read_text()
    assert "2356.TW" in html
    assert "英業達" in html
    assert "ENTRY_REDUCED" in html


def test_generate_replay_page_no_data(tmp_path):
    generate_replay_page(web_dir=tmp_path,
                         daily_obs_dir=tmp_path / "daily",
                         slot_dir=tmp_path / "intraday")
    html = (tmp_path / "replay.html").read_text()
    assert "Replay" in html
    assert "尚無資料" in html


```

Ensure `import json` is at the top of `tests/test_web_report_generator.py` (add after existing imports if not present).
```

- [ ] **Step 4.2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_web_report_generator.py -k "replay" -v 2>&1 | tail -10
```

Expected: `3 failed`

- [ ] **Step 4.3: Implement `generate_replay_page()`**

Add to `reporting/web_report_generator.py`:

```python
def generate_replay_page(
    web_dir: Path = WEB_DIR,
    daily_obs_dir: Path = INTRADAY_DAILY_DIR,
    slot_dir: Path = INTRADAY_SLOT_DIR,
) -> None:
    web_dir.mkdir(parents=True, exist_ok=True)

    daily_files = sorted(daily_obs_dir.glob("*_observation_summary.json"), reverse=True)

    body = "<h1>Intraday Replay</h1>"

    if not daily_files:
        body += '<div class="banner">尚無資料</div>'
        (web_dir / "replay.html").write_text(_html_page("Replay", "replay", body), encoding="utf-8")
        return

    # Date selector
    dates = [f.stem.replace("_observation_summary", "") for f in daily_files]
    latest = dates[0]
    options = "".join(
        f'<option value="{d}"{" selected" if d == latest else ""}>{d}</option>'
        for d in dates
    )
    body += (f'<h2>日期選擇</h2><select id="datesel" onchange="showDate(this.value)">'
             f'{options}</select>')

    # Per-date sections
    for date in dates:
        daily_path = daily_obs_dir / f"{date}_observation_summary.json"
        summary = _load_json(daily_path)
        slot_date_dir = slot_dir / date
        slot_files = sorted(slot_date_dir.glob("*.json")) if slot_date_dir.exists() else []

        display = "block" if date == latest else "none"
        section = f'<div id="date-{date}" style="display:{display}">'

        # Summary stats
        sc = summary.get("status_counts", {})
        total = summary.get("total_slots", 0)
        section += (f"<h2>{date} — {total} slots "
                    f"(PASS:{sc.get('PASS',0)} FAIL:{sc.get('FAIL',0)})</h2>")

        # Slot table
        if slot_files:
            section += ("<table><tr><th>Slot</th><th>時間</th><th>Top 1</th>"
                        "<th>Score</th><th>P1 結果</th><th>市場</th></tr>")
            for sf in slot_files:
                sd = _load_json(sf)
                cands = sd.get("candidates", [])
                top = cands[0] if cands else {}
                mkt = (sd.get("market") or {}).get("market_state", "N/A")
                section += (f"<tr><td>{sd.get('slot','')}</td>"
                             f"<td>{sd.get('run_time','')}</td>"
                             f"<td>{top.get('ticker','')} {top.get('name','')}</td>"
                             f"<td>{top.get('score','')}</td>"
                             f"<td>{top.get('p1_result','')}</td>"
                             f"<td>{mkt}</td></tr>")
            section += "</table>"

        # Persistence ranking
        persist = summary.get("top_persistence", [])
        if persist:
            section += "<h2>Persistence Ranking</h2>"
            section += "<table><tr><th>Ticker</th><th>出現次數</th><th>warn_l1_l4_pass</th></tr>"
            warn_tickers = {w["ticker"] for w in summary.get("warn_l1_l4_pass", [])}
            for p in persist[:10]:
                warn = "✓" if p["ticker"] in warn_tickers else ""
                section += (f"<tr><td>{p['ticker']}</td>"
                             f"<td>{p['appearances']}/{total}</td>"
                             f"<td>{warn}</td></tr>")
            section += "</table>"

        # Next-day watchlist
        wl = summary.get("next_day_watchlist", [])
        if wl:
            section += "<h2>明日 Watchlist</h2>"
            section += ("<table><tr><th>Ticker</th><th>Name</th><th>出現</th>"
                        "<th>最後排名</th><th>最後 P1</th></tr>")
            for w in wl:
                section += (f"<tr><td>{w.get('ticker','')}</td><td>{w.get('name','')}</td>"
                             f"<td>{w.get('appearances','')}/{total}</td>"
                             f"<td>{w.get('last_rank','')}</td>"
                             f"<td>{w.get('last_p1','')}</td></tr>")
            section += "</table>"

        section += "</div>"
        body += section

    # JS for date switching
    body += """<script>
function showDate(d){
  document.querySelectorAll('[id^="date-"]').forEach(el=>el.style.display='none');
  var el=document.getElementById('date-'+d);
  if(el) el.style.display='block';
}
</script>"""

    (web_dir / "replay.html").write_text(_html_page("Replay", "replay", body), encoding="utf-8")
```

- [ ] **Step 4.4: Add missing `import json` to test file top**

Ensure `tests/test_web_report_generator.py` has at the top (after existing imports):

```python
import json
```

- [ ] **Step 4.5: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_web_report_generator.py -k "replay" -v 2>&1 | tail -10
```

Expected: `3 passed`

- [ ] **Step 4.6: Commit**

```bash
git add reporting/web_report_generator.py tests/test_web_report_generator.py
git commit -m "feat(web): add generate_replay_page"
```

---

## Task 5: `generate_all()` with error handling

**Files:**
- Modify: `reporting/web_report_generator.py`
- Modify: `tests/test_web_report_generator.py`

- [ ] **Step 5.1: Write failing tests**

Append to `tests/test_web_report_generator.py`:

```python
from reporting.web_report_generator import generate_all


def test_generate_all_creates_all_three_files(tmp_path):
    generate_all(web_dir=tmp_path)
    assert (tmp_path / "status.html").exists()
    assert (tmp_path / "history.html").exists()
    assert (tmp_path / "replay.html").exists()


def test_generate_all_does_not_raise_on_missing_data(tmp_path):
    # Should not raise even when all data files are missing
    generate_all(web_dir=tmp_path)
```

- [ ] **Step 5.2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_web_report_generator.py -k "generate_all" -v 2>&1 | tail -10
```

Expected: `2 failed`

- [ ] **Step 5.3: Implement `generate_all()`**

Add to `reporting/web_report_generator.py`:

```python
def generate_all(web_dir: Path = WEB_DIR) -> None:
    for fn, kwargs in [
        (generate_status_page, {"web_dir": web_dir}),
        (generate_history_page, {"web_dir": web_dir}),
        (generate_replay_page, {"web_dir": web_dir}),
    ]:
        try:
            fn(**kwargs)
        except Exception as e:
            print(f"[WARN] web_report_generator: {fn.__name__} failed: {e}")
```

- [ ] **Step 5.4: Run full test suite**

```bash
python3 -m pytest tests/test_web_report_generator.py -v 2>&1 | tail -20
```

Expected: all tests pass (should be ~21 tests)

- [ ] **Step 5.5: Commit**

```bash
git add reporting/web_report_generator.py tests/test_web_report_generator.py
git commit -m "feat(web): add generate_all with error isolation"
```

---

## Task 6: Integration in `jobs/observation_daily.py`

**Files:**
- Modify: `jobs/observation_daily.py:315-360` (end of `main()`)

- [ ] **Step 6.1: Add `generate_all()` call at end of `main()`**

In `jobs/observation_daily.py`, locate the final lines of `main()`:

```python
    stable_str = "YES" if stable["stable"] else "NO"
    print(f"[{NOW}] === Observation complete: {final_status} | stable={stable_str} | type={stable['type']} ===")
    return 0 if stable["stable"] else 1
```

Replace with:

```python
    stable_str = "YES" if stable["stable"] else "NO"
    print(f"[{NOW}] === Observation complete: {final_status} | stable={stable_str} | type={stable['type']} ===")

    try:
        from reporting.web_report_generator import generate_all
        generate_all()
        print(f"[{NOW}] [WEB] HTML dashboard updated")
    except Exception as e:
        print(f"[{NOW}] [WARN] web dashboard update failed: {e}")

    return 0 if stable["stable"] else 1
```

- [ ] **Step 6.2: Smoke test**

```bash
cd /home/shimeon/investment_os
python3 -c "
from reporting.web_report_generator import generate_all
generate_all()
print('OK')
import os
for f in ['status.html','history.html','replay.html']:
    size = os.path.getsize(f'reports/web/{f}')
    print(f'{f}: {size} bytes')
"
```

Expected: three files created, each > 500 bytes

- [ ] **Step 6.3: Verify HTML in browser check (spot check)**

```bash
grep -c "<tr>" reports/web/history.html
grep "PASS\|FAIL" reports/web/status.html | head -3
```

Expected: `history.html` has at least 2 `<tr>` tags; `status.html` contains PASS badge

- [ ] **Step 6.4: Commit**

```bash
git add jobs/observation_daily.py
git commit -m "feat(web): integrate web dashboard generation into observation_daily"
```

---

## Task 7: Integration in `jobs/intraday_observation.py`

**Files:**
- Modify: `jobs/intraday_observation.py` (end of `main()`)

- [ ] **Step 7.1: Find the end of `main()` in intraday_observation.py**

```bash
grep -n "return\|=== Intraday" jobs/intraday_observation.py | tail -10
```

Note the line number of the final `return` statement.

- [ ] **Step 7.2: Add `generate_all()` call before the final return**

Find this block at the end of `main()` (exact lines may vary — use grep output from 7.1):

```python
    print(f"[{NOW}] === Intraday observation complete: {slot} | {final_status} ===")
    return 0 if final_status in ("PASS", "PARTIAL") else 1
```

Replace with:

```python
    print(f"[{NOW}] === Intraday observation complete: {slot} | {final_status} ===")

    try:
        from reporting.web_report_generator import generate_all
        generate_all()
        print(f"[{NOW}] [WEB] HTML dashboard updated")
    except Exception as e:
        print(f"[{NOW}] [WARN] web dashboard update failed: {e}")

    return 0 if final_status in ("PASS", "PARTIAL") else 1
```

- [ ] **Step 7.3: Verify intraday_observation still imports cleanly**

```bash
python3 -c "import jobs.intraday_observation; print('OK')"
```

Expected: `OK`

- [ ] **Step 7.4: Commit**

```bash
git add jobs/intraday_observation.py
git commit -m "feat(web): integrate web dashboard generation into intraday_observation"
```

---

## Task 8: HTTP server script and systemd service

**Files:**
- Create: `scripts/start_web_server.sh`
- Create: `~/.config/systemd/user/investment-os-web.service`

- [ ] **Step 8.1: Create `scripts/start_web_server.sh`**

```bash
#!/bin/bash
TS_IP=$(ip addr show tailscale0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
if [ -z "$TS_IP" ]; then
    echo "[ERROR] tailscale0 interface not found or has no IP" >&2
    exit 1
fi
echo "[INFO] Starting HTTP server on $TS_IP:8080"
exec python3 -m http.server 8080 --bind "$TS_IP"
```

```bash
chmod +x /home/shimeon/investment_os/scripts/start_web_server.sh
```

- [ ] **Step 8.2: Test the script manually (ensure tailscale0 is up)**

```bash
cd /home/shimeon/investment_os/reports/web
/home/shimeon/investment_os/scripts/start_web_server.sh &
sleep 1
curl -s "http://100.92.154.55:8080/status.html" | head -5
kill %1
```

Expected: `<!DOCTYPE html>` in first 5 lines

- [ ] **Step 8.3: Create systemd service**

```bash
cat > ~/.config/systemd/user/investment-os-web.service << 'EOF'
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
EOF
```

- [ ] **Step 8.4: Enable and start the service**

```bash
systemctl --user daemon-reload
systemctl --user enable investment-os-web.service
systemctl --user start investment-os-web.service
systemctl --user status investment-os-web.service
```

Expected: `Active: active (running)`

- [ ] **Step 8.5: Verify end-to-end access**

```bash
curl -s "http://100.92.154.55:8080/status.html" | grep -c "<tr>"
```

Expected: number ≥ 2

- [ ] **Step 8.6: Commit**

```bash
git add scripts/start_web_server.sh
git commit -m "feat(web): add HTTP server script and systemd service for Tailscale dashboard"
```

---

## Acceptance Checklist

- [ ] `reports/web/status.html`, `history.html`, `replay.html` all exist after running `generate_all()`
- [ ] `status.html` reflects current `signal_snapshot.json` and `mainline_snapshot.json`
- [ ] `history.html` has one row per `reports/observation/*_observation_summary.md` file
- [ ] `replay.html` shows slot data and watchlist for available dates; date selector works
- [ ] All `test_web_report_generator.py` tests pass
- [ ] `investment-os-web.service` is active and accessible at `http://100.92.154.55:8080/status.html`
- [ ] Generator errors do not cause pipeline runs to fail
- [ ] Pages render on mobile (no horizontal scroll on 375px width)
