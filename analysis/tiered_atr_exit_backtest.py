#!/usr/bin/env python3
"""
Investment OS — P0.4 Tiered ATR Exit Backtest v0.1

Usage:
    python analysis/tiered_atr_exit_backtest.py \
        --valuation-date 2026-05-26 --entry-capital 100000

Reads:  reports/daily/YYYY-MM-DD_daily_report.md
        yfinance (OHLC price data)
Writes: data/backtest/tiered_atr_exit_backtest_lots.csv
        data/backtest/tiered_atr_exit_backtest_comparison.csv
        data/backtest/tiered_atr_exit_backtest_summary.json
        reports/backtest/tiered_atr_exit_backtest_v0_1.md
        reports/validation/tiered_atr_exit_backtest_validation.md

Advisory and analytical only. No broker connections. No trades placed.
"""
from __future__ import annotations

import argparse
import csv as _csv
import json
import sys
import warnings
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

# P0.2 pure functions — do NOT import broker/execution/controller/decision
from analysis.five_day_top1_atr_backtest import (  # noqa: E402
    fetch_ohlc,
    get_close_series,
    parse_daily_report,
    build_entry,
    simulate_atr_exit,
    simulate_fixed10d_exit,
    simulate_ma_exit,
    compute_position_grade,
    compute_pnl,
    assemble_lot,
    aggregate_basket,
)

# P0.3 helpers
from analysis.rolling_five_day_top1_atr_diagnosis import (  # noqa: E402
    get_available_report_dates,
    build_rolling_baskets,
    flag_immature_basket,
    compute_post_exit_max_return,
)

REPORTS_BACKTEST   = ROOT / "reports" / "backtest"
REPORTS_VALIDATION = ROOT / "reports" / "validation"
DATA_BACKTEST      = ROOT / "data" / "backtest"

TIERED_STRATEGY_ID = "TIERED_ATR_EXIT_BACKTEST_v0_1"
BASKET_WINDOW      = 5

# Tiered ATR multiplier thresholds (based on peak float from entry price)
TIERED_INIT_MULT      = 1.5    # initial_stop = entry - 1.5 × ATR20
TIERED_TRAIL_LOW      = 2.0    # float_pct  < 5%
TIERED_TRAIL_MID      = 2.5    # 5% ≤ float_pct < 15%
TIERED_TRAIL_HIGH     = 3.0    # float_pct ≥ 15%
TIERED_LOW_THRESHOLD  = 0.05
TIERED_HIGH_THRESHOLD = 0.15
HOLD_PROTECTION_DATES = 3      # first N report dates: only initial_stop active

# Threshold for false exit detection (same as P0.3)
ATR_TOO_TIGHT_THRESHOLD = 0.05

ALL_MODELS = [
    "ATR_BASE",
    "ATR_WIDE",
    "TIERED_ATR",
    "TIERED_ATR_NO_HOLD_PROTECTION",
    "FIXED_10D",
    "MA5",
]


# ─────────────────────────────────────────────────────────────
# TIERED ATR trailing stop exit model
# ─────────────────────────────────────────────────────────────

def _tiered_trailing_stop(highest_close: float, entry_price: float, atr20: float) -> float:
    """Compute tiered trailing stop price based on peak float from entry."""
    float_pct = (highest_close - entry_price) / entry_price
    if float_pct < TIERED_LOW_THRESHOLD:
        trail_mult = TIERED_TRAIL_LOW
    elif float_pct < TIERED_HIGH_THRESHOLD:
        trail_mult = TIERED_TRAIL_MID
    else:
        trail_mult = TIERED_TRAIL_HIGH
    return highest_close - trail_mult * atr20


def simulate_tiered_atr_exit(
    entry: dict,
    ohlc: pd.DataFrame,
    report_dates: list[date],
    valuation_date: date,
    hold_protection: bool = True,
) -> dict:
    """ATR trailing stop with tiered multipliers and optional hold protection.

    Multiplier tiers (based on peak float from entry price):
        float_pct  < 5%  → 2.0× ATR
        5% ≤ float_pct < 15% → 2.5× ATR
        float_pct ≥ 15% → 3.0× ATR

    Hold protection: first HOLD_PROTECTION_DATES report dates after entry,
    only initial_stop (1.5×ATR) is active. Trailing stop ignored in this window.
    hold_period_protected=True when trailing would have triggered during protection.
    """
    entry_price = entry.get("entry_price")
    atr20       = entry.get("atr20_at_entry")
    shares      = entry.get("shares", 0) or 0
    ticker      = entry.get("ticker")

    _empty = {
        "exit_model": "TIERED_ATR", "exit_date": None, "exit_price": None,
        "exit_reason": "DATA_INCOMPLETE", "holding_days": None,
        "highest_close_since_entry": None, "trailing_stop_at_exit": None,
        "max_profit_seen": None, "max_drawdown_seen": None,
        "current_price": None, "current_value": None,
        "hold_period_protected": False,
    }
    if entry_price is None or atr20 is None or ticker is None:
        return _empty

    entry_date   = date.fromisoformat(entry["entry_date"])
    initial_stop = entry_price - TIERED_INIT_MULT * atr20
    highest_close = entry_price
    close_series  = get_close_series(ohlc, ticker, entry_date, valuation_date)

    # Determine protection window end date
    if hold_protection:
        post_entry = sorted(d for d in report_dates if d > entry_date)
        protection_end = post_entry[HOLD_PROTECTION_DATES - 1] if len(post_entry) >= HOLD_PROTECTION_DATES \
                         else (post_entry[-1] if post_entry else entry_date)
    else:
        protection_end = entry_date  # empty window → no protection

    max_profit      = 0.0
    max_drawdown    = 0.0
    hold_period_protected = False

    for i, (d, close) in enumerate(close_series):
        if close > highest_close:
            highest_close = close

        trailing_stop = _tiered_trailing_stop(highest_close, entry_price, atr20)

        in_protection = d <= protection_end
        if in_protection:
            if close < trailing_stop and not hold_period_protected:
                hold_period_protected = True  # trailing would have triggered
            effective_stop = initial_stop
        elif i == 0:
            # Outside protection on day 0: floor stops gap-down bypass of initial_stop
            effective_stop = max(trailing_stop, initial_stop)
        else:
            effective_stop = trailing_stop

        unrealized = (close - entry_price) * shares
        if unrealized > max_profit:
            max_profit = unrealized
        if unrealized < max_drawdown:
            max_drawdown = unrealized

        if close < effective_stop:
            return {
                "exit_model":               "TIERED_ATR",
                "exit_date":                d.isoformat(),
                "exit_price":               round(close, 2),
                "exit_reason":              "ATR_TRAILING_STOP",
                "holding_days":             i + 1,
                "highest_close_since_entry": round(highest_close, 2),
                "trailing_stop_at_exit":    round(effective_stop, 2),
                "max_profit_seen":          round(max_profit, 2),
                "max_drawdown_seen":        round(max_drawdown, 2),
                "current_price":            round(close, 2),
                "current_value":            round(close * shares, 2),
                "hold_period_protected":    hold_period_protected,
            }

    # Still open at valuation date
    current_price = close_series[-1][1] if close_series else entry_price
    unrealized = (current_price - entry_price) * shares
    if unrealized > max_profit:
        max_profit = unrealized
    if unrealized < max_drawdown:
        max_drawdown = unrealized

    trailing_stop = _tiered_trailing_stop(highest_close, entry_price, atr20)

    return {
        "exit_model":               "TIERED_ATR",
        "exit_date":                None,
        "exit_price":               None,
        "exit_reason":              "OPEN_POSITION",
        "holding_days":             len(close_series),
        "highest_close_since_entry": round(highest_close, 2),
        "trailing_stop_at_exit":    round(trailing_stop, 2),
        "max_profit_seen":          round(max_profit, 2),
        "max_drawdown_seen":        round(max_drawdown, 2),
        "current_price":            round(current_price, 2),
        "current_value":            round(current_price * shares, 2),
        "hold_period_protected":    hold_period_protected,
    }


# ─────────────────────────────────────────────────────────────
# Per-lot diagnostic metrics + model dispatch
# ─────────────────────────────────────────────────────────────

def compute_profit_giveback_pct(lot: dict) -> Optional[float]:
    """Fraction of peak unrealized profit given back at exit (or valuation).

    Returns None when max_profit_seen is None or ≤ 0 (position never profitable).
    Can exceed 1.0 when a profitable position crosses back into loss.
    """
    peak = lot.get("max_profit_seen")
    if peak is None or peak <= 0:
        return None
    pnl = lot.get("gross_pnl") or 0
    return round((peak - pnl) / peak, 4)


def _run_one_model(
    model_name: str,
    entry: dict,
    ohlc: pd.DataFrame,
    report_dates: list[date],
    valuation_date: date,
) -> dict:
    """Dispatch to the correct exit simulator for the given model name."""
    if model_name == "ATR_BASE":
        return simulate_atr_exit(entry, ohlc, 1.5, 2.0, valuation_date)
    if model_name == "ATR_WIDE":
        return simulate_atr_exit(entry, ohlc, 2.0, 2.5, valuation_date)
    if model_name == "TIERED_ATR":
        return simulate_tiered_atr_exit(entry, ohlc, report_dates, valuation_date,
                                        hold_protection=True)
    if model_name == "TIERED_ATR_NO_HOLD_PROTECTION":
        return simulate_tiered_atr_exit(entry, ohlc, report_dates, valuation_date,
                                        hold_protection=False)
    if model_name == "FIXED_10D":
        return simulate_fixed10d_exit(entry, ohlc, report_dates, valuation_date)
    if model_name == "MA5":
        return simulate_ma_exit(entry, ohlc, ma_period=5, valuation_date=valuation_date)
    raise ValueError(f"Unknown model: {model_name!r}")


# ─────────────────────────────────────────────────────────────
# Per-model comparison metrics aggregation
# ─────────────────────────────────────────────────────────────

def aggregate_model_metrics(
    lots_by_model: dict[str, list[dict]],
) -> dict[str, dict]:
    """Compute per-model comparison metrics from pre-enriched lot dicts.

    Each lot must already contain:
        post_exit_max_return  (float | None) — computed by orchestrator
        profit_giveback_pct   (float | None) — computed by orchestrator
        hold_period_protected (bool)          — from simulate_tiered_atr_exit
    """
    result: dict[str, dict] = {}

    for model_name, lots in lots_by_model.items():
        valid = [
            l for l in lots
            if l.get("data_quality_flag") == "PASS" and l.get("gross_pnl") is not None
        ]

        total_net = sum(l.get("estimated_net_pnl") or 0 for l in valid)

        false_exit = sum(
            1 for l in valid
            if l.get("exit_reason") == "ATR_TRAILING_STOP"
            and (l.get("post_exit_max_return") or 0) > ATR_TOO_TIGHT_THRESHOLD
        )

        max_dd = max((abs(l.get("max_drawdown_seen") or 0) for l in valid), default=0.0)
        worst  = min((l.get("gross_pnl") or 0 for l in valid), default=0.0)

        givebacks = [l["profit_giveback_pct"] for l in valid
                     if l.get("profit_giveback_pct") is not None]
        avg_giveback = round(sum(givebacks) / len(givebacks), 4) if givebacks else None

        protected = sum(1 for l in lots if l.get("hold_period_protected", False))

        result[model_name] = {
            "model_name":                     model_name,
            "total_lots":                     len(valid),
            "total_net_pnl":                  round(total_net, 2),
            "false_exit_count":               false_exit,
            "max_drawdown":                   round(max_dd, 2),
            "largest_single_lot_loss":        round(worst, 2),
            "avg_profit_giveback_pct":        avg_giveback,
            "protected_by_hold_period_count": protected,
        }

    return result


# ─────────────────────────────────────────────────────────────
# Output writers
# ─────────────────────────────────────────────────────────────

def write_lots_csv(lots_by_model: dict[str, list[dict]], path: Path) -> None:
    """Write all lots from all models to a single flat CSV (model_name column included)."""
    all_lots = [lot for lots in lots_by_model.values() for lot in lots]
    if not all_lots:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = _csv.DictWriter(f, fieldnames=list(all_lots[0].keys()))
        writer.writeheader()
        writer.writerows(all_lots)


def write_comparison_csv(model_metrics: dict[str, dict], path: Path) -> None:
    """Write one row per model with comparison metrics."""
    rows = [model_metrics[mn] for mn in ALL_MODELS if mn in model_metrics]
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = _csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_summary_json(result: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "strategy_id":    result.get("strategy_id"),
        "valuation_date": result.get("valuation_date"),
        "n_baskets":      result.get("n_baskets"),
        "model_metrics":  result.get("model_metrics", {}),
    }
    path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )


def write_comparison_report_md(result: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    w = lines.append

    w(f"# Comparison Report — {TIERED_STRATEGY_ID}")
    w("")
    w(f"Generated: {date.today().isoformat()}")
    w(f"Valuation date: {result.get('valuation_date', '—')}")
    w(f"Rolling baskets: {result.get('n_baskets', 0)}")
    w(""); w("---"); w("")

    w("## Model Comparison Summary"); w("")
    w("| Model | TotalNetPnL | FalseExits | MaxDrawdown | WorstLot | AvgGiveback% | Protected |")
    w("|-------|-------------|------------|-------------|----------|--------------|-----------|")
    metrics = result.get("model_metrics", {})
    for mn in ALL_MODELS:
        m = metrics.get(mn, {})
        net  = m.get("total_net_pnl") or 0
        fe   = m.get("false_exit_count", 0)
        dd   = m.get("max_drawdown") or 0
        wl   = m.get("largest_single_lot_loss") or 0
        gb   = m.get("avg_profit_giveback_pct")
        prot = m.get("protected_by_hold_period_count", 0)
        net_str = f"+{net:,.0f}" if net >= 0 else f"{net:,.0f}"
        wl_str  = f"+{wl:,.0f}" if wl >= 0 else f"{wl:,.0f}"
        gb_str  = f"{gb:.1%}" if gb is not None else "—"
        w(f"| {mn} | {net_str} | {fe} | {dd:,.0f} | {wl_str} | {gb_str} | {prot} |")
    w(""); w("---"); w("")

    w("## Model Definitions"); w("")
    w("| Model | Init× | Trail× | Hold Protection |")
    w("|-------|-------|--------|-----------------|")
    w("| ATR_BASE | 1.5 | 2.0 (fixed) | No |")
    w("| ATR_WIDE | 2.0 | 2.5 (fixed) | No |")
    w("| TIERED_ATR | 1.5 | 2.0→2.5→3.0 (float-pct tier) | Yes (3 report dates) |")
    w("| TIERED_ATR_NO_HOLD_PROTECTION | 1.5 | 2.0→2.5→3.0 | No |")
    w("| FIXED_10D | — | — (exit on day 10) | — |")
    w("| MA5 | — | — (close < MA5) | — |")
    w(""); w("---"); w("")

    w("## Tiered Multiplier Logic"); w("")
    w("Based on `(highest_close - entry_price) / entry_price`:")
    w("")
    w("- float_pct  < 5%: trailing = 2.0 × ATR20")
    w("- 5% ≤ float_pct < 15%: trailing = 2.5 × ATR20")
    w("- float_pct ≥ 15%: trailing = 3.0 × ATR20")
    w("")
    w("Hold protection: first 3 report dates after entry → only initial_stop (1.5×ATR) active.")
    w(""); w("---"); w("")

    w("*Advisory only. No trades placed. All outputs for human review.*"); w("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_validation_report_md(result: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    w = lines.append

    w(f"# Validation Report — {TIERED_STRATEGY_ID}"); w("")
    w(f"Generated: {date.today().isoformat()}"); w("")

    w("## Assumptions"); w("")
    w("1. Rolling baskets and OHLC data reuse P0.3 infrastructure (same 15 report dates, 11 baskets)")
    w("2. Entry price = signal-day adjusted close (yfinance auto_adjust=True, v0.1)")
    w("3. Tiered multiplier tiers based on peak float from entry price (highest_close, not current close)")
    w("4. Hold protection window = first 3 report dates (not calendar days) after entry")
    w("5. false_exit_count: exit_reason=ATR_TRAILING_STOP AND post_exit_max_return > 5%")
    w("6. profit_giveback_pct = (max_profit_seen − gross_pnl) / max_profit_seen; None when max_profit_seen ≤ 0")
    w("7. Transaction costs: buy 0.1425%, sell 0.1425% + STT 0.3% on sell value"); w("")

    w("## Known Limitations"); w("")
    w("- Only 15 daily report dates (2026-05-01 to 2026-05-26) — single bull market regime")
    w("- TIERED_ATR parameters (5%/15% thresholds, 2.0/2.5/3.0 multipliers) are first-pass heuristics")
    w("- Hold protection period = 3 report dates is heuristic; not derived from empirical data")
    w("- post_exit_max_return uses yfinance adjusted close — may differ from TWSE raw close")
    w("- DATA_QUALITY_ISSUE lots (ticker=None) excluded from metric aggregation"); w("")

    w("## Decision Criteria"); w("")
    w("Upgrade TIERED_ATR to candidate default ONLY if all three hold:")
    w("1. total_net_pnl(TIERED_ATR) > total_net_pnl(ATR_BASE)")
    w("2. false_exit_count(TIERED_ATR) < false_exit_count(ATR_BASE)")
    w("3. max_drawdown(TIERED_ATR) ≤ max_drawdown(ATR_BASE) × 1.2 (not more than 20% worse)")
    w("   AND largest_single_lot_loss(TIERED_ATR) ≥ largest_single_lot_loss(ATR_BASE) × 0.8")
    w(""); w("---"); w("")
    w("*This is a simulation. No trades were placed. No broker connections were made.*")
    w("*Owner should review before any capital allocation decisions.*"); w("")
    path.write_text("\n".join(lines), encoding="utf-8")


# ─────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────

def run_tiered_backtest(valuation_date: date, entry_capital: float) -> dict:
    """Run P0.4 tiered ATR exit backtest across all rolling baskets.
    Advisory only — no trades, no broker.
    """
    _empty = {
        "strategy_id":   TIERED_STRATEGY_ID,
        "valuation_date": valuation_date.isoformat(),
        "n_baskets":     0,
        "lots_by_model": {mn: [] for mn in ALL_MODELS},
        "model_metrics": {mn: {} for mn in ALL_MODELS},
    }

    report_dates  = get_available_report_dates()
    baskets_dates = build_rolling_baskets(report_dates, window=BASKET_WINDOW)
    if not baskets_dates:
        print("[WARN] Fewer than 5 report dates — cannot build any rolling baskets")
        return _empty

    print(f"[p0.4] {len(report_dates)} report dates → {len(baskets_dates)} rolling baskets")

    # Collect all unique tickers across all baskets
    all_tickers: set[str] = set()
    for bd in baskets_dates:
        for d in bd:
            p = parse_daily_report(d.isoformat())
            if p and p.get("ticker"):
                all_tickers.add(p["ticker"])

    if not all_tickers:
        print("[WARN] No tickers found in reports")
        return _empty

    # Single OHLC fetch: 65-day lookback for ATR20 warmup
    earliest = min(bd[0] for bd in baskets_dates)
    ohlc_start = (earliest - timedelta(days=65)).isoformat()
    ohlc_end   = (valuation_date + timedelta(days=1)).isoformat()
    tickers_list = sorted(all_tickers)
    print(f"[p0.4] Fetching OHLC for {tickers_list} ({ohlc_start} → {ohlc_end})")
    ohlc = fetch_ohlc(tickers_list, ohlc_start, ohlc_end)
    if ohlc.empty:
        print("[WARN] OHLC fetch returned empty DataFrame")

    planned_capital = entry_capital * BASKET_WINDOW
    lots_by_model: dict[str, list[dict]] = {mn: [] for mn in ALL_MODELS}

    for bi, basket_dates in enumerate(baskets_dates):
        basket_id   = f"{basket_dates[0].isoformat()}_5D"
        is_immature = flag_immature_basket(basket_dates, report_dates, valuation_date)
        print(f"[p0.4] Basket {bi+1}/{len(baskets_dates)}: {basket_id}"
              f"{' [IMMATURE]' if is_immature else ''}")

        entries = []
        for i, d in enumerate(basket_dates, 1):
            e = build_entry(i, d.isoformat(), ohlc, entry_capital)
            e["strategy_id"] = TIERED_STRATEGY_ID
            e["basket_id"]   = basket_id
            entries.append(e)

        for entry in entries:
            grade = compute_position_grade(
                entry.get("entry_signal", ""),
                entry.get("market_state"),
                entry.get("_role_confidence"),
            )

            for model_name in ALL_MODELS:
                ei  = _run_one_model(model_name, entry, ohlc, report_dates, valuation_date)
                pnl = compute_pnl(
                    entry.get("actual_cost") or 0, entry.get("shares") or 0,
                    ei.get("exit_price"), ei.get("exit_reason", "DATA_INCOMPLETE"),
                    valuation_date, ei.get("current_price"),
                )
                lot = assemble_lot(entry, ei, grade, pnl)
                lot["model_name"]            = model_name
                lot["basket_id"]             = basket_id
                lot["is_immature"]           = is_immature
                lot["hold_period_protected"] = ei.get("hold_period_protected", False)

                # Enrich with post-exit max return for false_exit detection
                exit_date_obj = (date.fromisoformat(ei["exit_date"])
                                 if ei.get("exit_date") else None)
                post_exit = compute_post_exit_max_return(
                    entry.get("ticker", ""), exit_date_obj, valuation_date,
                    ei.get("exit_price") or 0, ohlc,
                )
                lot["post_exit_max_return"] = post_exit["post_exit_max_return"]
                lot["profit_giveback_pct"]  = compute_profit_giveback_pct(lot)

                lots_by_model[model_name].append(lot)

    model_metrics = aggregate_model_metrics(lots_by_model)

    return {
        "strategy_id":    TIERED_STRATEGY_ID,
        "valuation_date": valuation_date.isoformat(),
        "entry_capital":  entry_capital,
        "planned_capital": planned_capital,
        "n_baskets":      len(baskets_dates),
        "lots_by_model":  lots_by_model,
        "model_metrics":  model_metrics,
    }


# ─────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Investment OS — P0.4 Tiered ATR Exit Backtest v0.1"
    )
    parser.add_argument("--valuation-date", default="2026-05-26")
    parser.add_argument("--entry-capital", type=float, default=100_000.0)
    args = parser.parse_args()

    val_date = date.fromisoformat(args.valuation_date)
    print(f"[p0.4] {TIERED_STRATEGY_ID}")
    print(f"[p0.4] valuation={val_date}  capital/lot={args.entry_capital:,.0f}")

    result = run_tiered_backtest(val_date, args.entry_capital)

    if not any(result["lots_by_model"].values()):
        print("[ERROR] No lots produced — check that reports/daily/ contains report files")
        return 1

    lots_csv      = DATA_BACKTEST      / "tiered_atr_exit_backtest_lots.csv"
    comp_csv      = DATA_BACKTEST      / "tiered_atr_exit_backtest_comparison.csv"
    summary_json  = DATA_BACKTEST      / "tiered_atr_exit_backtest_summary.json"
    report_md     = REPORTS_BACKTEST   / "tiered_atr_exit_backtest_v0_1.md"
    validation_md = REPORTS_VALIDATION / "tiered_atr_exit_backtest_validation.md"

    write_lots_csv(result["lots_by_model"], lots_csv)
    write_comparison_csv(result["model_metrics"], comp_csv)
    write_summary_json(result, summary_json)
    write_comparison_report_md(result, report_md)
    write_validation_report_md(result, validation_md)

    print(f"\n[p0.4] Artifacts written:")
    for p in [lots_csv, comp_csv, summary_json, report_md, validation_md]:
        print(f"  {p}")

    mm = result["model_metrics"]
    print("\n[p0.4] Comparison summary:")
    for mn in ALL_MODELS:
        m = mm.get(mn, {})
        print(f"  {mn:<38} net={m.get('total_net_pnl', 0):>10,.0f}  "
              f"false_exit={m.get('false_exit_count', 0)}  "
              f"protected={m.get('protected_by_hold_period_count', 0)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
