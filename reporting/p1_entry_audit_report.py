# =============================================================
# reporting/p1_entry_audit_report.py
# =============================================================
# Architecture v1.6 P1: Markdown report generator.
#
# Reads the audit_result dict produced by audit.p1_entry_audit
# and writes a human-readable Markdown report to docs/.
#
# Does NOT modify any runtime files.
# Does NOT execute trades.
# =============================================================

from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCS_DIR = PROJECT_ROOT / "docs"


def _safe(value, default="-"):
    if value is None:
        return default
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _lock_badge(status):
    return {"PASS": "✅", "WARN": "⚠️", "BLOCK": "🚫", "SKIP": "⏭️"}.get(status, "❓")


def _action_badge(action):
    return {
        "ENTRY": "✅ ENTRY",
        "ENTRY_REDUCED": "⚠️ ENTRY_REDUCED",
        "WAIT": "🚫 WAIT",
        "SKIP": "⏭️ SKIP",
        "DATA_UNAVAILABLE": "❌ DATA_UNAVAILABLE",
        "SETUP_REJECTED": "❌ SETUP_REJECTED",
        "SIZING_INFEASIBLE": "❌ SIZING_INFEASIBLE",
    }.get(action, action)


def _section_header(result):
    market = result.get("market_state", "-")
    vix = result.get("vix_value")
    vix_str = f"{vix:.2f}" if vix is not None else "-"
    snap_at = result.get("snapshot_generated_at", "-")
    gen_at = result.get("generated_at", datetime.now().isoformat())
    capital = result.get("capital", 100_000)
    date_str = gen_at[:10] if gen_at else datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# P1 Entry Audit — {date_str}",
        "",
        "## Source",
        "",
        f"- Snapshot: `{result.get('snapshot_path', '-')}`",
        f"- Snapshot generated at: `{snap_at}`",
        f"- Audit generated at: `{gen_at}`",
        f"- Capital: `{capital:,}`",
        "",
        "## Market Context",
        "",
        f"| Market State | VIX |",
        f"| --- | --- |",
        f"| **{market}** | {vix_str} |",
        "",
        "## Purpose",
        "",
        "This audit report is **advisory only**.",
        "It does not execute trades and does not change any runtime decisions.",
        "`execution/risk.py` remains the active runtime risk gate.",
        "`pipeline/main_v1.py` decisions are unchanged.",
    ]
    return "\n".join(lines)


def _section_summary(result):
    s = result.get("audit_summary", {})
    ds = s.get("data_source", "-")

    lines = [
        "## Audit Summary",
        "",
        f"| Metric | Value |",
        f"| --- | --- |",
        f"| Data source | `{ds}` |",
        f"| Total signals | {s.get('total_signals', 0)} |",
        f"| EntryLock PASS | {s.get('entry_lock_PASS', 0)} |",
        f"| EntryLock WARN | {s.get('entry_lock_WARN', 0)} |",
        f"| EntryLock BLOCK | {s.get('entry_lock_BLOCK', 0)} |",
        f"| EntryLock SKIP | {s.get('entry_lock_SKIP', 0)} |",
        f"| TradeSetup VALID | {s.get('setup_VALID', 0)} |",
        f"| TradeSetup INVALID | {s.get('setup_INVALID', 0)} |",
        f"| TradeSetup INSUFFICIENT | {s.get('setup_INSUFFICIENT_DATA', 0)} |",
        f"| Sizing feasible | {s.get('sizing_feasible', 0)} |",
        f"| P1 ENTRY | {s.get('p1_audit_ENTRY', 0)} |",
        f"| P1 ENTRY_REDUCED | {s.get('p1_audit_ENTRY_REDUCED', 0)} |",
        f"| P1 WAIT | {s.get('p1_audit_WAIT', 0)} |",
        f"| P1 SKIP | {s.get('p1_audit_SKIP', 0)} |",
        f"| P1 DATA_UNAVAILABLE | {s.get('p1_audit_DATA_UNAVAILABLE', 0)} |",
        f"| Divergences | **{s.get('divergence_count', 0)}** |",
    ]
    return "\n".join(lines)


def _section_entry_lock(entries):
    headers = ["#", "ticker", "name", "signal", "level", "L0", "L1", "L2", "L3", "L4", "status", "p1_action"]
    lines = [
        "## Entry Lock Results (L0–L4)",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for idx, e in enumerate(entries, 1):
        lock = e.get("entry_lock", {})
        locks = lock.get("locks", {})
        status = lock.get("entry_lock_status", "-")
        row = [
            str(idx),
            _safe(e.get("ticker")),
            _safe(e.get("name")),
            _safe(e.get("signal")),
            _safe(e.get("level")),
            _lock_badge(locks.get("L0_market", {}).get("status", "-")),
            _lock_badge(locks.get("L1_selection", {}).get("status", "-")),
            _lock_badge(locks.get("L2_setup", {}).get("status", "-")),
            _lock_badge(locks.get("L3_validation", {}).get("status", "-")),
            _lock_badge(locks.get("L4_risk", {}).get("status", "-")),
            f"**{status}**",
            _action_badge(e.get("p1_audit_action", "-")),
        ]
        lines.append("| " + " | ".join(r.replace("|", "/") for r in row) + " |")

    return "\n".join(lines)


def _section_trade_setup(entries):
    headers = ["ticker", "setup_type", "entry_zone", "stop", "T1", "T2", "R/R", "status"]
    lines = [
        "## Trade Setup Results",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for e in entries:
        ts = e.get("trade_setup", {})
        row = [
            _safe(e.get("ticker")),
            _safe(ts.get("setup_type")),
            _safe(ts.get("entry_zone")),
            _safe(ts.get("stop_loss_price")),
            _safe(ts.get("target_1")),
            _safe(ts.get("target_2")),
            _safe(ts.get("risk_reward")),
            _safe(ts.get("setup_status")),
        ]
        lines.append("| " + " | ".join(r.replace("|", "/") for r in row) + " |")

    return "\n".join(lines)


def _section_position_sizing(entries):
    headers = ["ticker", "shares", "value", "pct%", "max_loss", "risk/share", "feasible"]
    lines = [
        "## Position Sizing Results",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for e in entries:
        ps = e.get("position_sizing", {})
        pct = ps.get("position_pct")
        pct_str = f"{pct*100:.2f}%" if pct is not None else "-"
        row = [
            _safe(e.get("ticker")),
            _safe(ps.get("shares")),
            _safe(ps.get("position_value")),
            pct_str,
            _safe(ps.get("max_loss_value")),
            _safe(ps.get("risk_per_share")),
            "✅" if ps.get("feasible") else "❌",
        ]
        lines.append("| " + " | ".join(r.replace("|", "/") for r in row) + " |")

    return "\n".join(lines)


def _section_divergences(entries):
    flagged = [e for e in entries if e.get("divergence_flags")]

    lines = ["## Pipeline Divergences", ""]

    if not flagged:
        lines.append("No divergences detected.")
        return "\n".join(lines)

    headers = ["ticker", "name", "p1_action", "pipeline_action", "flags"]
    lines += [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for e in flagged:
        pd_ = e.get("pipeline_decision") or {}
        row = [
            _safe(e.get("ticker")),
            _safe(e.get("name")),
            _safe(e.get("p1_audit_action")),
            _safe(pd_.get("action")),
            ", ".join(e.get("divergence_flags", [])),
        ]
        lines.append("| " + " | ".join(r.replace("|", "/") for r in row) + " |")

    return "\n".join(lines)


def _section_risk_notes():
    return "\n".join([
        "## Risk Notes",
        "",
        "- This report is advisory only. No automatic trade is executed.",
        "- `execution/risk.py` is the active runtime risk gate and is NOT changed by this audit.",
        "- `pipeline/main_v1.py` decisions are NOT changed.",
        "- Divergence flags are informational. Manual review required before any action.",
        "- `decision/risk_lock.py` is excluded from this audit (not yet reviewed for P1).",
        "",
        "## Manual Action Checklist",
        "",
        "- [ ] Review all WAIT / BLOCK entries before considering entry",
        "- [ ] Review all ENTRY_REDUCED entries — consider reduced position size",
        "- [ ] Investigate P0_BLOCK_vs_PIPELINE_BUY divergences",
        "- [ ] Confirm no ticker-name mismatch in report",
        "- [ ] Confirm this report does not trigger any direct execution",
        "- [ ] Write manual decision notes before any trade",
    ])


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def generate_p1_audit_markdown(audit_result, report_path=None):
    """
    Generate a human-readable Markdown report from a P1 audit result dict.

    Parameters
    ----------
    audit_result : dict
        Output of audit.p1_entry_audit.run_p1_audit().
    report_path : str | Path | None
        Output path. If None, defaults to docs/P1_ENTRY_AUDIT_{date}.md.

    Returns
    -------
    Path
        The path where the report was written.
    """
    if report_path is None:
        date_str = datetime.now().strftime("%Y%m%d")
        report_path = DEFAULT_DOCS_DIR / f"P1_ENTRY_AUDIT_{date_str}.md"

    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    entries = audit_result.get("audit_entries", [])

    sections = [
        _section_header(audit_result),
        "",
        _section_summary(audit_result),
        "",
        _section_entry_lock(entries),
        "",
        _section_trade_setup(entries),
        "",
        _section_position_sizing(entries),
        "",
        _section_divergences(entries),
        "",
        _section_risk_notes(),
    ]

    report_path.write_text("\n".join(sections), encoding="utf-8")
    return report_path
