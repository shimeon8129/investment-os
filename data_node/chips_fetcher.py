"""
data_node/chips_fetcher.py

Daily chips refresh pipeline — wraps steps/fetch_chips.py and adds:
- chip_status: STRONG_POSITIVE / POSITIVE / MIXED / DIVERGENCE / STRONG_DIVERGENCE / STALE / MISSING
- chip_freshness: FRESH / STALE / MISSING
- Unified output schema per Build Plan Layer C

Output files:
  data/chips/YYYY-MM-DD_chips.json
  data/chips/latest_chips.json
"""

import json
import os
import sys
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from steps.fetch_chips import (
    fetch_with_backoff,
    parse_twse,
    parse_tpex,
    score_chip_flow,
    twse_url,
    tpex_url,
    normalize_code,
)

OUTPUT_DIR = "data/chips"
LATEST_PATH = os.path.join(OUTPUT_DIR, "latest_chips.json")

# A chip date is FRESH if it matches today or yesterday's trading day
_FRESH_DAYS = 2


def compute_chip_status(row: dict) -> str:
    foreign = row.get("foreign_net_buy", 0)
    trust = row.get("trust_net_buy", 0)
    dealer = row.get("dealer_net_buy", 0)
    total = row.get("institutional_net_buy", 0)

    if total == 0 and foreign == 0 and trust == 0 and dealer == 0:
        return "MISSING"
    if foreign < 0 and trust < 0 and dealer < 0:
        return "STRONG_DIVERGENCE"
    if total > 1_000_000 and foreign > 0:
        return "STRONG_POSITIVE"
    if total > 0 and foreign > 0:
        return "POSITIVE"
    if total < 0 or foreign < 0:
        return "DIVERGENCE"
    return "MIXED"


def compute_chip_freshness(chip_date_str: str, run_date: date = None) -> str:
    if not chip_date_str:
        return "MISSING"
    try:
        chip_date = datetime.strptime(chip_date_str, "%Y-%m-%d").date()
        ref = run_date or date.today()
        delta = (ref - chip_date).days
        return "FRESH" if delta <= _FRESH_DAYS else "STALE"
    except ValueError:
        return "MISSING"


def fetch_and_build(tickers: list = None, run_date: date = None) -> dict:
    """
    Fetch latest institutional chips data for given tickers (or all).
    Returns unified chips report dict.
    """
    twse_data, twse_date = fetch_with_backoff(twse_url)
    tpex_data, tpex_date = fetch_with_backoff(tpex_url)

    twse_rows = parse_twse(twse_data)
    tpex_rows = parse_tpex(tpex_data)

    ref_date = run_date or date.today()
    today_str = ref_date.strftime("%Y-%m-%d")

    all_codes = set()
    if tickers:
        for t in tickers:
            all_codes.add(normalize_code(t))
    else:
        all_codes = set(twse_rows.keys()) | set(tpex_rows.keys())

    items = []
    for code in all_codes:
        ticker_tw = f"{code}.TW"
        ticker_two = f"{code}.TWO"

        row = tpex_rows.get(code) if (ticker_two in (tickers or [])) else twse_rows.get(code)
        if not row:
            row = twse_rows.get(code) or tpex_rows.get(code)
        if not row:
            continue

        chip_date = twse_date if row.get("market") == "TWSE" else tpex_date
        chip_score = score_chip_flow(row)
        chip_status = compute_chip_status(row)
        chip_freshness = compute_chip_freshness(chip_date, ref_date)
        institutional_bias = (
            "BUY" if row["institutional_net_buy"] > 0
            else "SELL" if row["institutional_net_buy"] < 0
            else "FLAT"
        )

        items.append({
            "date": chip_date,
            "ticker": row.get("ticker", ticker_tw),
            "code": code,
            "name": row.get("name", ""),
            "market": row.get("market", "TWSE"),
            "foreign_net_buy": row.get("foreign_net_buy", 0),
            "trust_net_buy": row.get("trust_net_buy", 0),
            "dealer_net_buy": row.get("dealer_net_buy", 0),
            "institutional_net_buy": row.get("institutional_net_buy", 0),
            "chip_score": chip_score,
            "institutional_bias": institutional_bias,
            "chip_status": chip_status,
            "chip_freshness": chip_freshness,
        })

    items.sort(key=lambda r: r["chip_score"], reverse=True)

    return {
        "generated_at": today_str,
        "source": "twse_tpex_institutional",
        "market_dates": {"TWSE": twse_date, "TPEX": tpex_date},
        "total": len(items),
        "items": items,
    }


def save(report: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dated_path = os.path.join(OUTPUT_DIR, f"{report['generated_at']}_chips.json")
    for path in [dated_path, LATEST_PATH]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Chips saved: {dated_path}")
    print(f"Chips saved: {LATEST_PATH}")


def load_latest() -> dict:
    if not os.path.exists(LATEST_PATH):
        return {}
    with open(LATEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_chip_map(report: dict) -> dict:
    """Return {code: chip_item} for quick lookup."""
    return {item["code"]: item for item in report.get("items", [])}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="Run date YYYY-MM-DD")
    args = parser.parse_args()

    run_date = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else None

    print("Fetching chips data...")
    report = fetch_and_build(run_date=run_date)
    save(report)

    print(f"\nTotal: {report['total']} tickers")
    print(f"TWSE date: {report['market_dates']['TWSE']}")
    print(f"TPEX date: {report['market_dates']['TPEX']}")
    print("\nTop 10 by chip score:")
    for row in report["items"][:10]:
        print(
            f"  {row['ticker']} {row['name']} | "
            f"chip_score={row['chip_score']} | "
            f"status={row['chip_status']} | "
            f"freshness={row['chip_freshness']} | "
            f"total={row['institutional_net_buy']:,}"
        )


if __name__ == "__main__":
    main()
