# Replay Builder Auto-Integration + US Market Jobs — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auto-integrate `observation_replay_builder` into every intraday slot so `replay.html` always shows today's data, and add US market observation (3 slots) that runs through the same pipeline.

**Architecture:** Extend `intraday_observation.py` with `--market tw|us` argparse flag; `us` mode uses ET-based `session_date` to avoid cross-midnight date errors, routes to `daily_run_us.py`, and applies the US market guard from `market_calendar.json`. After each slot (TW or US), `build_summary(session_date_str)` + `generate_all()` auto-update the replay page. Three new systemd timers (21:30/01:00/04:30 CST) cover the US session.

**Tech Stack:** Python 3.11+ (`zoneinfo` stdlib), systemd timers, existing `utils.market_calendar`, existing `jobs.observation_replay_builder.build_summary`.

---

## File Map

| Action | Path |
|--------|------|
| Modify | `jobs/intraday_observation.py` |
| Create | `jobs/daily_run_us.py` |
| Modify | `scripts/run_intraday_observation.sh` |
| Create | `systemd/investment-os-intraday-us-market-open.timer` |
| Create | `systemd/investment-os-intraday-us-midday.timer` |
| Create | `systemd/investment-os-intraday-us-post-close.timer` |
| Create | `tests/test_intraday_us.py` |

---

## Task 0: Immediate backfill — fix today's replay data

**Files:** none (one-shot command)

- [ ] **Step 1: Run replay builder for today**

```bash
cd /home/shimeon/investment_os
python3 -m jobs.observation_replay_builder 2026-05-11
```

Expected output:
```
[observation_replay_builder] Building summary for 2026-05-11...
[observation_replay_builder] Written: .../data/observations/daily/2026-05-11_observation_summary.json
[observation_replay_builder] total_slots=7 status={'PASS': ...}
```

- [ ] **Step 2: Verify replay.html updates**

```bash
python3 -c "
from reporting.web_report_generator import generate_replay_page
generate_replay_page()
print('OK')
"
```

Then open `reports/web/replay.html` and confirm 2026-05-11 appears in the date selector with 7 slots.

- [ ] **Step 3: Commit backfilled data**

```bash
git add data/observations/daily/2026-05-11_observation_summary.json reports/web/replay.html
git commit -m "fix(data): backfill 2026-05-11 daily observation summary"
```

---

## Task 1: Integrate `build_summary` + `--market` flag into `intraday_observation.py`

**Files:**
- Modify: `jobs/intraday_observation.py`
- Create: `tests/test_intraday_us.py`

This task replaces the hardcoded `sys.argv` parsing with `argparse`, adds `US_VALID_SLOTS`, computes `session_date_str` from market timezone, unifies the calendar guard, routes `_run_daily()` by market, and calls `build_summary` after each slot.

- [ ] **Step 1: Write the failing test**

Create `tests/test_intraday_us.py`:

```python
"""Tests for --market us flag and build_summary integration in intraday_observation."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_us_valid_slots_defined():
    """US_VALID_SLOTS contains the three expected slot names."""
    from jobs.intraday_observation import US_VALID_SLOTS
    assert "us_market_open" in US_VALID_SLOTS
    assert "us_midday" in US_VALID_SLOTS
    assert "us_post_close_review" in US_VALID_SLOTS


def test_run_daily_us_calls_daily_run_us(monkeypatch):
    """_run_daily('us') invokes jobs.daily_run_us module."""
    import subprocess as sp
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        m = MagicMock()
        m.stdout = ""
        m.stderr = ""
        m.returncode = 0
        return m

    monkeypatch.setattr(sp, "run", fake_run)
    from jobs.intraday_observation import _run_daily
    _run_daily("us")
    assert "jobs.daily_run_us" in " ".join(captured["cmd"])


def test_run_daily_tw_calls_daily_run(monkeypatch):
    """_run_daily('tw') invokes jobs.daily_run module."""
    import subprocess as sp
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        m = MagicMock()
        m.stdout = ""
        m.stderr = ""
        m.returncode = 0
        return m

    monkeypatch.setattr(sp, "run", fake_run)
    from jobs.intraday_observation import _run_daily
    _run_daily("tw")
    assert "jobs.daily_run" in " ".join(captured["cmd"])
    assert "daily_run_us" not in " ".join(captured["cmd"])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/shimeon/investment_os
python3 -m pytest tests/test_intraday_us.py -v 2>&1 | head -30
```

Expected: `FAILED` on `test_us_valid_slots_defined` and `test_run_daily_us_calls_daily_run_us` (ImportError or AttributeError — US_VALID_SLOTS not yet defined, `_run_daily` not yet market-aware).

- [ ] **Step 3: Add `US_VALID_SLOTS` near the top of `intraday_observation.py`**

Find the `VALID_SLOTS` constant (around line 29) and add `US_VALID_SLOTS` immediately after:

```python
VALID_SLOTS = (
    "pre_market",
    "market_open",
    "mid_morning",
    "noon_review",
    "pre_close",
    "post_close_review",
)

US_VALID_SLOTS = (
    "us_market_open",
    "us_midday",
    "us_post_close_review",
)
```

- [ ] **Step 4: Update `_run_daily()` to accept `market` parameter**

Replace the existing `_run_daily()` function (lines 85–104) with:

```python
def _run_daily(market: str = "tw") -> tuple[str, int]:
    module = "jobs.daily_run_us" if market == "us" else "jobs.daily_run"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    try:
        p = subprocess.run(
            [sys.executable, "-m", module],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )
        combined = p.stdout
        if p.stderr.strip():
            combined += "\n--- STDERR ---\n" + p.stderr
        return combined, p.returncode
    except subprocess.TimeoutExpired:
        return f"ERROR: {module} timed out after 300s\n", 1
    except Exception as e:
        return f"ERROR: {e}\n", 1
```

- [ ] **Step 5: Replace `main()` with the market-aware version**

Replace the entire `main()` function (from `def main() -> int:` to `return 0 if runtime_status in ("PASS", "PARTIAL") else 1`) with:

```python
def main() -> int:
    import argparse
    from zoneinfo import ZoneInfo

    parser = argparse.ArgumentParser(
        description="Investment OS Intraday Observation Runner"
    )
    parser.add_argument("slot", help="Observation slot name")
    parser.add_argument("--market", choices=["tw", "us"], default="tw",
                        help="Market session (default: tw)")
    args = parser.parse_args()
    slot = args.slot
    market = args.market

    if market == "tw" and slot not in VALID_SLOTS:
        print(f"Usage: python3 jobs/intraday_observation.py <slot> [--market tw|us]")
        print(f"Valid TW slots: {' | '.join(VALID_SLOTS)}")
        return 1
    if market == "us" and slot not in US_VALID_SLOTS:
        print(f"Usage: python3 jobs/intraday_observation.py <slot> [--market tw|us]")
        print(f"Valid US slots: {' | '.join(US_VALID_SLOTS)}")
        return 1

    print(f"[{NOW}] === Intraday observation: {slot} (market={market}) ===")

    # Compute session date in market's local timezone to handle cross-midnight US slots
    if market == "us":
        session_date = datetime.now(ZoneInfo("America/New_York")).date()
    else:
        session_date = datetime.now(ZoneInfo("Asia/Taipei")).date()
    session_date_str = session_date.isoformat()

    # Calendar guard: skip holidays (weekends already filtered by Mon..Fri timers)
    market_key = "US" if market == "us" else "TW"
    mkt_status = is_market_open(market_key, session_date)
    if mkt_status not in ("OPEN", "OPEN_EARLY_CLOSE"):
        print(f"[{NOW}] [SKIP] {market_key} market {mkt_status} — skipping ({slot})")
        return 0

    # Slot-specific output dirs — use session_date_str for correct date folder
    intraday_report_dir = ROOT / "reports" / "intraday" / session_date_str
    intraday_log_dir = ROOT / "logs" / "intraday" / session_date_str
    intraday_data_dir = ROOT / "data" / "processed" / "intraday" / session_date_str
    for d in (intraday_report_dir, intraday_log_dir, intraday_data_dir):
        d.mkdir(parents=True, exist_ok=True)

    slot_report_path = intraday_report_dir / f"{HHMM}_{slot}.md"
    slot_log_path = intraday_log_dir / f"{HHMM}_{slot}.log"
    daily_report_src = ROOT / "reports" / "daily" / f"{session_date_str}_daily_report.md"

    # 1. Load role map
    role_index = _load_role_index()
    print(f"[{NOW}] [ROLE] role_index loaded: {len(role_index)} tickers")

    # 2. Git status before
    print(f"[{NOW}] [GIT] Capturing status before run...")
    git_before = _get_git_info()
    print(f"[{NOW}] [GIT] branch={git_before['branch']} commit={git_before['latest_commit']} tree={git_before['working_tree']}")

    # 3. Run market-specific daily job
    daily_module = "jobs.daily_run_us" if market == "us" else "jobs.daily_run"
    print(f"[{NOW}] [RUN] python3 -m {daily_module}")
    output, returncode = _run_daily(market)
    print(f"[{NOW}] [RUN] returncode={returncode}")

    slot_log_path.write_text(output, encoding="utf-8")
    print(f"[{NOW}] [WRITE] {slot_log_path}")

    # 4. Read generated outputs
    signal_snap: dict = {}
    if SIGNAL_SNAPSHOT_SRC.exists():
        try:
            signal_snap = json.loads(SIGNAL_SNAPSHOT_SRC.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[{NOW}] [WARN] Could not read signal_snapshot.json: {e}")

    mainline_snap: dict = {}
    if MAINLINE_SNAPSHOT_SRC.exists():
        try:
            mainline_snap = json.loads(MAINLINE_SNAPSHOT_SRC.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[{NOW}] [WARN] Could not read mainline_snapshot.json: {e}")

    p1_snap: dict = {}
    p1_snap_src = ROOT / "data" / "processed" / "p1_audit_report.json"
    if p1_snap_src.exists():
        try:
            p1_snap = json.loads(p1_snap_src.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[{NOW}] [WARN] Could not read p1_audit_report.json: {e}")

    report_text = ""
    if daily_report_src.exists():
        try:
            report_text = daily_report_src.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[{NOW}] [WARN] Could not read daily report: {e}")

    # 5. Copy snapshots into intraday slot folder
    signal_snap_dest = None
    if SIGNAL_SNAPSHOT_SRC.exists():
        signal_snap_dest = intraday_data_dir / f"{HHMM}_signal_snapshot.json"
        shutil.copy2(SIGNAL_SNAPSHOT_SRC, signal_snap_dest)
        print(f"[{NOW}] [COPY] {signal_snap_dest}")

    mainline_snap_dest = None
    if MAINLINE_SNAPSHOT_SRC.exists():
        mainline_snap_dest = intraday_data_dir / f"{HHMM}_mainline_snapshot.json"
        shutil.copy2(MAINLINE_SNAPSHOT_SRC, mainline_snap_dest)
        print(f"[{NOW}] [COPY] {mainline_snap_dest}")

    # 6. Git status after
    git_after = _get_git_info()

    # 7. Build and write slot report
    runtime_status = _compute_runtime_status(returncode, output)

    obs_dir = ROOT / "data" / "observations" / "intraday" / session_date_str
    obs_dir.mkdir(parents=True, exist_ok=True)
    obs_path = obs_dir / f"{HHMM}_{slot}_observation.json"
    try:
        obs_data = _build_observation_json(
            slot=slot,
            git_before=git_before,
            runtime_status=runtime_status,
            signal_snap=signal_snap,
            mainline_snap=mainline_snap,
            p1_snap=p1_snap,
            role_index=role_index,
        )
        obs_path.write_text(json.dumps(obs_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{NOW}] [WRITE] {obs_path}")
    except Exception as e:
        print(f"[{NOW}] [WARN] Could not write observation JSON: {e}")

    snap_fields = _read_snapshot_fields(signal_snap)
    freshness_block = _extract_freshness_block(report_text) if report_text else "(daily report not found)"
    candidates = _read_mainline_candidates(mainline_snap, role_index)
    p1_summary = _read_p1_audit_summary(p1_snap)
    manual_flags = _extract_manual_review_flags(report_text) if report_text else ["(daily report not found)"]
    data_warnings = _extract_data_warnings(output)

    slot_report = _build_slot_report(
        slot=slot,
        git_before=git_before,
        git_after=git_after,
        runtime_status=runtime_status,
        output=output,
        snap_fields=snap_fields,
        freshness_block=freshness_block,
        candidates=candidates,
        p1_summary=p1_summary,
        manual_flags=manual_flags,
        data_warnings=data_warnings,
        slot_report_path=slot_report_path,
        slot_log_path=slot_log_path,
        signal_snap_dest=signal_snap_dest,
        mainline_snap_dest=mainline_snap_dest,
    )

    slot_report_path.write_text(slot_report, encoding="utf-8")
    print(f"[{NOW}] [WRITE] {slot_report_path}")

    print(f"[{NOW}] === Intraday observation {slot}: {runtime_status} ===")

    # 7b. Auto-update daily replay summary
    try:
        from jobs.observation_replay_builder import build_summary
        build_summary(session_date_str)
        print(f"[{NOW}] [REPLAY] daily summary updated for {session_date_str}")
    except Exception as e:
        print(f"[{NOW}] [WARN] build_summary failed: {e}")

    try:
        from reporting.web_report_generator import generate_all
        generate_all()
        print(f"[{NOW}] [WEB] HTML dashboard updated")
    except Exception as e:
        print(f"[{NOW}] [WARN] web dashboard update failed: {e}")

    return 0 if runtime_status in ("PASS", "PARTIAL") else 1
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd /home/shimeon/investment_os
python3 -m pytest tests/test_intraday_us.py -v
```

Expected: 3 PASSED.

- [ ] **Step 7: Confirm existing TW pipeline still works**

```bash
python3 -m pytest tests/test_web_report_generator.py -v 2>&1 | tail -5
```

Expected: all existing tests still PASSED.

- [ ] **Step 8: Commit**

```bash
git add jobs/intraday_observation.py tests/test_intraday_us.py
git commit -m "feat(obs): add --market flag, session_date, and auto build_summary to intraday_observation"
```

---

## Task 2: Create `daily_run_us.py` scaffold

**Files:**
- Create: `jobs/daily_run_us.py`
- Test: `tests/test_intraday_us.py` (add test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_intraday_us.py`:

```python
def test_daily_run_us_exits_zero_without_candidates(tmp_path, monkeypatch):
    """daily_run_us returns 0 when candidates_us.json does not exist."""
    import jobs.daily_run_us as dru
    monkeypatch.setattr(dru, "CANDIDATES_US", tmp_path / "candidates_us.json")
    assert dru.main() == 0


def test_daily_run_us_exits_zero_with_empty_candidates(tmp_path, monkeypatch):
    """daily_run_us returns 0 when candidates_us.json is an empty list."""
    import jobs.daily_run_us as dru
    f = tmp_path / "candidates_us.json"
    f.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(dru, "CANDIDATES_US", f)
    assert dru.main() == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m pytest tests/test_intraday_us.py::test_daily_run_us_exits_zero_without_candidates -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'jobs.daily_run_us'`

- [ ] **Step 3: Create `jobs/daily_run_us.py`**

```python
#!/usr/bin/env python3
"""
Investment OS — US Market Daily Run (scaffold)

Usage:
    python3 -m jobs.daily_run_us

Reads:  data/candidates_us.json  (must be populated before this script produces real output)
Writes: data/processed/signal_snapshot.json, data/processed/mainline_snapshot.json

No-ops gracefully when candidates_us.json is absent or empty.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CANDIDATES_US = ROOT / "data" / "candidates_us.json"


def main() -> int:
    if not CANDIDATES_US.exists():
        print("[INFO] candidates_us.json not found — skipping US run")
        return 0

    try:
        candidates = json.loads(CANDIDATES_US.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] Could not read candidates_us.json: {e}")
        return 1

    if not candidates:
        print("[INFO] candidates_us.json is empty — skipping US run")
        return 0

    print(f"[INFO] US run: {len(candidates)} candidates loaded (scaffold — implement US data logic here)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_intraday_us.py -v
```

Expected: 5 PASSED (3 from Task 1 + 2 new).

- [ ] **Step 5: Smoke test the module directly**

```bash
python3 -m jobs.daily_run_us
```

Expected output: `[INFO] candidates_us.json not found — skipping US run`

- [ ] **Step 6: Commit**

```bash
git add jobs/daily_run_us.py tests/test_intraday_us.py
git commit -m "feat(jobs): add daily_run_us.py scaffold for US market observation"
```

---

## Task 3: Update `run_intraday_observation.sh` for US slots

**Files:**
- Modify: `scripts/run_intraday_observation.sh`

- [ ] **Step 1: Read current script**

```bash
cat scripts/run_intraday_observation.sh
```

- [ ] **Step 2: Replace the `python3` call line to detect US slots**

The current script ends with:
```bash
python3 jobs/intraday_observation.py "$1"
```

Replace that final line only with:

```bash
SLOT="$1"
MARKET_FLAG=""
if [[ "$SLOT" == us_* ]]; then
    MARKET_FLAG="--market us"
fi

python3 jobs/intraday_observation.py "$SLOT" $MARKET_FLAG
```

Full updated script:

```bash
#!/usr/bin/env bash
# Manual trigger for Investment OS intraday observation runner v0.1.
# Usage: scripts/run_intraday_observation.sh <slot>
# TW slots: pre_market | market_open | mid_morning | noon_review | pre_close | post_close_review
# US slots:  us_market_open | us_midday | us_post_close_review
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

if [ -d "venv" ]; then
    source venv/bin/activate
fi

export PYTHONPATH="$PWD"

SLOT="$1"
MARKET_FLAG=""
if [[ "$SLOT" == us_* ]]; then
    MARKET_FLAG="--market us"
fi

python3 jobs/intraday_observation.py "$SLOT" $MARKET_FLAG
```

- [ ] **Step 3: Verify TW slot still works (dry-run argument parsing only)**

```bash
python3 -c "
import sys
sys.argv = ['intraday_observation.py', 'post_close_review']
from jobs.intraday_observation import VALID_SLOTS, US_VALID_SLOTS
assert 'post_close_review' in VALID_SLOTS
print('TW slot validation OK')
sys.argv = ['intraday_observation.py', 'us_market_open', '--market', 'us']
assert 'us_market_open' in US_VALID_SLOTS
print('US slot validation OK')
"
```

Expected: two `OK` lines, no exceptions.

- [ ] **Step 4: Commit**

```bash
git add scripts/run_intraday_observation.sh
git commit -m "feat(scripts): auto-detect us_ slot prefix and pass --market us flag"
```

---

## Task 4: Create US systemd timer files

**Files:**
- Create: `systemd/investment-os-intraday-us-market-open.timer`
- Create: `systemd/investment-os-intraday-us-midday.timer`
- Create: `systemd/investment-os-intraday-us-post-close.timer`

- [ ] **Step 1: Create `systemd/investment-os-intraday-us-market-open.timer`**

```ini
[Unit]
Description=Investment OS Intraday Observation Timer — us_market_open 21:30 Asia/Taipei

[Timer]
OnCalendar=Mon..Fri 21:30:00
TimeZone=Asia/Taipei
Persistent=false
Unit=investment-os-intraday-observation@us_market_open.service

[Install]
WantedBy=timers.target
```

- [ ] **Step 2: Create `systemd/investment-os-intraday-us-midday.timer`**

```ini
[Unit]
Description=Investment OS Intraday Observation Timer — us_midday 01:00 Asia/Taipei

[Timer]
OnCalendar=Tue..Sat 01:00:00
TimeZone=Asia/Taipei
Persistent=false
Unit=investment-os-intraday-observation@us_midday.service

[Install]
WantedBy=timers.target
```

- [ ] **Step 3: Create `systemd/investment-os-intraday-us-post-close.timer`**

```ini
[Unit]
Description=Investment OS Intraday Observation Timer — us_post_close_review 04:30 Asia/Taipei

[Timer]
OnCalendar=Tue..Sat 04:30:00
TimeZone=Asia/Taipei
Persistent=false
Unit=investment-os-intraday-observation@us_post_close_review.service

[Install]
WantedBy=timers.target
```

- [ ] **Step 4: Verify systemd syntax**

```bash
systemd-analyze verify \
  systemd/investment-os-intraday-us-market-open.timer \
  systemd/investment-os-intraday-us-midday.timer \
  systemd/investment-os-intraday-us-post-close.timer
```

Expected: no output (means no errors). If `systemd-analyze verify` requires unit to be installed, use:

```bash
systemd-analyze calendar "Mon..Fri 21:30:00" --timezone=Asia/Taipei
systemd-analyze calendar "Tue..Sat 01:00:00" --timezone=Asia/Taipei
systemd-analyze calendar "Tue..Sat 04:30:00" --timezone=Asia/Taipei
```

Expected: each prints the next scheduled fire time in CST.

- [ ] **Step 5: Commit**

```bash
git add systemd/investment-os-intraday-us-market-open.timer \
        systemd/investment-os-intraday-us-midday.timer \
        systemd/investment-os-intraday-us-post-close.timer
git commit -m "feat(systemd): add US market intraday observation timers (21:30/01:00/04:30 CST)"
```

---

## Task 5: Install timers and end-to-end verify

**Files:** none (systemd install + manual test)

- [ ] **Step 1: Install the three new timers**

```bash
sudo cp systemd/investment-os-intraday-us-market-open.timer /etc/systemd/system/
sudo cp systemd/investment-os-intraday-us-midday.timer /etc/systemd/system/
sudo cp systemd/investment-os-intraday-us-post-close.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now \
  investment-os-intraday-us-market-open.timer \
  investment-os-intraday-us-midday.timer \
  investment-os-intraday-us-post-close.timer
```

- [ ] **Step 2: Confirm all 9 investment timers are listed**

```bash
systemctl list-timers | grep investment
```

Expected: 6 TW timers + 3 US timers = 9 total rows.

- [ ] **Step 3: Manual smoke test — simulate a US slot**

```bash
cd /home/shimeon/investment_os
bash scripts/run_intraday_observation.sh us_market_open
```

Expected log lines (in order):
```
=== Intraday observation: us_market_open (market=us) ===
[ROLE] role_index loaded: ...
[RUN] python3 -m jobs.daily_run_us
[INFO] candidates_us.json not found — skipping US run
[RUN] returncode=0
[WRITE] data/observations/intraday/<ET-date>/...us_market_open_observation.json
[REPLAY] daily summary updated for <ET-date>
[WEB] HTML dashboard updated
=== Intraday observation us_market_open: PARTIAL ===
```

- [ ] **Step 4: Confirm replay.html shows the new US slot**

```bash
grep "us_market_open" reports/web/replay.html
```

Expected: one `<td>us_market_open</td>` row in the table.

- [ ] **Step 5: Manual smoke test — confirm TW slot unchanged**

```bash
bash scripts/run_intraday_observation.sh post_close_review 2>&1 | grep -E "market=|RUN|REPLAY|WEB"
```

Expected:
```
=== Intraday observation: post_close_review (market=tw) ===
[RUN] python3 -m jobs.daily_run
[REPLAY] daily summary updated for 2026-05-11
[WEB] HTML dashboard updated
```

- [ ] **Step 6: Run full test suite**

```bash
python3 -m pytest tests/ -v 2>&1 | tail -15
```

Expected: all tests PASSED (no regressions).

- [ ] **Step 7: Final commit**

```bash
git add -u
git commit -m "feat: integrate US market observation pipeline with auto replay builder update"
```
