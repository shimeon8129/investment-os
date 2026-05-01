#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
REPORT_DIR = ROOT / "reports" / "daily"
PROCESSED_DIR = ROOT / "data" / "processed"

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

    if datetime.now().weekday() >= 5:
        log("[INFO] Weekend detected — market closed, skipping pipeline")
        snapshot = {
            "date": today,
            "generated_at": now,
            "status": "MARKET_CLOSED",
            "market_closed": True,
            "reason": "weekend",
            "checks": [],
            "safety": {
                "broker_login": False,
                "auto_trade": False,
                "advisory_only": True,
            },
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
            "## Runtime Status",
            "",
            "- Status: MARKET_CLOSED",
            "- Market closed: true",
            "- Reason: weekend",
            "",
            "> No market pipeline was run. Markets are closed on weekends.",
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

    mainline_snap = read_json(PROCESSED_DIR / "mainline_snapshot.json", fallback={})

    snapshot = {
        "date": today,
        "generated_at": now,
        "runtime": "Investment OS v0.2 bootstrap",
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
        "## Runtime Status",
        "",
        f"- Status: {snapshot['status']}",
        f"- Watchlist loaded: {snapshot['watchlist_loaded']}",
        f"- Watchlist count: {snapshot['watchlist_count']}",
        f"- Holdings loaded: {snapshot['holdings_loaded']}",
        f"- Holdings count: {snapshot['holdings_count']}",
        "",
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
            "| Rank | Ticker | Name | Sector | Signal | Score |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for i, row in enumerate(mainline_snap.get("ranked", [])[:5], 1):
            report_lines.append(
                f"| {i} | {row.get('ticker', '')} | {row.get('name', '')} "
                f"| {row.get('sector', '')} | {row.get('signal', '')} | {row.get('score', '')} |"
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

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
