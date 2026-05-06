# =============================================================
# tests/smoke_p1_entry_audit.py
# =============================================================
# Offline smoke test for Architecture v1.6 P1 audit runner.
#
# No network I/O. Injects DataFrames and mock snapshot dict.
# Does NOT write any report files (write_report=False).
# =============================================================

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from audit.p1_entry_audit import run_p1_audit


def _build_mock_close_volume():
    """Build 11-bar DataFrames for three mock tickers."""
    # PASS_TW: ascending price, high volume today → all locks should PASS (BULL market)
    prices_pass = [95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105]
    vol_pass = [1_000_000] * 10 + [2_000_000]  # today > avg

    # BLOCK_TW: price well below MA — L3/L4 should BLOCK
    prices_block = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 78]
    vol_block = [1_000_000] * 10 + [500_000]   # today < avg

    # EARLY_TW: ascending price, good volume → L1 WARN (EARLY level)
    prices_early = prices_pass[:]
    vol_early = vol_pass[:]

    close = pd.DataFrame({
        "PASS_TW": prices_pass,
        "BLOCK_TW": prices_block,
        "EARLY_TW": prices_early,
    })

    volume = pd.DataFrame({
        "PASS_TW": vol_pass,
        "BLOCK_TW": vol_block,
        "EARLY_TW": vol_early,
    })

    return close, volume


def _build_mock_snapshot():
    """Return a minimal mock snapshot dict (no file I/O required)."""
    return {
        "generated_at": "2026-05-07T00:00:00",
        "market_state": "BULL",
        "vix_value": 18.0,
        "signals": [
            {"ticker": "PASS_TW",  "signal": "BUY",  "level": "ATTACK"},
            {"ticker": "BLOCK_TW", "signal": "BUY",  "level": "READY"},
            {"ticker": "EARLY_TW", "signal": "BUY",  "level": "EARLY"},
        ],
        "ranked": [
            {
                "ticker": "PASS_TW", "name": "Pass Stock",
                "sector": "Tech", "score": 180.0, "level": "ATTACK",
            },
            {
                "ticker": "BLOCK_TW", "name": "Block Stock",
                "sector": "Finance", "score": 100.0, "level": "READY",
            },
            {
                "ticker": "EARLY_TW", "name": "Early Stock",
                "sector": "Energy", "score": 80.0, "level": "EARLY",
            },
        ],
        "decisions": {
            # pipeline decided BUY for PASS_TW — expect no BLOCK divergence
            "PASS_TW": {
                "action": "BUY",
                "position_size": 0.1,
                "stop_loss": 0.05,
                "reason": "NORMAL",
            },
        },
    }


def _assert(condition, message):
    if not condition:
        print(f"  ✗ FAIL: {message}")
        raise AssertionError(message)
    print(f"  ✓ {message}")


def main():
    print("=" * 55)
    print("Smoke Test: Architecture v1.6 P1 Entry Audit Runner")
    print("=" * 55)

    close, volume = _build_mock_close_volume()
    snapshot = _build_mock_snapshot()

    result = run_p1_audit(
        snapshot_data=snapshot,
        close=close,
        volume=volume,
        write_report=False,
    )

    entries = result["audit_entries"]
    safety = result["safety"]
    summary = result["audit_summary"]

    # ── Safety assertions ────────────────────────────────────
    print("\n[Safety]")
    _assert(safety["advisory_only"] is True, "advisory_only == True")
    _assert(safety["runtime_modified"] is False, "runtime_modified == False")
    _assert(safety["snapshot_modified"] is False, "snapshot_modified == False")
    _assert(safety["broker_login"] is False, "broker_login == False")
    _assert(safety["auto_trade"] is False, "auto_trade == False")

    # ── Entry count ──────────────────────────────────────────
    print("\n[Entries]")
    _assert(len(entries) == 3, f"3 audit_entries (got {len(entries)})")

    for e in entries:
        _assert(e["runtime_changed"] is False,
                f"{e['ticker']}: runtime_changed == False")
        valid_actions = {
            "ENTRY", "ENTRY_REDUCED", "WAIT", "SKIP",
            "DATA_UNAVAILABLE", "SETUP_REJECTED", "SIZING_INFEASIBLE",
        }
        _assert(e["p1_audit_action"] in valid_actions,
                f"{e['ticker']}: p1_audit_action '{e['p1_audit_action']}' in valid set")

    # ── EARLY_TW: L1 must be WARN (EARLY level) ─────────────
    print("\n[EARLY_TW — L1 must be WARN]")
    early = next(e for e in entries if e["ticker"] == "EARLY_TW")
    l1_status = early["entry_lock"]["locks"]["L1_selection"]["status"]
    _assert(l1_status == "WARN",
            f"EARLY_TW L1_selection == WARN (got {l1_status})")
    _assert(early["p1_audit_action"] == "ENTRY_REDUCED",
            f"EARLY_TW p1_audit_action == ENTRY_REDUCED (got {early['p1_audit_action']})")

    # ── BLOCK_TW: must be BLOCK / WAIT ──────────────────────
    print("\n[BLOCK_TW — must be BLOCK / WAIT]")
    block = next(e for e in entries if e["ticker"] == "BLOCK_TW")
    block_lock_status = block["entry_lock"]["entry_lock_status"]
    _assert(block_lock_status == "BLOCK",
            f"BLOCK_TW entry_lock_status == BLOCK (got {block_lock_status})")
    _assert(block["p1_audit_action"] == "WAIT",
            f"BLOCK_TW p1_audit_action == WAIT (got {block['p1_audit_action']})")

    # ── PASS_TW: no BLOCK divergence against pipeline BUY ───
    print("\n[PASS_TW — no P0_BLOCK_vs_PIPELINE_BUY divergence]")
    pass_e = next(e for e in entries if e["ticker"] == "PASS_TW")
    _assert("P0_BLOCK_vs_PIPELINE_BUY" not in pass_e["divergence_flags"],
            "PASS_TW has no P0_BLOCK_vs_PIPELINE_BUY flag")

    # ── BLOCK_TW: no pipeline decision → NO_PIPELINE_DECISION
    print("\n[BLOCK_TW — NO_PIPELINE_DECISION flag]")
    _assert("NO_PIPELINE_DECISION" in block["divergence_flags"],
            "BLOCK_TW has NO_PIPELINE_DECISION flag")

    # ── Summary counts ───────────────────────────────────────
    print("\n[Summary]")
    _assert(summary["total_signals"] == 3, f"total_signals == 3")
    _assert(summary["data_source"] == "INJECTED", f"data_source == INJECTED")

    # ── Output display ───────────────────────────────────────
    print("\n[Results]")
    for e in entries:
        print(f"  {e['ticker']:12s} "
              f"lock={e['entry_lock']['entry_lock_status']:6s} "
              f"setup={e['trade_setup']['setup_status']:20s} "
              f"p1={e['p1_audit_action']:20s} "
              f"flags={e['divergence_flags']}")

    print(f"\n  Summary: {summary}")

    print("\n" + "=" * 55)
    print("Smoke P1 Entry Audit: PASSED")
    print("=" * 55)


if __name__ == "__main__":
    main()
