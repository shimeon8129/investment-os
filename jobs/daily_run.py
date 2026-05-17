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
CANDIDATES_FILE = ROOT / "data" / "candidates.json"
UNIVERSE_FILE = ROOT / "data" / "universe_tw.csv"

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

def _load_universe_map() -> dict:
    if not UNIVERSE_FILE.exists():
        return {}
    import csv
    result = {}
    try:
        with UNIVERSE_FILE.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("ticker"):
                    result[row["ticker"]] = {"name": row.get("name", ""), "sector": row.get("sector", "")}
    except Exception:
        pass
    return result


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
        "## 市場環境",
        "",
    ]

    if mainline_snap:
        ms  = mainline_snap.get("market_state", "N/A")
        msc = mainline_snap.get("market_score", None)
        vix = mainline_snap.get("vix_value", None)
        vix_alert   = mainline_snap.get("vix_alert", "UNKNOWN")
        guidance    = mainline_snap.get("market_guidance", {})
        msc_str = f"{float(msc):.4f}" if msc is not None else "N/A"
        vix_str = f"{float(vix):.2f}"  if vix is not None else "N/A"

        report_lines += [
            f"- 市場狀態: **{ms}** | 分數: {msc_str} | VIX: {vix_str} | VIX Alert: **{vix_alert}**",
            "",
            f"> {guidance.get('summary', '—')}",
            "",
            f"**持倉操作方向：** {guidance.get('holding_action', '—')}",
            "",
            f"**新進場許可：** {'✅ 允許' if guidance.get('new_entry_ok') else '🚫 暫緩'}"
            + (f"（限 {', '.join(guidance.get('role_filter', []))}）" if guidance.get('role_filter') else ""),
            "",
        ]

        # 現有持倉建議
        report_lines += ["## 現有持倉建議", ""]
        h_guidance = mainline_snap.get("holdings_guidance", [])
        if h_guidance:
            report_lines += [
                "| Ticker | Name | Role | 建議 | 說明 |",
                "| --- | --- | --- | --- | --- |",
            ]
            for h in h_guidance:
                report_lines.append(
                    f"| {h['ticker']} | {h['name']} | {h['role']} "
                    f"| **{h['recommendation']}** | {h['note']} |"
                )
        else:
            report_lines.append("- 目前無持倉記錄。")
        report_lines.append("")

        # WAVE_SWING 進場候選（1-2週）
        report_lines += ["## 進場候選 — WAVE_SWING（1-2 週）", ""]
        ws = mainline_snap.get("wave_swing_candidates", [])
        ws_buy = [r for r in ws if r.get("action_mode") in ("TECH_BUY", "TECH_ATTACK", "TECH_BUY_CAUTION")]
        if not guidance.get("new_entry_ok"):
            report_lines += [f"> 市場狀態 {ms} / VIX {vix_alert}，暫緩新進場。以下僅供觀察。", ""]
        if ws_buy:
            report_lines += [
                "| # | Ticker | Name | Action | Chase | Chips | Vol | 建議 |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
            for i, r in enumerate(ws_buy[:8], 1):
                vol_str = f"{r.get('vol_ratio', 0):.2f}x"
                report_lines.append(
                    f"| {i} | {r['ticker']} | {r.get('name','')} "
                    f"| {r.get('action_mode','')} "
                    f"| {r.get('chase_risk','')} "
                    f"| {r.get('chip_status','')} "
                    f"| {vol_str} "
                    f"| {r.get('suggested_action','')} |"
                )
        else:
            report_lines.append("- 目前無 WAVE_SWING BUY 信號。")
        report_lines.append("")

        # SATELLITE 觀察清單（2-8週）
        report_lines += ["## 觀察清單 — SATELLITE（2-8 週）", ""]
        sat = mainline_snap.get("satellite_watch", [])
        if sat:
            report_lines += [
                "| Ticker | Name | Action | Chase | Chips | 說明 |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
            for r in sat[:5]:
                report_lines.append(
                    f"| {r['ticker']} | {r.get('name','')} "
                    f"| {r.get('action_mode','')} "
                    f"| {r.get('chase_risk','')} "
                    f"| {r.get('chip_status','')} "
                    f"| {r.get('suggested_action','')} |"
                )
        else:
            report_lines.append("- SATELLITE 候選不在本次 top-10 內。")
        report_lines.append("")

        # CORE 觀察（不主動進場）
        core_w = mainline_snap.get("core_watch", [])
        if core_w:
            report_lines += ["## CORE 持倉狀態（長期，不主動進出）", ""]
            report_lines += [
                "| Ticker | Name | Action | Chase | 說明 |",
                "| --- | --- | --- | --- | --- |",
            ]
            for r in core_w:
                report_lines.append(
                    f"| {r['ticker']} | {r.get('name','')} "
                    f"| {r.get('action_mode','')} "
                    f"| {r.get('chase_risk','')} "
                    f"| {r.get('suggested_action','')} |"
                )
            report_lines.append("")

    else:
        report_lines += ["- Mainline snapshot: missing", ""]

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

    # Phase 1B: EARLY Watchlist — score=1 candidates not yet confirmed by volume/price
    report_lines += ["## EARLY Watchlist", ""]
    early_data = read_json(CANDIDATES_FILE, fallback=[])
    early_candidates = [c for c in early_data if c.get("score") == 1]
    if early_candidates:
        universe_map = _load_universe_map()
        report_lines += [
            "| Ticker | Name | Sector | Price |",
            "| --- | --- | --- | --- |",
        ]
        for c in early_candidates:
            ticker = c.get("ticker", "")
            info = universe_map.get(ticker, {})
            name = info.get("name") or ""
            sector = info.get("sector") or ""
            price = c.get("price", "")
            price_str = f"{price:.1f}" if isinstance(price, float) else str(price)
            report_lines.append(f"| {ticker} | {name} | {sector} | {price_str} |")
        report_lines += [
            "",
            f"> {len(early_candidates)} EARLY candidates (score=1). Conditions partially met — monitor for confirmation.",
            "",
        ]
    else:
        report_lines += ["- No EARLY candidates in current scan.", ""]

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

    ranked = mainline_snap.get("ranked", [])
    decisions = mainline_snap.get("decisions", {})
    exit_signals = mainline_snap.get("exit_signals", {})
    name_map_snap = {r.get("ticker", ""): r.get("name", "") for r in ranked}
    ranked_tickers = {r.get("ticker", "") for r in ranked}

    holding_list = holdings.get("holdings", []) if isinstance(holdings, dict) else []
    holding_tickers = {h["ticker"] if "." in h.get("ticker","") else h["ticker"]+".TW"
                       for h in holding_list}

    # Top 3 候選
    top3_lines = []
    for i, entry in enumerate(ranked[:3], 1):
        ticker = entry.get("ticker", "")
        score = entry.get("score", 0)
        vol_r = entry.get("vol_ratio", 0)
        vol_tag = f" 🔥量{vol_r:.1f}x" if vol_r >= 1.5 else ""
        top3_lines.append(f"{i}. {ticker} {entry.get('name','')} {score:.1f}{vol_tag}")
    top3_text = "\n".join(top3_lines) if top3_lines else "（無候選）"

    # 決策
    decision_lines = []
    for ticker, d in decisions.items():
        name = name_map_snap.get(ticker, "")
        action = d.get("action", "")
        reason = d.get("reason", "")
        size = d.get("position_size", 0)
        decision_lines.append(f"• {ticker} {name} → {action}（{reason}，{size*100:.0f}%）")
    decision_text = "\n".join(decision_lines) if decision_lines else "（無決策）"

    # 持倉掉出候選名單警示
    dropped_lines = []
    for h in holding_list:
        raw = h.get("ticker", "")
        tw = raw if "." in raw else raw + ".TW"
        if tw not in ranked_tickers:
            dropped_lines.append(f"⚠️ {raw} {h.get('name','')} 已掉出候選名單")
    dropped_text = "\n".join(dropped_lines) if dropped_lines else "✅ 所有持倉仍在候選名單內"

    # 停損觸發
    exit_text = ""
    if exit_signals:
        exit_lines = [f"🔴 {t} {name_map_snap.get(t,'')} → {d.get('action','')}" for t, d in exit_signals.items()]
        exit_text = "\n\n*停損觸發：*\n" + "\n".join(exit_lines)

    ms = mainline_snap.get("market_state", "N/A")
    vix = mainline_snap.get("vix_value", 0)
    msg = (
        f"*Daily Run 完成* ({today})\n"
        f"市場：{ms} | VIX: {vix:.2f}\n\n"
        f"*Top 3:*\n{top3_text}\n\n"
        f"*決策:*\n{decision_text}\n\n"
        f"*持倉監控:*\n{dropped_text}"
        f"{exit_text}"
    )
    send_notification(msg)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
