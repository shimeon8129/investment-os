#!/usr/bin/env python3
"""
Investment OS MVP-Auto-Observation v0.1
Daily observation wrapper — runs jobs.daily_run, writes dated log and observation summary.

Hard constraints:
- Does NOT modify strategy/entry/exit logic.
- Does NOT enable auto-trading or broker access.
- Does NOT commit or push.
- Idempotent: re-running same day overwrites dated log and observation summary.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.market_calendar import is_market_open

TODAY = datetime.now().strftime("%Y-%m-%d")
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

LOG_DIR = ROOT / "logs"
OBS_DIR = ROOT / "reports" / "observation"
DAILY_REPORT_DIR = ROOT / "reports" / "daily"
SNAPSHOT_PATH = ROOT / "data" / "processed" / "signal_snapshot.json"

LOG_DIR.mkdir(parents=True, exist_ok=True)
OBS_DIR.mkdir(parents=True, exist_ok=True)

dated_log = LOG_DIR / f"daily_run_{TODAY}.log"
obs_report = OBS_DIR / f"{TODAY}_observation_summary.md"
daily_report = DAILY_REPORT_DIR / f"{TODAY}_daily_report.md"

SUBPROCESS_LABELS = [
    "daily_decision_dashboard",
    "smoke_daily_decision_dashboard",
    "smoke_portfolio_holdings",
    "pipeline_main_v1",
    "p1_entry_audit",
]


# ─────────────────────────────────────────────────────────────
# Git helpers
# ─────────────────────────────────────────────────────────────

def _git(args: list[str]) -> str:
    try:
        r = subprocess.run(
            ["git"] + args,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return r.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"


def _git_status() -> dict:
    branch = _git(["branch", "--show-current"])
    remote_ref = _git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])

    fetch_err = None
    try:
        subprocess.run(
            ["git", "fetch", "origin", "--quiet"],
            cwd=str(ROOT),
            capture_output=True,
            timeout=30,
        )
    except Exception as e:
        fetch_err = str(e)

    ahead_behind = _git(["rev-list", "--left-right", "--count", "HEAD...origin/main"])
    porcelain = _git(["status", "--porcelain"])

    ahead = behind = "?"
    parts = ahead_behind.split()
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        ahead, behind = parts[0], parts[1]

    if fetch_err:
        sync = f"FETCH_FAILED ({fetch_err})"
    elif behind == "0" and ahead == "0":
        sync = "UP_TO_DATE"
    elif behind not in ("0", "?"):
        sync = f"BEHIND_BY_{behind}"
    elif ahead not in ("0", "?"):
        sync = f"AHEAD_BY_{ahead}"
    else:
        sync = "UNKNOWN"

    modified_lines = [l for l in porcelain.strip().splitlines() if l.strip() and not l.startswith("??")]
    tree = "CLEAN" if not modified_lines else f"MODIFIED ({len(modified_lines)} files)"

    return {
        "branch": branch,
        "remote": remote_ref if remote_ref else "N/A",
        "sync": sync,
        "working_tree": tree,
    }


# ─────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────

def _run_daily() -> tuple[str, int]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    try:
        p = subprocess.run(
            [sys.executable, "-m", "jobs.daily_run"],
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
        return "ERROR: jobs.daily_run timed out after 300s\n", 1
    except Exception as e:
        return f"ERROR: {e}\n", 1


# ─────────────────────────────────────────────────────────────
# Parsers
# ─────────────────────────────────────────────────────────────

def _parse_subprocess_results(output: str, snapshot: dict, market_closed: bool) -> dict:
    if market_closed:
        return {label: "SKIPPED (market closed)" for label in SUBPROCESS_LABELS}

    check_map = {c["label"]: c.get("status", "UNKNOWN") for c in snapshot.get("checks", [])}
    results = {}
    for label in SUBPROCESS_LABELS:
        if label in check_map:
            results[label] = check_map[label]
        elif f"[PASS] {label}" in output:
            results[label] = "PASS"
        elif f"[FAIL] {label}" in output:
            results[label] = "FAIL"
        else:
            results[label] = "UNKNOWN"
    return results


def _market_status(snapshot: dict) -> dict:
    mc = snapshot.get("market_context", {})
    markets = mc.get("markets", {})
    tw = markets.get("TW", {})
    tw_status = tw.get("status", "UNKNOWN") if isinstance(tw, dict) else str(tw)
    market_closed = snapshot.get("market_closed", False)
    expected = "Skip pipeline (MARKET_CLOSED)" if market_closed else "Run pipeline"
    actual = snapshot.get("status", "UNKNOWN")
    return {
        "tw_status": tw_status,
        "expected": expected,
        "actual": actual,
        "market_closed": market_closed,
    }


def _compute_final_status(returncode: int, snapshot: dict, market_closed: bool) -> str:
    if returncode != 0:
        return "FAIL"
    if market_closed:
        snap_status = snapshot.get("status", "UNKNOWN")
        return "PASS" if snap_status == "MARKET_CLOSED" else "PARTIAL"
    return snapshot.get("status", "UNKNOWN")


def _regression_check(output: str) -> dict:
    import_errors = bool(re.search(r"ImportError|ModuleNotFoundError", output))
    schema_errors = bool(re.search(r"KeyError|ValidationError", output))
    exceptions = bool(re.search(r"Traceback \(most recent call last\)", output))

    missing = []
    if not SNAPSHOT_PATH.exists():
        missing.append("signal_snapshot.json")
    if not daily_report.exists():
        missing.append(f"{TODAY}_daily_report.md")

    return {
        "import_errors": "YES" if import_errors else "NONE",
        "schema_errors": "YES" if schema_errors else "NONE",
        "missing_outputs": ", ".join(missing) if missing else "NONE",
        "empty_or_abnormal": "YES" if len(output.strip()) < 50 else "NONE",
        "unexpected_exceptions": "YES" if exceptions else "NONE",
    }


def _stable_record(subprocess_results: dict, market_closed: bool, final_status: str) -> dict:
    if market_closed and final_status == "PASS":
        return {
            "stable": True,
            "type": "CLOSED-day gate PASS",
            "reason": "Market closed path executed as expected",
        }

    all_pass = all(v == "PASS" for v in subprocess_results.values())
    if not market_closed and all_pass and final_status == "PASS":
        return {
            "stable": True,
            "type": "OPEN-day PASS",
            "reason": "All subprocesses PASS, required outputs present",
        }
    if final_status == "PARTIAL":
        return {
            "stable": False,
            "type": "PARTIAL",
            "reason": "One or more subprocesses failed",
        }
    return {
        "stable": False,
        "type": "FAIL",
        "reason": "Unexpected failure — check dated log",
    }


# ─────────────────────────────────────────────────────────────
# Report builder
# ─────────────────────────────────────────────────────────────

def _build_summary(
    git: dict,
    market: dict,
    subprocess_results: dict,
    regression: dict,
    stable: dict,
    final_status: str,
) -> str:
    if stable["stable"]:
        next_action = "Continue observation"
    elif final_status == "PARTIAL":
        next_action = "Investigate regression — check dated log and daily report for details"
    else:
        next_action = "Request owner approval — unexpected failure detected"

    lines = [
        f"# Investment OS Observation Summary - {TODAY}",
        "",
        "## Final Status",
        "",
        final_status,
        "",
        "## Git Status",
        "",
        f"- Branch: {git['branch']}",
        f"- Remote: {git['remote']}",
        f"- origin/main sync: {git['sync']}",
        f"- Working tree: {git['working_tree']}",
        "",
        "## Market Gate",
        "",
        f"- TW market status: {market['tw_status']}",
        f"- Expected behavior: {market['expected']}",
        f"- Actual behavior: {market['actual']}",
        "",
        "## Runtime Subprocess Results",
        "",
        f"- daily_decision_dashboard: {subprocess_results.get('daily_decision_dashboard', 'N/A')}",
        f"- smoke_daily_decision_dashboard: {subprocess_results.get('smoke_daily_decision_dashboard', 'N/A')}",
        f"- smoke_portfolio_holdings: {subprocess_results.get('smoke_portfolio_holdings', 'N/A')}",
        f"- pipeline_main_v1: {subprocess_results.get('pipeline_main_v1', 'N/A')}",
        f"- p1_entry_audit: {subprocess_results.get('p1_entry_audit', 'N/A')}",
        "",
        "## Output Artifacts",
        "",
        f"- data/processed/signal_snapshot.json: {'EXISTS' if SNAPSHOT_PATH.exists() else 'MISSING'}",
        f"- reports/daily/{TODAY}_daily_report.md: {'EXISTS' if daily_report.exists() else 'MISSING'}",
        f"- logs/daily_run_{TODAY}.log: {'EXISTS' if dated_log.exists() else 'MISSING'}",
        "",
        "## Regression Check",
        "",
        f"- Import errors: {regression['import_errors']}",
        f"- Schema errors: {regression['schema_errors']}",
        f"- Missing outputs: {regression['missing_outputs']}",
        f"- Empty or abnormal output: {regression['empty_or_abnormal']}",
        f"- Unexpected exceptions: {regression['unexpected_exceptions']}",
        "",
        "## Stable Observation Record",
        "",
        f"- Counts as stable observation record: {'YES' if stable['stable'] else 'NO'}",
        f"- Type: {stable['type']}",
        f"- Reason: {stable['reason']}",
        "",
        "## Recommended Next Action",
        "",
        next_action,
        "",
        f"*Generated at: {NOW}*",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main() -> int:
    print(f"[{NOW}] === Investment OS Observation v0.1 start ===")

    # Calendar guard: skip holidays (weekends already filtered by Mon..Fri timer)
    from datetime import date
    tw_status = is_market_open("TW", date.today())
    if tw_status not in ("OPEN", "OPEN_EARLY_CLOSE"):
        print(f"[{NOW}] [SKIP] TW market {tw_status} — skipping observation")
        return 0

    # 1. Git checks
    print(f"[{NOW}] [GIT] Checking branch and remote sync...")
    git = _git_status()
    print(f"[{NOW}] [GIT] branch={git['branch']} sync={git['sync']} tree={git['working_tree']}")

    # 2. Run daily_run
    print(f"[{NOW}] [RUN] python3 -m jobs.daily_run")
    output, returncode = _run_daily()

    # 3. Write dated log (before building summary so EXISTS check passes)
    dated_log.write_text(output, encoding="utf-8")
    print(f"[{NOW}] [WRITE] {dated_log}")

    # 4. Read snapshot
    snapshot: dict = {}
    if SNAPSHOT_PATH.exists():
        try:
            snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[{NOW}] [WARN] Could not read snapshot: {e}")

    # 5. Parse and classify
    market = _market_status(snapshot)
    market_closed = market["market_closed"]
    final_status = _compute_final_status(returncode, snapshot, market_closed)
    subprocess_results = _parse_subprocess_results(output, snapshot, market_closed)
    regression = _regression_check(output)
    stable = _stable_record(subprocess_results, market_closed, final_status)

    # 6. Write observation summary
    summary = _build_summary(git, market, subprocess_results, regression, stable, final_status)
    obs_report.write_text(summary, encoding="utf-8")
    print(f"[{NOW}] [WRITE] {obs_report}")

    stable_str = "YES" if stable["stable"] else "NO"
    print(f"[{NOW}] === Observation complete: {final_status} | stable={stable_str} | type={stable['type']} ===")

    try:
        from reporting.web_report_generator import generate_all
        generate_all()
        print(f"[{NOW}] [WEB] HTML dashboard updated")
    except Exception as e:
        print(f"[{NOW}] [WARN] web dashboard update failed: {e}")

    return 0 if stable["stable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
