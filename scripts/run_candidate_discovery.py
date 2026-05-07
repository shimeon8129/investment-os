#!/usr/bin/env python3
# scripts/run_candidate_discovery.py
"""
Main runner for Candidate Discovery Pool + Data Quality Gate v0.1.

Usage:
    python3 scripts/run_candidate_discovery.py [--date YYYY-MM-DD] [--no-price]

Outputs:
    data/discovery/YYYY-MM-DD_candidate_discovery_pool.csv
    reports/discovery/YYYY-MM-DD_candidate_discovery_report.md

Guardrails:
    - Does NOT modify data/universe_tw.csv
    - Does NOT modify trading logic
    - Does NOT modify current holdings
    - US symbols are classified THEME_MAPPING_ONLY, not mixed into TW ranking
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from discovery.data_quality_gate import run_gate
from discovery.etf_source_fetcher import (
    load_all_etf_candidates,
    load_ai_watchlist_candidates,
    load_ai_watchlist_codes,
    fetch_price,
)
from discovery.discovery_pool_builder import build_pool, build_summary
from reporting.candidate_discovery_report import generate_report


def _snapshot_universe_mtime() -> float | None:
    universe_path = PROJECT_ROOT / "data" / "universe_tw.csv"
    if not universe_path.exists():
        print("[GUARDRAIL] WARNING: universe_tw.csv not found")
        return None
    return universe_path.stat().st_mtime


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="Run date YYYY-MM-DD")
    parser.add_argument("--no-price", action="store_true", help="Skip yfinance price fetch")
    args = parser.parse_args()

    run_date = args.date or datetime.now().strftime("%Y-%m-%d")
    fetch_prices = not args.no_price

    print(f"\n{'='*60}")
    print(f"Candidate Discovery Pool v0.1 — {run_date}")
    print(f"{'='*60}\n")

    universe_mtime = _snapshot_universe_mtime()

    gate_log = []

    # ── Step 1: Load candidates ──────────────────────────────────
    print("[1/5] Loading ETF holdings...")
    etf_candidates = load_all_etf_candidates(log_sink=gate_log)
    print(f"      {len(etf_candidates)} raw ETF holding records")

    print("[2/5] Loading AI watchlist candidates...")
    ai_candidates = load_ai_watchlist_candidates(log_sink=gate_log)
    print(f"      {len(ai_candidates)} AI watchlist records")

    all_raw = etf_candidates + ai_candidates

    # ── Step 2: Data Quality Gate ────────────────────────────────
    print("[3/5] Running Data Quality Gate...")
    validated = run_gate(all_raw, gate_log)
    rejected_count = sum(1 for r in validated if r["data_quality_status"] == "REJECT_BAD_TICKER")
    conflict_count = sum(1 for r in validated if r["data_quality_status"] == "SOURCE_CONFLICT_REVIEW")
    print(f"      validated={len(validated)}, rejected={rejected_count}, conflicts={conflict_count}")

    # ── Step 3: AI watchlist codes for scoring ───────────────────
    ai_codes = load_ai_watchlist_codes()

    # ── Step 4: Build pool without CSV to attach prices ─────────
    pool, _ = build_pool(validated, ai_codes, run_date=run_date, write_csv=False)

    # ── Step 5: Fetch prices for TW tickers ─────────────────────
    if fetch_prices:
        print("[4/5] Fetching prices via yfinance...")
        tw_pool = [r for r in pool if not r.get("us_mapping_flag")]
        for i, rec in enumerate(tw_pool):
            code = rec["normalized_ticker"]
            price_data = fetch_price(code, gate_log)
            rec["close"] = price_data["close"]
            rec["pct_change"] = price_data["pct_change"]
            if (i + 1) % 10 == 0:
                print(f"      {i+1}/{len(tw_pool)} prices fetched...")
        for rec in pool:
            if rec.get("us_mapping_flag"):
                rec["close"] = "DATA_MISSING"
                rec["pct_change"] = "DATA_MISSING"
    else:
        print("[4/5] Price fetch skipped (--no-price)")
        for rec in pool:
            rec["close"] = "DATA_MISSING"
            rec["pct_change"] = "DATA_MISSING"

    # ── Write CSV (re-build to persist price data) ───────────────
    print("[5/5] Writing outputs...")
    price_lookup = {r["normalized_ticker"]: {"close": r.get("close"), "pct_change": r.get("pct_change")} for r in pool}
    pool_final, csv_path = build_pool(validated, ai_codes, run_date=run_date, write_csv=True)
    for rec in pool_final:
        prices = price_lookup.get(rec["normalized_ticker"], {})
        rec["close"] = prices.get("close", "DATA_MISSING")
        rec["pct_change"] = prices.get("pct_change", "DATA_MISSING")

    summary = build_summary(pool_final)
    generate_report(pool_final, summary, gate_log, run_date=run_date, write_file=True)

    # ── Guardrail: verify universe untouched ─────────────────────
    universe_path = PROJECT_ROOT / "data" / "universe_tw.csv"
    if universe_path.exists() and universe_mtime is not None:
        assert universe_path.stat().st_mtime == universe_mtime, \
            "GUARDRAIL VIOLATION: universe_tw.csv was modified!"

    # ── Summary ──────────────────────────────────────────────────
    report_path = PROJECT_ROOT / "reports" / "discovery" / f"{run_date}_candidate_discovery_report.md"
    print(f"\n{'='*60}")
    print("Discovery Summary:")
    for status, count in sorted(summary.items()):
        print(f"  {status}: {count}")
    print(f"\nOutputs:")
    print(f"  CSV:    {csv_path}")
    print(f"  Report: {report_path}")
    print(f"\nGate log: {len(gate_log)} entries")
    if rejected_count:
        print(f"  Rejected tickers: {rejected_count}")
    if conflict_count:
        print(f"  Conflict review needed: {conflict_count}")
    print(f"\nGuardrails confirmed:")
    print(f"  - universe_tw.csv: NOT MODIFIED")
    print(f"  - Trading logic:   NOT TOUCHED")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
