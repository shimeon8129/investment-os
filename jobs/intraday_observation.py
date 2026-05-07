#!/usr/bin/env python3
"""
Investment OS — Manual Intraday Observation Runner v0.1

Usage:
    python3 jobs/intraday_observation.py <slot>

Slots: pre_market | market_open | mid_morning | noon_review | pre_close | post_close_review

Runs jobs.daily_run, captures output, writes slot-specific report, log, and snapshots.
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

VALID_SLOTS = (
    "pre_market",
    "market_open",
    "mid_morning",
    "noon_review",
    "pre_close",
    "post_close_review",
)

TODAY = datetime.now().strftime("%Y-%m-%d")
NOW_DT = datetime.now()
NOW = NOW_DT.strftime("%Y-%m-%d %H:%M:%S")
HHMM = NOW_DT.strftime("%H%M")

DAILY_REPORT_SRC = ROOT / "reports" / "daily" / f"{TODAY}_daily_report.md"
SIGNAL_SNAPSHOT_SRC = ROOT / "data" / "processed" / "signal_snapshot.json"
MAINLINE_SNAPSHOT_SRC = ROOT / "data" / "processed" / "mainline_snapshot.json"


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


def _read_mainline_candidates(mainline: dict) -> list[str]:
    rows = mainline.get("ranked", [])[:5]
    if not rows:
        return ["(no ranked candidates in mainline snapshot)"]
    lines = []
    for i, row in enumerate(rows, 1):
        score = row.get("score", "N/A")
        score_str = f"{float(score):.2f}" if isinstance(score, (int, float)) else str(score)
        lines.append(
            f"{i}. {row.get('ticker', '')} {row.get('name', '')} "
            f"— Score: {score_str} | Signal: {row.get('signal', '')}"
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
        "- Command: `python3 -m jobs.daily_run`",
        f"- Runtime final status: **{runtime_status}**",
        "",
        "## Output Paths",
        "",
        f"- Daily report: `{DAILY_REPORT_SRC}` ({'EXISTS' if DAILY_REPORT_SRC.exists() else 'MISSING'})",
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
    if len(sys.argv) != 2 or sys.argv[1] not in VALID_SLOTS:
        print(f"Usage: python3 jobs/intraday_observation.py <slot>")
        print(f"Valid slots: {' | '.join(VALID_SLOTS)}")
        return 1

    slot = sys.argv[1]
    print(f"[{NOW}] === Intraday observation: {slot} ===")

    # Slot-specific output dirs
    intraday_report_dir = ROOT / "reports" / "intraday" / TODAY
    intraday_log_dir = ROOT / "logs" / "intraday" / TODAY
    intraday_data_dir = ROOT / "data" / "processed" / "intraday" / TODAY
    for d in (intraday_report_dir, intraday_log_dir, intraday_data_dir):
        d.mkdir(parents=True, exist_ok=True)

    slot_report_path = intraday_report_dir / f"{HHMM}_{slot}.md"
    slot_log_path = intraday_log_dir / f"{HHMM}_{slot}.log"

    # 1. Git status before
    print(f"[{NOW}] [GIT] Capturing status before run...")
    git_before = _get_git_info()
    print(f"[{NOW}] [GIT] branch={git_before['branch']} commit={git_before['latest_commit']} tree={git_before['working_tree']}")

    # 2. Run daily_run
    print(f"[{NOW}] [RUN] python3 -m jobs.daily_run")
    output, returncode = _run_daily()
    print(f"[{NOW}] [RUN] returncode={returncode}")

    # 3. Write slot log
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
    if DAILY_REPORT_SRC.exists():
        try:
            report_text = DAILY_REPORT_SRC.read_text(encoding="utf-8")
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

    # 7. Parse and build report
    runtime_status = _compute_runtime_status(returncode, output)
    snap_fields = _read_snapshot_fields(signal_snap)
    freshness_block = _extract_freshness_block(report_text) if report_text else "(daily report not found)"
    candidates = _read_mainline_candidates(mainline_snap)
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
    return 0 if runtime_status in ("PASS", "PARTIAL") else 1


if __name__ == "__main__":
    raise SystemExit(main())
