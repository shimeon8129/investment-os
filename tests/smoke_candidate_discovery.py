# tests/smoke_candidate_discovery.py
"""
Offline smoke test for Candidate Discovery Pool v0.1.
No network I/O. No file writes. Uses synthetic mock data.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from discovery.data_quality_gate import validate, run_gate
from discovery.etf_source_fetcher import (
    get_etf_holdings,
    load_ai_watchlist_candidates,
    load_ai_watchlist_codes,
    ACTIVE_ETFS,
    SEMICONDUCTOR_ETFS,
)
from discovery.discovery_pool_builder import build_pool, build_summary
from reporting.candidate_discovery_report import generate_report


def _assert(condition, message):
    if not condition:
        print(f"  ✗ FAIL: {message}")
        raise AssertionError(message)
    print(f"  ✓ {message}")


def _make_raw_candidates():
    return [
        {
            "ticker": "2330", "name": "台積電", "industry": "Core",
            "source_type": "ETF_HOLDING", "source_name": "元大台灣50",
            "source_ticker_or_etf": "0050", "source_weight": 0.458,
            "source_date": "2026-04-30",
            "active_etf_flag": False, "momentum_etf_flag": False,
            "_semiconductor_etf_flag": False,
        },
        {
            "ticker": "3363", "name": "上詮", "industry": "矽光子",
            "source_type": "ETF_HOLDING", "source_name": "中信AI晶片",
            "source_ticker_or_etf": "00993A", "source_weight": 0.051,
            "source_date": "2026-04-30",
            "active_etf_flag": True, "momentum_etf_flag": False,
            "_semiconductor_etf_flag": False,
        },
        {
            "ticker": "NVDA", "name": "NVIDIA", "industry": "GPU",
            "source_type": "ETF_HOLDING", "source_name": "統一FANG+",
            "source_ticker_or_etf": "00757", "source_weight": 0.125,
            "source_date": "2026-04-30",
            "active_etf_flag": False, "momentum_etf_flag": False,
            "_semiconductor_etf_flag": False,
        },
        {
            "ticker": "2454", "name": "WRONG NAME", "industry": "IC Design",
            "source_type": "ETF_HOLDING", "source_name": "富邦科技",
            "source_ticker_or_etf": "0052", "source_weight": 0.061,
            "source_date": "2026-04-30",
            "active_etf_flag": False, "momentum_etf_flag": False,
            "_semiconductor_etf_flag": False,
        },
        {
            "ticker": "??BAD", "name": "Unknown", "industry": "",
            "source_type": "ETF_HOLDING", "source_name": "test",
            "source_ticker_or_etf": "test", "source_weight": 0.01,
            "source_date": "2026-04-30",
            "active_etf_flag": False, "momentum_etf_flag": False,
            "_semiconductor_etf_flag": False,
        },
    ]


def test_data_quality_gate():
    print("\n[Data Quality Gate]")
    raw = _make_raw_candidates()
    universe_codes = {"2330", "2454"}
    master_map = {"2330": "台積電", "2454": "聯發科"}

    results = [validate(c.copy(), universe_codes, master_map) for c in raw]

    r_2330 = next(r for r in results if r["normalized_ticker"] == "2330")
    _assert(r_2330["data_quality_status"] == "EXISTING_UNIVERSE_REINFORCED",
            "2330 → EXISTING_UNIVERSE_REINFORCED")
    _assert(r_2330["already_in_universe"] is True, "2330 → already_in_universe=True")

    r_3363 = next(r for r in results if r["normalized_ticker"] == "3363")
    _assert(r_3363["data_quality_status"] == "NEW_DISCOVERY_CANDIDATE",
            "3363 → NEW_DISCOVERY_CANDIDATE")

    r_nvda = next(r for r in results if r["normalized_ticker"] == "NVDA")
    _assert(r_nvda["data_quality_status"] == "THEME_MAPPING_ONLY",
            "NVDA → THEME_MAPPING_ONLY")
    _assert(r_nvda["us_mapping_flag"] is True, "NVDA → us_mapping_flag=True")

    r_2454 = next(r for r in results if r["normalized_ticker"] == "2454")
    _assert(r_2454["data_quality_status"] == "SOURCE_CONFLICT_REVIEW",
            "2454 name mismatch → SOURCE_CONFLICT_REVIEW")

    r_bad = next(r for r in results if "BAD" in r["normalized_ticker"])
    _assert(r_bad["data_quality_status"] == "REJECT_BAD_TICKER",
            "??BAD → REJECT_BAD_TICKER")


def test_etf_fetcher():
    print("\n[ETF Source Fetcher]")
    logs = []

    h_0050 = get_etf_holdings("0050", logs)
    _assert(len(h_0050) > 0, "0050 returns holdings")
    _assert(h_0050[0]["active_etf_flag"] is False, "0050 → active_etf_flag=False")
    _assert(h_0050[0]["source_ticker_or_etf"] == "0050", "source_ticker_or_etf == '0050'")

    h_active = get_etf_holdings("00993A", logs)
    _assert(len(h_active) > 0, "00993A returns holdings")
    _assert(h_active[0]["active_etf_flag"] is True, "00993A → active_etf_flag=True")

    h_semi = get_etf_holdings("00891", logs)
    _assert(h_semi[0]["_semiconductor_etf_flag"] is True, "00891 → _semiconductor_etf_flag=True")

    h_missing = get_etf_holdings("NONEXISTENT", logs)
    _assert(h_missing == [], "unknown ETF → empty list (no crash)")
    _assert(any("skipping" in l for l in logs), "missing ETF logged")


def test_discovery_pool_builder():
    print("\n[Discovery Pool Builder]")
    raw = _make_raw_candidates()
    universe_codes = {"2330", "2454"}
    master_map = {"2330": "台積電", "2454": "聯發科"}

    validated = [validate(c.copy(), universe_codes, master_map) for c in raw]
    ai_codes = {"2330", "3363"}
    pool, csv_path = build_pool(validated, ai_codes, run_date="2026-05-07", write_csv=False)

    _assert(csv_path is None, "write_csv=False → csv_path=None")
    _assert(len(pool) > 0, "pool has records")

    us_mixed = [r for r in pool
                if r.get("us_mapping_flag") and r["discovery_status"] != "THEME_MAPPING_ONLY"]
    _assert(len(us_mixed) == 0, "US symbols not mixed into TW ranking")

    for field in ["ticker", "discovery_score", "discovery_status", "recommended_action", "date"]:
        _assert(field in pool[0], f"field '{field}' present in pool records")

    r_2330 = next((r for r in pool if r["normalized_ticker"] == "2330"), None)
    _assert(r_2330 is not None, "2330 in pool")
    _assert(r_2330.get("_in_ai_watchlist") is True, "2330 → _in_ai_watchlist=True")
    _assert(r_2330["discovery_score"] >= 20, f"2330 score >= 20 (got {r_2330['discovery_score']})")

    summary = build_summary(pool)
    _assert(isinstance(summary, dict), "build_summary returns dict")


def test_report_generator():
    print("\n[Report Generator]")
    pool = [
        {
            "ticker": "2330", "name": "台積電", "industry": "Core",
            "source_ticker_or_etf": "0050,00891", "source_weight": 0.45,
            "close": 950.0, "pct_change": 1.5,
            "note": "AI watchlist confirmed",
            "discovery_status": "EXISTING_UNIVERSE_REINFORCED",
            "recommended_action": "WATCH_EXISTING_UNIVERSE",
        },
        {
            "ticker": "NVDA", "name": "NVIDIA", "industry": "GPU",
            "source_ticker_or_etf": "00757", "source_weight": 0.125,
            "close": "DATA_MISSING", "pct_change": "DATA_MISSING", "note": "",
            "discovery_status": "THEME_MAPPING_ONLY",
            "recommended_action": "US_MAPPING_ONLY",
        },
    ]
    summary = {"EXISTING_UNIVERSE_REINFORCED": 1, "THEME_MAPPING_ONLY": 1}
    gate_log = ["[GATE] sample log entry"]

    text = generate_report(pool, summary, gate_log, run_date="2026-05-07", write_file=False)

    required_sections = [
        "## 1. Executive Summary",
        "## 2. Existing Universe Reinforced",
        "## 3. New Discovery Candidates",
        "## 4. Source Conflict Review",
        "## 5. Theme Mapping Only",
        "## 6. Data Quality Gate Findings",
        "## 7. Owner Review List",
    ]
    for section in required_sections:
        _assert(section in text, f"report contains '{section}'")

    _assert("NVDA" in text, "NVDA appears in report")
    _assert("台積電" in text, "台積電 appears in report")
    _assert("DATA_MISSING" in text, "DATA_MISSING rendered in report")


def test_universe_not_modified():
    print("\n[Guardrail: universe_tw.csv not modified]")
    universe_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "universe_tw.csv"
    )
    if not os.path.exists(universe_path):
        print("  - universe_tw.csv not found, skipping guardrail check")
        return
    with open(universe_path, "r", encoding="utf-8") as f:
        original = f.read()
    run_gate([{"ticker": "2330", "name": "台積電", "source_name": "x", "source_date": "2026-04-30"}])
    with open(universe_path, "r", encoding="utf-8") as f:
        after = f.read()
    _assert(original == after, "universe_tw.csv unchanged after run_gate()")


def main():
    print("=" * 60)
    print("Smoke Test: Candidate Discovery Pool + Data Quality Gate v0.1")
    print("=" * 60)

    test_data_quality_gate()
    test_etf_fetcher()
    test_discovery_pool_builder()
    test_report_generator()
    test_universe_not_modified()

    print("\n" + "=" * 60)
    print("Smoke Candidate Discovery: PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
