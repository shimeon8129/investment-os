#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from utils.market_calendar import get_market_context, get_latest_full_trading_day
from utils.telegram_notify import send_notification
LOG_DIR = ROOT / "logs"
REPORT_DIR = ROOT / "reports" / "daily"
PROCESSED_DIR = ROOT / "data" / "processed"
ROLE_MAP_FILE = ROOT / "data" / "portfolio" / "role_map.json"

LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

log_file = LOG_DIR / "daily_run.log"
report_file = REPORT_DIR / f"{today}_daily_report.md"
snapshot_file = PROCESSED_DIR / "signal_snapshot.json"

def log(msg: str) -> None:
    line = f"[{now}] {msg}"
    print(line)
    with log_file.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"[WARN] Failed to read {path}: {e}")
        return fallback

def _load_role_index() -> dict:
    if not ROLE_MAP_FILE.exists():
        log("[WARN] role_map.json not found — role fields will show as UNKNOWN")
        return {}
    try:
        data = json.loads(ROLE_MAP_FILE.read_text(encoding="utf-8"))
        return {e["ticker"]: e for e in data.get("entries", []) if e.get("ticker")}
    except Exception as e:
        log(f"[WARN] Failed to load role_map.json: {e} — role fields will show as UNKNOWN")
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


def _role_inline(ticker: str, role_index: dict) -> str:
    rc = _role_context(ticker, role_index)
    intent = rc["intent"] or "—"
    return f"{rc['base_role']}/{rc['active_role']} [{rc['role_confidence']}] intent={intent}"


def run_module_or_script(label: str, command: list[str]) -> dict:
    log(f"[RUN] {label}: {' '.join(command)}")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    try:
        p = subprocess.run(
            command,
            cwd=str(ROOT),
            env=env,
            text=True,
            capture_output=True,
            timeout=90,
        )
        result = {
            "label": label,
            "command": command,
            "returncode": p.returncode,
            "stdout": p.stdout[-4000:],
            "stderr": p.stderr[-4000:],
            "status": "PASS" if p.returncode == 0 else "FAIL",
        }
        log(f"[{result['status']}] {label}")
        if p.stderr:
            log(f"[STDERR] {label}: {p.stderr[-1000:]}")
        return result
    except Exception as e:
        log(f"[FAIL] {label}: {e}")
        return {
            "label": label,
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(e),
            "status": "FAIL",
        }

def main() -> int:
    log("=== Investment OS daily_run start ===")

    mctx = get_market_context()
    tw_status = mctx["markets"]["TW"]["status"]
    tw_open = mctx["markets"]["TW"]["is_open"]
    log(f"[CALENDAR] TW={tw_status}")

    latest_full_trading_day = get_latest_full_trading_day("TW").isoformat()
    report_label = "TODAY_MARKET_OPEN" if tw_open else "MARKET_CLOSED_SNAPSHOT"
    _FRESHNESS_META = {
        "run_date": today,
        "market_date": mctx["date"],
        "market_status": tw_status,
        "latest_full_trading_day": latest_full_trading_day,
        "data_as_of_date": "UNKNOWN",
        "data_mode": "OBSERVATION",
        "report_label": report_label,
        "data_freshness_warning": "Data vintage not explicitly available in current MVP pipeline.",
    }
    _FRESHNESS_LINES = [
        "## Data Freshness",
        "",
        f"- report_label: `{report_label}`",
        f"- run_date: {today}",
        f"- market_date: {mctx['date']}",
        f"- market_status (TW): {tw_status}",
        f"- latest_full_trading_day (TW): {latest_full_trading_day}",
        "- data_as_of_date: UNKNOWN",
        "- data_mode: OBSERVATION",
        "> **Warning:** Data vintage not explicitly available in current MVP pipeline.",
        "",
    ]

    if not tw_open:
        log(f"[INFO] TW market closed ({tw_status}) — skipping pipeline")
        snapshot = {
            "date": today,
            "generated_at": now,
            "status": "MARKET_CLOSED",
            "market_closed": True,
            "reason": tw_status,
            "market_context": mctx,
            "checks": [],
            "safety": {
                "broker_login": False,
                "auto_trade": False,
                "advisory_only": True,
            },
            **_FRESHNESS_META,
        }
        snapshot_file.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        report_lines = [
            f"# Investment OS Daily Report - {today}",
            "",
            f"Generated at: {now}",
            "",
        ]
        report_lines += _FRESHNESS_LINES
        report_lines += [
            "## Runtime Status",
            "",
            "- Status: MARKET_CLOSED",
            f"- Reason: {tw_status}",
            "",
            "> No market pipeline was run. TW market is closed.",
            "",
            "## Human Summary",
            "",
            "- No new trading decision is generated today.",
        ]
        for mkt, info in mctx["markets"].items():
            report_lines.append(f"- {mkt} market: {info['status']}")
        report_lines += [
            "- Market pipeline skipped under current v0.1 behavior.",
            "  (v0.2 will use latest valid trading day data instead of skipping.)",
            "- Advisory only: no trades are placed automatically.",
            "",
            "## Market Calendar",
            "",
        ]
        for mkt, info in mctx["markets"].items():
            report_lines.append(f"- {mkt}: {info['status']}")
        report_lines += [
            "",
            "## Safety",
            "",
            "- Broker login: disabled",
            "- Auto trading: disabled",
            "- Advisory only: true",
            "",
            "## Output Files",
            "",
            f"- `{snapshot_file}`",
            f"- `{report_file}`",
            f"- `{log_file}`",
            "",
        ]
        report_file.write_text("\n".join(report_lines), encoding="utf-8")
        log(f"[WRITE] {snapshot_file}")
        log(f"[WRITE] {report_file}")
        log("=== Investment OS daily_run done (market closed) ===")
        return 0

    watchlist = read_json(ROOT / "data" / "watchlist.json", fallback={})
    holdings = read_json(ROOT / "data" / "portfolio" / "current_holdings.json", fallback={})
    role_index = _load_role_index()

    checks = []

    if (ROOT / "reporting" / "daily_decision_dashboard.py").exists():
        checks.append(
            run_module_or_script(
                "daily_decision_dashboard",
                [sys.executable, "-m", "reporting.daily_decision_dashboard"],
            )
        )
    else:
        log("[WARN] reporting/daily_decision_dashboard.py not found")

    if (ROOT / "tests" / "smoke_daily_decision_dashboard.py").exists():
        checks.append(
            run_module_or_script(
                "smoke_daily_decision_dashboard",
                [sys.executable, "tests/smoke_daily_decision_dashboard.py"],
            )
        )

    if (ROOT / "tests" / "smoke_portfolio_holdings.py").exists():
        checks.append(
            run_module_or_script(
                "smoke_portfolio_holdings",
                [sys.executable, "tests/smoke_portfolio_holdings.py"],
            )
        )

    if (ROOT / "pipeline" / "main_v1.py").exists():
        checks.append(
            run_module_or_script(
                "pipeline_main_v1",
                [sys.executable, "-m", "pipeline.main_v1"],
            )
        )

    # P1 entry audit — advisory-only, non-blocking; result NOT in checks[]
    p1_audit_check = None
    if (ROOT / "audit" / "p1_entry_audit.py").exists():
        p1_audit_check = run_module_or_script(
            "p1_entry_audit",
            [sys.executable, "-m", "audit.p1_entry_audit"],
        )

    mainline_snap = read_json(PROCESSED_DIR / "mainline_snapshot.json", fallback={})
    p1_audit_snap = read_json(PROCESSED_DIR / "p1_audit_report.json", fallback={})

    snapshot = {
        "date": today,
        "generated_at": now,
        "runtime": "Investment OS v0.2 bootstrap",
        "market_context": mctx,
        "watchlist_loaded": bool(watchlist),
        "watchlist_count": len(watchlist.get("tickers", [])) if isinstance(watchlist, dict) else 0,
        "holdings_loaded": bool(holdings),
        "holdings_count": len(holdings.get("holdings", [])) if isinstance(holdings, dict) else 0,
        "checks": checks,
        "status": "PASS" if all(c.get("status") == "PASS" for c in checks) else "PARTIAL",
        "safety": {
            "broker_login": False,
            "auto_trade": False,
            "advisory_only": True,
        },
        "role_summary": {
            "loaded": bool(role_index),
            "ticker_count": len(role_index),
            "warning": None if role_index else "role_map.json not found or failed to load",
        },
        **_FRESHNESS_META,
    }

    snapshot_file.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report_lines = [
        f"# Investment OS Daily Report - {today}",
        "",
        f"Generated at: {now}",
        "",
    ]
    report_lines += _FRESHNESS_LINES
    report_lines += [
        "## Market Calendar",
        "",
    ]
    for mkt, info in mctx["markets"].items():
        report_lines.append(f"- {mkt}: {info['status']}")
    report_lines += [
        "",
        "## Runtime Status",
        "",
        f"- Status: {snapshot['status']}",
        f"- Watchlist loaded: {snapshot['watchlist_loaded']}",
        f"- Watchlist count: {snapshot['watchlist_count']}",
        f"- Holdings loaded: {snapshot['holdings_loaded']}",
        f"- Holdings count: {snapshot['holdings_count']}",
        "",
        "## Human Summary",
        "",
    ]

    if mainline_snap:
        ms = mainline_snap.get("market_state", "N/A")
        msc = mainline_snap.get("market_score", None)
        vix = mainline_snap.get("vix_value", None)
        msc_str = f"{float(msc):.4f}" if msc is not None else "N/A"
        vix_str = f"{float(vix):.2f}" if vix is not None else "N/A"
        report_lines += [
            f"- Market state: **{ms}** | Score: {msc_str} | VIX: {vix_str}",
            "",
            "**Top 3 candidates:**",
            "",
        ]
        for i, row in enumerate(mainline_snap.get("ranked", [])[:3], 1):
            score = row.get("score", 0)
            score_str = f"{float(score):.2f}" if score is not None else "N/A"
            ticker = row.get("ticker", "")
            role_str = _role_inline(ticker, role_index)
            report_lines.append(
                f"{i}. {ticker} {row.get('name', '')} "
                f"— Score: {score_str} | Signal: {row.get('signal', '')} | Role: {role_str}"
            )
        report_lines.append("")
        action_counts: dict[str, int] = {}
        for d in mainline_snap.get("decisions", {}).values():
            a = d.get("action", "UNKNOWN")
            action_counts[a] = action_counts.get(a, 0) + 1
        counts_str = " | ".join(
            f"{a}: {n}" for a, n in sorted(action_counts.items())
        ) if action_counts else "none"
        report_lines += [
            f"- Decisions: {counts_str}",
            "- Advisory only: all outputs are for human review; no trades are placed automatically.",
            "",
        ]
    else:
        report_lines += [
            "- Mainline snapshot not available. No advisory summary.",
            "",
        ]

    report_lines += [
        "## Mainline Snapshot",
        "",
    ]

    if mainline_snap:
        report_lines += [
            f"- Market state: {mainline_snap.get('market_state', 'N/A')}",
            f"- Market score: {mainline_snap.get('market_score', 'N/A')}",
            f"- VIX: {mainline_snap.get('vix_value', 'N/A')}",
            "",
            "### Top Ranked",
            "",
            "| Rank | Ticker | Name | Sector | Signal | Score | base_role | active_role | role_confidence | intent |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for i, row in enumerate(mainline_snap.get("ranked", [])[:5], 1):
            ticker = row.get("ticker", "")
            rc = _role_context(ticker, role_index)
            report_lines.append(
                f"| {i} | {ticker} | {row.get('name', '')} "
                f"| {row.get('sector', '')} | {row.get('signal', '')} | {row.get('score', '')} "
                f"| {rc['base_role']} | {rc['active_role']} | {rc['role_confidence']} | {rc['intent'] or '—'} |"
            )
        report_lines += [
            "",
            "### Decisions",
            "",
            "| Ticker | Action | Reason |",
            "| --- | --- | --- |",
        ]
        for ticker, d in mainline_snap.get("decisions", {}).items():
            report_lines.append(
                f"| {ticker} | {d.get('action', '')} | {d.get('reason', '')} |"
            )
        report_lines.append("")
    else:
        report_lines += [
            "- Mainline snapshot: missing",
            "",
        ]

    # P1 Entry Audit report section — advisory, non-blocking
    p1_ok = (
        p1_audit_check is not None
        and p1_audit_check.get("status") == "PASS"
        and bool(p1_audit_snap)
    )
    report_lines += ["## P1 Entry Audit", ""]
    if p1_ok:
        s = p1_audit_snap.get("audit_summary", {})
        p1_date = p1_audit_snap.get("generated_at", today)[:10].replace("-", "")
        report_lines += [
            f"- Total signals audited: {s.get('total_signals', 0)}",
            f"- EntryLock: PASS={s.get('entry_lock_PASS', 0)} "
            f"WARN={s.get('entry_lock_WARN', 0)} "
            f"BLOCK={s.get('entry_lock_BLOCK', 0)} "
            f"SKIP={s.get('entry_lock_SKIP', 0)}",
            f"- P1 Action: ENTRY={s.get('p1_audit_ENTRY', 0)} "
            f"ENTRY_REDUCED={s.get('p1_audit_ENTRY_REDUCED', 0)} "
            f"WAIT={s.get('p1_audit_WAIT', 0)} "
            f"SKIP={s.get('p1_audit_SKIP', 0)} "
            f"UNAVAIL={s.get('p1_audit_DATA_UNAVAILABLE', 0)}",
            f"- Divergences: {s.get('divergence_count', 0)}",
            "- Advisory only. No runtime decisions changed.",
            f"- Report: docs/P1_ENTRY_AUDIT_{p1_date}.md",
            "",
        ]
    else:
        report_lines += [
            "- P1 Entry Audit: UNAVAILABLE (subprocess failed or report not found)",
            "",
        ]

    report_lines += ["## Role-Aware Candidate Summary", ""]
    if mainline_snap and mainline_snap.get("ranked"):
        if role_index:
            report_lines += [
                "| Ticker | Name | Score | Signal | base_role | active_role | role_confidence | intent |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
            for row in mainline_snap.get("ranked", [])[:10]:
                ticker = row.get("ticker", "")
                rc = _role_context(ticker, role_index)
                score = row.get("score", "N/A")
                score_str = f"{float(score):.2f}" if isinstance(score, (int, float)) else str(score)
                report_lines.append(
                    f"| {ticker} | {row.get('name', '')} | {score_str} | {row.get('signal', '')} "
                    f"| {rc['base_role']} | {rc['active_role']} | {rc['role_confidence']} | {rc['intent'] or '—'} |"
                )
            report_lines.append("")
        else:
            report_lines += ["- role_map.json not available — role fields UNKNOWN", ""]
    else:
        report_lines += ["- No ranked candidates available.", ""]

    report_lines += [
        "## Checks",
        "",
    ]

    for c in checks:
        report_lines.append(f"### {c['label']}")
        report_lines.append("")
        report_lines.append(f"- Status: {c['status']}")
        report_lines.append(f"- Return code: {c['returncode']}")
        if c.get("stderr"):
            report_lines.append("")
            report_lines.append("```text")
            report_lines.append(c["stderr"][-1500:])
            report_lines.append("```")
        report_lines.append("")

    report_lines.extend([
        "## Safety",
        "",
        "- Broker login: disabled",
        "- Auto trading: disabled",
        "- Advisory only: true",
        "",
        "## Output Files",
        "",
        f"- `{snapshot_file}`",
        f"- `{report_file}`",
        f"- `{log_file}`",
        "",
    ])

    report_file.write_text("\n".join(report_lines), encoding="utf-8")

    log(f"[WRITE] {snapshot_file}")
    log(f"[WRITE] {report_file}")
    log("=== Investment OS daily_run done ===")

    top3_lines = []
    for entry in mainline_snap.get("ranked", [])[:3]:
        top3_lines.append(
            f"{entry.get('rank','?')}. {entry.get('ticker','')} {entry.get('name','')} "
            f"score={entry.get('score','?')} signal={entry.get('signal','?')}"
        )
    top3_text = "\n".join(top3_lines) if top3_lines else "（無候選）"
    send_notification(f"*Daily Run 完成* ({today})\n\n*Top 3:*\n{top3_text}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
