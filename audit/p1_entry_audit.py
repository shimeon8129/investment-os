# =============================================================
# audit/p1_entry_audit.py
# =============================================================
# Architecture v1.6 P1: Parallel Audit Runner
#
# Reads data/processed/mainline_snapshot.json (read-only).
# Wires: TradeSetupBuilder → PositionSizing → EntryLockEngine.
# Writes data/processed/p1_audit_report.json (new file only).
#
# Hard constraints (enforced by import list):
#   - Does NOT modify pipeline/main_v1.py
#   - Does NOT modify execution/risk.py
#   - Does NOT import decision.risk_lock (out-of-scope, not reviewed)
#   - Does NOT write to mainline_snapshot.json
#   - Does NOT execute trades or login to any broker
#   - runtime_changed is always False
# =============================================================

import json
from datetime import datetime
from pathlib import Path

from decision.entry_lock_engine import evaluate_all
from decision.trade_setup_builder import build_trade_setup
from risk.position_sizing import calculate_position_size

_DEFAULT_SNAPSHOT = "data/processed/mainline_snapshot.json"
_DEFAULT_REPORT = "data/processed/p1_audit_report.json"
_DEFAULT_CAPITAL = 100_000
_PRICE_PERIOD = "1y"


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _load_snapshot(snapshot_path):
    path = Path(snapshot_path)
    with open(path, "r", encoding="utf-8") as f:
        snap = json.load(f)

    if "market_state" not in snap:
        raise ValueError(f"snapshot missing market_state: {snapshot_path}")

    snap.setdefault("signals", [])
    snap.setdefault("decisions", {})
    snap.setdefault("ranked", [])
    return snap


def _reload_prices(tickers, period=_PRICE_PERIOD):
    """
    Reload close/volume via data_node.loader.load_price_data.
    Returns (close, volume, status) where status is RELOADED or RELOAD_FAILED.
    load_price_data(tickers, period) — period default "1mo"; we use "1y" for MA.
    Raises ValueError if all tickers fail; we catch that here.
    """
    if not tickers:
        return None, None, "NO_TICKERS"

    try:
        from data_node.loader import load_price_data
        close, volume = load_price_data(tickers, period=period)
        return close, volume, "RELOADED"
    except Exception as exc:
        print(f"⚠️  P1 price reload failed: {exc}")
        return None, None, "RELOAD_FAILED"


def _build_ranked_map(snapshot):
    """Extract {ticker: {name, sector, score, level}} from ranked[]."""
    ranked_map = {}
    for r in snapshot.get("ranked", []):
        t = r.get("ticker")
        if t:
            ranked_map[t] = {
                "name": r.get("name", t),
                "sector": r.get("sector", "-"),
                "score": r.get("score", 0),
                "level": r.get("level", ""),
            }
    return ranked_map


def _skip_lock(reason):
    """Return a SKIP lock dict for all layers when data is unavailable."""
    layer = {
        "status": "SKIP",
        "severity": "INFO",
        "reason": reason,
        "source_module": "p1_entry_audit",
    }
    return {
        "entry_lock_status": "SKIP",
        "final_action_suggestion": "WAIT",
        "blocked_by": [],
        "locks": {
            "L0_market": layer,
            "L1_selection": layer,
            "L2_setup": layer,
            "L3_validation": layer,
            "L4_risk": layer,
        },
    }


def _p1_audit_action(entry_lock_status, setup, sizing):
    """
    Derive p1_audit_action and p1_audit_reason from P0 module outputs.
    Priority: BLOCK/SKIP > DATA_UNAVAILABLE > SETUP_REJECTED
              > SIZING_INFEASIBLE > ENTRY_REDUCED > ENTRY
    """
    if entry_lock_status == "BLOCK":
        return "WAIT", "EntryLock BLOCK"
    if entry_lock_status == "SKIP":
        return "SKIP", "EntryLock SKIP"
    if setup.get("setup_status") == "INSUFFICIENT_DATA":
        return "DATA_UNAVAILABLE", "TradeSetup insufficient data"
    if setup.get("setup_status") == "INVALID":
        rr = setup.get("risk_reward")
        return "SETUP_REJECTED", f"TradeSetup INVALID (R/R={rr})"
    if not sizing.get("feasible", False):
        return "SIZING_INFEASIBLE", "PositionSizing not feasible"
    if entry_lock_status == "WARN":
        return "ENTRY_REDUCED", "EntryLock WARN — reduced size recommended"
    return "ENTRY", "All L0-L4 PASS; setup VALID; sizing feasible"


def _compute_divergence_flags(p1_action, pipeline_decision, setup, sizing):
    """Compare P1 audit action against pipeline decision; return flag list."""
    flags = []
    p_action = (pipeline_decision or {}).get("action", "")

    if pipeline_decision is None:
        if p1_action == "ENTRY":
            flags.append("P0_ENTRY_vs_NO_PIPELINE")
        flags.append("NO_PIPELINE_DECISION")
    else:
        if p1_action == "WAIT" and p_action == "BUY":
            flags.append("P0_BLOCK_vs_PIPELINE_BUY")
        elif p1_action == "ENTRY_REDUCED" and p_action == "BUY":
            flags.append("P0_WARN_vs_PIPELINE_BUY")
        elif p1_action == "ENTRY" and p_action in ("HOLD", "NO_TRADE"):
            flags.append("P0_ENTRY_vs_PIPELINE_HOLD")

    rr = setup.get("risk_reward")
    if rr is not None and rr < 1.0:
        flags.append("SETUP_INVALID_RR")
    if not sizing.get("feasible", True):
        flags.append("SIZING_NOT_FEASIBLE")

    return flags


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def run_p1_audit(
    snapshot_path=_DEFAULT_SNAPSHOT,
    capital=_DEFAULT_CAPITAL,
    close=None,
    volume=None,
    snapshot_data=None,
    write_report=True,
    report_path=_DEFAULT_REPORT,
):
    """
    Architecture v1.6 P1 Parallel Audit Runner.

    Reads mainline_snapshot.json; wires TradeSetupBuilder + PositionSizing +
    EntryLockEngine; writes a sidecar audit report.
    Runtime decisions are NEVER changed.

    Parameters
    ----------
    snapshot_path : str
        Path to mainline_snapshot.json (read-only).
    capital : float
        Total capital for position sizing. Default 100,000.
    close : pd.DataFrame | None
        Pre-loaded close prices. If None, reloaded via data_node.loader.
    volume : pd.DataFrame | None
        Pre-loaded volume. If None, reloaded via data_node.loader.
    snapshot_data : dict | None
        If provided, bypasses file read (for testing / offline mode).
    write_report : bool
        If True, writes p1_audit_report.json.
    report_path : str
        Output path for the JSON audit report.

    Returns
    -------
    dict
        Audit result with audit_entries[], audit_summary, and safety block.
    """
    # 1. Load snapshot
    snap = snapshot_data if snapshot_data is not None else _load_snapshot(snapshot_path)

    market_state = snap.get("market_state", "UNKNOWN")
    vix_value = snap.get("vix_value")
    signals = snap.get("signals", [])
    decisions = snap.get("decisions", {})
    ranked_map = _build_ranked_map(snap)

    signal_tickers = [s["ticker"] for s in signals if s.get("ticker")]

    # 2. Resolve price data
    data_source = "INJECTED"
    if close is None or volume is None:
        close, volume, data_source = _reload_prices(signal_tickers)

    prices_available = (
        close is not None
        and not close.empty
        and data_source != "RELOAD_FAILED"
    )

    # 3. EntryLockEngine — batch evaluate all signals at once
    if prices_available:
        entry_lock_list = evaluate_all(
            close, volume, market_state, vix_value, {}, signals
        )
    else:
        reason = "DATA_RELOAD_FAILED" if data_source == "RELOAD_FAILED" else "NO_PRICE_DATA"
        entry_lock_list = [
            {"ticker": s.get("ticker", ""), **_skip_lock(reason)}
            for s in signals
        ]

    entry_lock_map = {r["ticker"]: r for r in entry_lock_list}

    # 4. Per-ticker: TradeSetupBuilder → PositionSizing → divergence
    audit_entries = []

    for sig in signals:
        ticker = sig.get("ticker", "")
        signal = sig.get("signal", "")
        level = sig.get("level", "")

        info = ranked_map.get(ticker, {})
        name = info.get("name", ticker)
        sector = info.get("sector", "-")

        # TradeSetupBuilder
        if prices_available:
            candidate_hint = {"level": level, **info}
            setup = build_trade_setup(
                ticker=ticker,
                close=close,
                volume=volume,
                signal=signal,
                candidate=candidate_hint,
            )
        else:
            setup = {
                "ticker": ticker,
                "setup_type": "UNKNOWN",
                "entry_zone": None,
                "invalidation_price": None,
                "stop_loss_price": None,
                "target_1": None,
                "target_2": None,
                "risk_reward": None,
                "setup_status": "INSUFFICIENT_DATA",
            }

        # PositionSizing — only when TradeSetup is VALID
        if (
            setup.get("setup_status") == "VALID"
            and setup.get("entry_zone") is not None
            and setup.get("stop_loss_price") is not None
        ):
            sizing = calculate_position_size(
                capital=capital,
                entry_price=setup["entry_zone"],
                stop_price=setup["stop_loss_price"],
                max_loss_pct=0.01,
            )
        else:
            sizing = {
                "shares": 0,
                "position_value": 0.0,
                "position_pct": 0.0,
                "max_loss_value": round(capital * 0.01, 4),
                "risk_per_share": 0.0,
                "feasible": False,
            }

        # EntryLockEngine result for this ticker
        lock = entry_lock_map.get(ticker, _skip_lock("TICKER_NOT_IN_LOCK_MAP"))
        entry_lock_status = lock.get("entry_lock_status", "SKIP")

        # P1 audit action
        if data_source == "RELOAD_FAILED":
            p1_action, p1_reason = "DATA_UNAVAILABLE", "DATA_RELOAD_FAILED"
            div_flags = ["DATA_RELOAD_FAILED"]
        else:
            p1_action, p1_reason = _p1_audit_action(entry_lock_status, setup, sizing)
            pipeline_decision = decisions.get(ticker)
            div_flags = _compute_divergence_flags(p1_action, pipeline_decision, setup, sizing)

        pipeline_decision = decisions.get(ticker)

        audit_entries.append({
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "signal": signal,
            "level": level,
            "source_action": signal,
            "entry_lock": lock,
            "trade_setup": setup,
            "position_sizing": sizing,
            "pipeline_decision": pipeline_decision,
            "p1_audit_action": p1_action,
            "p1_audit_reason": p1_reason,
            "divergence_flags": div_flags,
            "runtime_changed": False,
        })

    # 5. Audit summary
    def _count(field, value):
        return sum(1 for e in audit_entries if e.get(field) == value)

    def _count_lock(value):
        return sum(
            1 for e in audit_entries
            if e.get("entry_lock", {}).get("entry_lock_status") == value
        )

    def _count_setup(value):
        return sum(
            1 for e in audit_entries
            if e.get("trade_setup", {}).get("setup_status") == value
        )

    summary = {
        "total_signals": len(signals),
        "entry_lock_PASS": _count_lock("PASS"),
        "entry_lock_WARN": _count_lock("WARN"),
        "entry_lock_BLOCK": _count_lock("BLOCK"),
        "entry_lock_SKIP": _count_lock("SKIP"),
        "setup_VALID": _count_setup("VALID"),
        "setup_INVALID": _count_setup("INVALID"),
        "setup_INSUFFICIENT_DATA": _count_setup("INSUFFICIENT_DATA"),
        "sizing_feasible": sum(1 for e in audit_entries if e["position_sizing"].get("feasible")),
        "p1_audit_ENTRY": _count("p1_audit_action", "ENTRY"),
        "p1_audit_ENTRY_REDUCED": _count("p1_audit_action", "ENTRY_REDUCED"),
        "p1_audit_WAIT": _count("p1_audit_action", "WAIT"),
        "p1_audit_SKIP": _count("p1_audit_action", "SKIP"),
        "p1_audit_DATA_UNAVAILABLE": _count("p1_audit_action", "DATA_UNAVAILABLE"),
        "p1_audit_SETUP_REJECTED": _count("p1_audit_action", "SETUP_REJECTED"),
        "p1_audit_SIZING_INFEASIBLE": _count("p1_audit_action", "SIZING_INFEASIBLE"),
        "divergence_count": sum(1 for e in audit_entries if e["divergence_flags"]),
        "data_source": data_source,
    }

    # 6. Assemble result
    result = {
        "generated_at": datetime.now().isoformat(),
        "snapshot_generated_at": snap.get("generated_at", ""),
        "snapshot_path": str(snapshot_path),
        "capital": capital,
        "market_state": market_state,
        "vix_value": vix_value,
        "audit_summary": summary,
        "audit_entries": audit_entries,
        "safety": {
            "advisory_only": True,
            "runtime_modified": False,
            "snapshot_modified": False,
            "broker_login": False,
            "auto_trade": False,
            "execution_risk_py_unchanged": True,
        },
    }

    # 7. Write JSON report (new file only, never overwrites snapshot)
    if write_report:
        out = Path(report_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        print(f"📋 Audit report written: {out}")

    return result


# ─────────────────────────────────────────────────────────────
# CLI entry point: python3 -m audit.p1_entry_audit
# ─────────────────────────────────────────────────────────────

def main():
    import sys

    snapshot_path = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_SNAPSHOT

    print("=" * 58)
    print("Architecture v1.6 P1 Entry Audit Runner")
    print("=" * 58)
    print(f"Snapshot : {snapshot_path}")
    print(f"Capital  : {_DEFAULT_CAPITAL:,}")

    result = run_p1_audit(snapshot_path=snapshot_path, write_report=True)

    s = result["audit_summary"]
    print(f"\nMarket   : {result['market_state']} | VIX: {result['vix_value']}")
    print(f"Signals  : {s['total_signals']}")
    print(f"EntryLock: PASS={s['entry_lock_PASS']} WARN={s['entry_lock_WARN']} "
          f"BLOCK={s['entry_lock_BLOCK']} SKIP={s['entry_lock_SKIP']}")
    print(f"Setup    : VALID={s['setup_VALID']} INSUF={s['setup_INSUFFICIENT_DATA']}")
    print(f"P1 Action: ENTRY={s['p1_audit_ENTRY']} REDUCED={s['p1_audit_ENTRY_REDUCED']} "
          f"WAIT={s['p1_audit_WAIT']} SKIP={s['p1_audit_SKIP']} "
          f"UNAVAIL={s['p1_audit_DATA_UNAVAILABLE']}")
    print(f"Divergence count: {s['divergence_count']}")

    if s["divergence_count"]:
        print("\nDivergences:")
        for e in result["audit_entries"]:
            if e["divergence_flags"]:
                print(f"  {e['ticker']:12s} p1={e['p1_audit_action']:20s} "
                      f"pipeline={( e['pipeline_decision'] or {}).get('action','-'):8s} "
                      f"flags={e['divergence_flags']}")

    print(f"\nAdvisory only. runtime_modified={result['safety']['runtime_modified']}")

    from reporting.p1_entry_audit_report import generate_p1_audit_markdown
    md_path = generate_p1_audit_markdown(result)
    print(f"📄 Markdown report : {md_path}")

    print("\n✅ P1 Audit Done")


if __name__ == "__main__":
    main()
