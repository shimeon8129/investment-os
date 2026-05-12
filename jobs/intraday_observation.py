#!/usr/bin/env python3
"""
Investment OS — Manual Intraday Observation Runner v0.2

Usage:
    python3 jobs/intraday_observation.py <slot> [--market tw|us]

TW Slots: pre_market | market_open | mid_morning | noon_review | pre_close | post_close_review
US Slots: us_market_open | us_midday | us_post_close_review

Runs jobs.daily_run (TW) or jobs.daily_run_us (US), captures output, writes slot-specific
report, log, and snapshots. Computes session_date in market-local timezone for correct
cross-midnight handling. Auto-updates the daily replay summary via build_summary().
Does NOT modify trading logic, signal logic, or existing 16:00 observation automation.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.market_calendar import is_market_open
from utils.telegram_notify import send_notification

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

TODAY = datetime.now().strftime("%Y-%m-%d")
NOW_DT = datetime.now()
NOW = NOW_DT.strftime("%Y-%m-%d %H:%M:%S")
HHMM = NOW_DT.strftime("%H%M")

DAILY_REPORT_SRC = ROOT / "reports" / "daily" / f"{TODAY}_daily_report.md"
SIGNAL_SNAPSHOT_SRC = ROOT / "data" / "processed" / "signal_snapshot.json"
MAINLINE_SNAPSHOT_SRC = ROOT / "data" / "processed" / "mainline_snapshot.json"
ROLE_MAP_FILE = ROOT / "data" / "portfolio" / "role_map.json"


# ─────────────────────────────────────────────────────────────────────────────
# Git helpers
# ─────────────────────────────────────────────────────────────────────────────

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


def _get_git_info() -> dict:
    branch = _git(["branch", "--show-current"])
    commit = _git(["rev-parse", "--short", "HEAD"])
    porcelain = _git(["status", "--porcelain"])
    modified = [l for l in porcelain.strip().splitlines() if l.strip() and not l.startswith("??")]
    tree = "CLEAN" if not modified else f"MODIFIED ({len(modified)} files)"
    return {
        "branch": branch,
        "latest_commit": commit,
        "working_tree": tree,
        "porcelain": porcelain.strip() or "(clean)",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# Parsers
# ─────────────────────────────────────────────────────────────────────────────

def _compute_runtime_status(returncode: int, output: str) -> str:
    if returncode != 0:
        return "FAIL"
    if re.search(r"Traceback \(most recent call last\)", output):
        return "PARTIAL"
    if re.search(r"\[FAIL\]", output):
        return "PARTIAL"
    return "PASS"


def _extract_freshness_block(report_text: str) -> str:
    lines = report_text.splitlines()
    in_block = False
    block: list[str] = []
    for line in lines:
        if line.strip() == "## Data Freshness":
            in_block = True
            block.append(line)
            continue
        if in_block:
            if line.startswith("## ") and line.strip() != "## Data Freshness":
                break
            block.append(line)
    if block:
        return "\n".join(block).strip()
    return "(Data Freshness block not found in daily report)"


def _read_snapshot_fields(snapshot: dict) -> dict:
    mc = snapshot.get("market_context", {})
    markets = mc.get("markets", {})
    tw = markets.get("TW", {})
    tw_status = tw.get("status", "N/A") if isinstance(tw, dict) else str(tw)
    return {
        "market_status": tw_status,
        "market_state": snapshot.get("market_state", "N/A"),
        "market_score": snapshot.get("market_score", "N/A"),
        "vix": snapshot.get("vix_value", "N/A"),
        "report_label": snapshot.get("report_label", "N/A"),
        "data_as_of_date": snapshot.get("data_as_of_date", "N/A"),
        "latest_full_trading_day": snapshot.get("latest_full_trading_day", "N/A"),
    }


def _read_mainline_candidates(mainline: dict, role_index: dict) -> list[str]:
    rows = mainline.get("ranked", [])[:5]
    if not rows:
        return ["(no ranked candidates in mainline snapshot)"]
    lines = []
    for i, row in enumerate(rows, 1):
        ticker = row.get("ticker", "")
        score = row.get("score", "N/A")
        score_str = f"{float(score):.2f}" if isinstance(score, (int, float)) else str(score)
        rc = _role_context(ticker, role_index)
        intent = rc["intent"] or "—"
        role_str = f"{rc['base_role']}/{rc['active_role']} [{rc['role_confidence']}] intent={intent}"
        lines.append(
            f"{i}. {ticker} {row.get('name', '')} "
            f"— Score: {score_str} | Signal: {row.get('signal', '')} | Role: {role_str}"
        )
    return lines


def _read_p1_audit_summary(snapshot: dict) -> str:
    s = snapshot.get("audit_summary", {})
    if not s:
        return "(P1 audit summary not available)"
    return (
        f"total={s.get('total_signals', 0)} "
        f"EntryLock(PASS={s.get('entry_lock_PASS', 0)} "
        f"WARN={s.get('entry_lock_WARN', 0)} "
        f"BLOCK={s.get('entry_lock_BLOCK', 0)}) "
        f"Action(ENTRY={s.get('p1_audit_ENTRY', 0)} "
        f"WAIT={s.get('p1_audit_WAIT', 0)} "
        f"SKIP={s.get('p1_audit_SKIP', 0)}) "
        f"Divergences={s.get('divergence_count', 0)}"
    )


def _extract_manual_review_flags(report_text: str) -> list[str]:
    flags = re.findall(r"EXIT_ALL.*", report_text)
    flags += re.findall(r"manual.*review.*flag.*", report_text, re.IGNORECASE)
    flags += re.findall(r"⚠[^\n]*", report_text)
    return list(dict.fromkeys(flags)) or ["(none detected)"]


def _extract_data_warnings(output: str) -> list[str]:
    warnings = re.findall(r"\[WARN\][^\n]+", output)
    warnings += re.findall(r"data_warning[^\n]+", output, re.IGNORECASE)
    return list(dict.fromkeys(warnings)) or ["(none detected)"]


def _load_role_index() -> dict:
    if not ROLE_MAP_FILE.exists():
        print(f"[{NOW}] [WARN] role_map.json not found — role fields will show as UNKNOWN")
        return {}
    try:
        data = json.loads(ROLE_MAP_FILE.read_text(encoding="utf-8"))
        return {e["ticker"]: e for e in data.get("entries", []) if e.get("ticker")}
    except Exception as e:
        print(f"[{NOW}] [WARN] Failed to load role_map.json: {e} — role fields will show as UNKNOWN")
        return {}


def _role_context(ticker: str, role_index: dict) -> dict:
    e = role_index.get(ticker, {})
    return {
        "base_role": e.get("base_role", "UNKNOWN"),
        "active_role": e.get("active_role", "UNKNOWN"),
        "role_confidence": e.get("role_confidence", "UNKNOWN"),
        "intent": e.get("intent"),
        "upgrade_path": e.get("upgrade_path"),
        "role_reason": e.get("role_reason", []),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Observation JSON builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_p1_index(p1_snap: dict) -> dict:
    """Return dict keyed by ticker for O(1) lookup of P1 audit fields."""
    index: dict = {}
    for entry in p1_snap.get("audit_entries", []):
        ticker = entry.get("ticker")
        if not ticker:
            continue
        el = entry.get("entry_lock", {})
        locks = el.get("locks", {})
        blocked_by = el.get("blocked_by", [])
        block_reason = None
        if blocked_by:
            block_key = blocked_by[0]
            block_reason = locks.get(block_key, {}).get("reason")
        l0 = locks.get("L0_market", {})
        index[ticker] = {
            "p1_result": entry.get("p1_audit_action"),
            "L0": l0.get("status"),
            "L1": locks.get("L1_selection", {}).get("status"),
            "L2": locks.get("L2_setup", {}).get("status"),
            "L3": locks.get("L3_validation", {}).get("status"),
            "L4": locks.get("L4_risk", {}).get("status"),
            "block_reason": block_reason,
            "warn_reason": l0.get("reason") if l0.get("status") == "WARN" else None,
        }
    return index


def _build_observation_json(
    slot: str,
    git_before: dict,
    runtime_status: str,
    signal_snap: dict,
    mainline_snap: dict,
    p1_snap: dict,
    role_index: dict,
    session_date_str: str,
) -> dict:
    """Build normalized observation dict for a single slot run."""
    mc = signal_snap.get("market_context", {})
    markets = mc.get("markets", {})
    tw = markets.get("TW", {})
    tw_status = tw.get("status") if isinstance(tw, dict) else str(tw)

    market = {
        "market_status": tw_status,
        "market_state": signal_snap.get("market_state"),
        "market_score": signal_snap.get("market_score"),
        "vix": signal_snap.get("vix_value"),
        "report_label": signal_snap.get("report_label"),
        "data_as_of_date": signal_snap.get("data_as_of_date"),
        "latest_full_trading_day": signal_snap.get("latest_full_trading_day"),
    }
    market = {k: ("N/A" if v is None else v) for k, v in market.items()}

    p1_index = _build_p1_index(p1_snap)
    ranked = mainline_snap.get("ranked", [])

    candidates = []
    for rank, row in enumerate(ranked, 1):
        ticker = row.get("ticker", "")
        p1 = p1_index.get(ticker, {})
        candidates.append({
            "ticker": ticker,
            "name": row.get("name"),
            "rank": rank,
            "score": row.get("score"),
            "signal": row.get("signal"),
            "p1_result": p1.get("p1_result"),
            "L0": p1.get("L0"),
            "L1": p1.get("L1"),
            "L2": p1.get("L2"),
            "L3": p1.get("L3"),
            "L4": p1.get("L4"),
            "block_reason": p1.get("block_reason"),
            "warn_reason": p1.get("warn_reason"),
            "already_in_position": None,
            "manual_review_flag": None,
            "role_context": _role_context(ticker, role_index),
        })

    return {
        "date": session_date_str,
        "slot": slot,
        "run_time": NOW,
        "git_commit": git_before.get("latest_commit"),
        "runtime_status": runtime_status,
        "market": market,
        "candidates": candidates,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Report builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_slot_report(
    slot: str,
    git_before: dict,
    git_after: dict,
    runtime_status: str,
    output: str,
    snap_fields: dict,
    freshness_block: str,
    candidates: list[str],
    p1_summary: str,
    manual_flags: list[str],
    data_warnings: list[str],
    slot_report_path: Path,
    slot_log_path: Path,
    signal_snap_dest: Path | None,
    mainline_snap_dest: Path | None,
    daily_module: str,
    daily_report_src: Path,
) -> str:
    lines = [
        f"# Investment OS Intraday Observation — {slot}",
        "",
        f"**Slot:** {slot}",
        f"**Run timestamp:** {NOW}",
        f"**Git branch:** {git_before['branch']}",
        f"**Latest commit:** {git_before['latest_commit']}",
        "",
        "## Git Status Before Run",
        "",
        f"- Branch: {git_before['branch']}",
        f"- Latest commit: {git_before['latest_commit']}",
        f"- Working tree: {git_before['working_tree']}",
        "",
        "```",
        git_before["porcelain"],
        "```",
        "",
        "## Runtime",
        "",
        f"- Command: `python3 -m {daily_module}`",
        f"- Runtime final status: **{runtime_status}**",
        "",
        "## Output Paths",
        "",
        f"- Daily report: `{daily_report_src}` ({'EXISTS' if daily_report_src.exists() else 'MISSING'})",
        f"- Signal snapshot: `{SIGNAL_SNAPSHOT_SRC}` ({'EXISTS' if SIGNAL_SNAPSHOT_SRC.exists() else 'MISSING'})",
        f"- Mainline snapshot: `{MAINLINE_SNAPSHOT_SRC}` ({'EXISTS' if MAINLINE_SNAPSHOT_SRC.exists() else 'MISSING'})",
        f"- Slot report: `{slot_report_path}`",
        f"- Slot log: `{slot_log_path}`",
    ]

    if signal_snap_dest:
        lines.append(f"- Intraday signal snapshot: `{signal_snap_dest}`")
    if mainline_snap_dest:
        lines.append(f"- Intraday mainline snapshot: `{mainline_snap_dest}`")

    lines += [
        "",
        freshness_block,
        "",
        "## Market Status",
        "",
        f"- TW market status: {snap_fields['market_status']}",
        f"- report_label: {snap_fields['report_label']}",
        f"- data_as_of_date: {snap_fields['data_as_of_date']}",
        f"- latest_full_trading_day: {snap_fields['latest_full_trading_day']}",
        "",
        "## Market State / Score / VIX",
        "",
        f"- market_state: {snap_fields['market_state']}",
        f"- market_score: {snap_fields['market_score']}",
        f"- VIX: {snap_fields['vix']}",
        "",
        "## Top Ranked Candidates",
        "",
    ]
    lines.extend(candidates)

    lines += [
        "",
        "## P1 Entry Audit Summary",
        "",
        p1_summary,
        "",
        "## Manual Review Flags",
        "",
    ]
    lines.extend(f"- {f}" for f in manual_flags)

    lines += [
        "",
        "## Data Warnings / Regression Notes",
        "",
    ]
    lines.extend(f"- {w}" for w in data_warnings)

    lines += [
        "",
        "## Git Status After Run",
        "",
        f"- Working tree: {git_after['working_tree']}",
        "",
        "```",
        git_after["porcelain"],
        "```",
        "",
        "## Notes",
        "",
        "> Generated files (reports, logs, snapshots) are runtime outputs only.",
        "> They are NOT committed to git.",
        "",
        f"*Generated at: {NOW}*",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

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
            session_date_str=session_date_str,
        )
        obs_path.write_text(json.dumps(obs_data, ensure_ascii=False, indent=2), encoding="utf-8")
        slot_cands = obs_data.get("candidates", [])[:3]
        cand_lines = [
            f"  {c.get('rank','?')}. {c.get('ticker','')} {c.get('name','')} signal={c.get('signal','?')}"
            for c in slot_cands
        ]
        cand_text = "\n".join(cand_lines) if cand_lines else "（無候選）"
        send_notification(f"*盤中觀察完成* ({slot})\n\n*Top 3:*\n{cand_text}")
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
        daily_module=daily_module,
        daily_report_src=daily_report_src,
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


if __name__ == "__main__":
    raise SystemExit(main())
