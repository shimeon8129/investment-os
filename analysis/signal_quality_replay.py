#!/usr/bin/env python3
"""
Investment OS — Signal Quality Replay v0.1

Usage:
    python3 analysis/signal_quality_replay.py --days 10

Reads:  reports/daily/, docs/P1_ENTRY_AUDIT_*.md,
        docs/DAILY_DECISION_DASHBOARD_*.md,
        data/processed/p1_audit_report.json,
        data/processed/mainline_snapshot.json
Writes: reports/validation/YYYY-MM-DD_signal_quality_replay.md
        data/validation/YYYY-MM-DD_signal_quality_replay.json

Analysis only. No trading logic, pipeline, or holdings are modified.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
import yfinance as yf

from utils.market_calendar import is_market_open

# ──────────────────────────────────────────────────────────────
# Calendar helpers
# ──────────────────────────────────────────────────────────────

def get_trading_days(n: int, market: str = "TW", anchor: Optional[date] = None) -> list[str]:
    if anchor is None:
        anchor = date.today()
    days: list[str] = []
    d = anchor - timedelta(days=1)
    for _ in range(n * 10):
        if len(days) >= n:
            break
        if is_market_open(market, d) in ("OPEN", "OPEN_EARLY_CLOSE"):
            days.append(d.isoformat())
        d -= timedelta(days=1)
    return days  # newest first


def nth_trading_day_after(base: str, n: int, market: str = "TW") -> Optional[str]:
    d = date.fromisoformat(base) + timedelta(days=1)
    count = 0
    for _ in range(60):
        if is_market_open(market, d) in ("OPEN", "OPEN_EARLY_CLOSE"):
            count += 1
            if count == n:
                return d.isoformat()
        d += timedelta(days=1)
    return None


# ──────────────────────────────────────────────────────────────
# Data loading from historical files
# ──────────────────────────────────────────────────────────────

_LOCK_EMOJI = {"⚠️": "WARN", "✅": "PASS", "🚫": "BLOCK"}


def _emoji_to_status(cell: str) -> Optional[str]:
    cell = cell.strip()
    for em, status in _LOCK_EMOJI.items():
        if em in cell:
            return status
    return None


def load_from_p1_audit_json(date_str: str) -> Optional[dict]:
    """Load ranking + L0-L4 from p1_audit_report.json (only for the date it was generated)."""
    audit_path = ROOT / "data/processed/p1_audit_report.json"
    snap_path = ROOT / "data/processed/mainline_snapshot.json"
    if not audit_path.exists() or not snap_path.exists():
        return None

    with open(audit_path, encoding="utf-8") as f:
        audit = json.load(f)
    if not audit.get("generated_at", "").startswith(date_str):
        return None

    with open(snap_path, encoding="utf-8") as f:
        snap = json.load(f)

    ranked_list = snap.get("ranked", [])
    rank_map = {r["ticker"]: (i + 1, r.get("score")) for i, r in enumerate(ranked_list)}

    candidates = []
    for entry in audit.get("audit_entries", []):
        ticker = entry["ticker"]
        lock = entry.get("entry_lock", {})
        locks = lock.get("locks", {})

        def lstat(key):
            v = locks.get(key, {})
            return v.get("status")

        def warn_reason():
            for v in locks.values():
                if v.get("status") == "WARN":
                    return v.get("reason")
            return None

        rank, score = rank_map.get(ticker, (None, None))
        candidates.append({
            "ticker": ticker,
            "name": entry.get("name", ticker),
            "rank": rank,
            "score": score,
            "signal": entry.get("signal"),
            "p1_result": entry.get("p1_audit_action"),
            "L0": lstat("L0_market"),
            "L1": lstat("L1_selection"),
            "L2": lstat("L2_setup"),
            "L3": lstat("L3_validation"),
            "L4": lstat("L4_risk"),
            "block_reason": lock.get("blocked_by", [None])[0] if lock.get("blocked_by") else None,
            "warn_reason": warn_reason(),
        })

    candidates.sort(key=lambda x: (x["rank"] or 999))
    return {
        "date": date_str,
        "source": "p1_audit_report.json + mainline_snapshot.json",
        "market_state": audit.get("market_state"),
        "market_score": snap.get("market_score"),
        "vix": audit.get("vix_value"),
        "candidates": candidates,
        "limitation": None,
    }


def _parse_p1_audit_md(md_path: Path, date_str: str) -> Optional[dict]:
    """Parse docs/P1_ENTRY_AUDIT_YYYYMMDD.md for L0-L4 per ticker."""
    if not md_path.exists():
        return None
    text = md_path.read_text(encoding="utf-8")

    market_state = None
    vix = None
    m = re.search(r"\*\*(\w+)\*\*\s*\|\s*([\d.]+)", text)
    if m:
        market_state = m.group(1)
        try:
            vix = float(m.group(2))
        except ValueError:
            pass

    lock_map: dict[str, dict] = {}
    for line in text.splitlines():
        if "|" not in line:
            continue
        cols = [c.strip() for c in line.split("|")]
        cols = [c for c in cols if c]
        if len(cols) < 11:
            continue
        # Expected: # | ticker | name | signal | level | L0 | L1 | L2 | L3 | L4 | status | p1_action
        try:
            int(cols[0])
        except ValueError:
            continue
        ticker = cols[1]
        l0 = _emoji_to_status(cols[5])
        l1 = _emoji_to_status(cols[6])
        l2 = _emoji_to_status(cols[7])
        l3 = _emoji_to_status(cols[8])
        l4 = _emoji_to_status(cols[9])
        p1_raw = cols[11] if len(cols) > 11 else ""
        if "ENTRY_REDUCED" in p1_raw:
            p1 = "ENTRY_REDUCED"
        elif "ENTRY" in p1_raw:
            p1 = "ENTRY"
        elif "WAIT" in p1_raw:
            p1 = "WAIT"
        else:
            p1 = None
        lock_map[ticker] = {
            "L0": l0, "L1": l1, "L2": l2, "L3": l3, "L4": l4,
            "p1_result": p1,
        }
    return {
        "market_state": market_state,
        "vix": vix,
        "lock_map": lock_map,
    }


def _parse_daily_report_top5(date_str: str) -> Optional[dict]:
    """Parse reports/daily/YYYY-MM-DD_daily_report.md for top 5 ranked candidates."""
    path = ROOT / "reports" / "daily" / f"{date_str}_daily_report.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")

    market_state = None
    market_score = None
    vix = None
    ms_m = re.search(r"Market state:\s*\*\*(\w+)\*\*\s*\|\s*Score:\s*([\d.]+)\s*\|\s*VIX:\s*([\d.]+)", text)
    if ms_m:
        market_state = ms_m.group(1)
        market_score = float(ms_m.group(2))
        vix = float(ms_m.group(3))

    candidates = []
    in_table = False
    for line in text.splitlines():
        if "| Rank |" in line and "Ticker" in line:
            in_table = True
            continue
        if in_table:
            if not line.strip().startswith("|"):
                in_table = False
                continue
            cols = [c.strip() for c in line.split("|")]
            cols = [c for c in cols if c]
            if len(cols) < 5 or cols[0] == "---":
                continue
            try:
                rank = int(cols[0])
            except ValueError:
                continue
            ticker = cols[1]
            name = cols[2]
            score = None
            try:
                score = float(cols[5])
            except (ValueError, IndexError):
                pass
            signal = cols[4] if len(cols) > 4 else None
            candidates.append({
                "ticker": ticker, "name": name, "rank": rank,
                "score": score, "signal": signal,
                "p1_result": None, "L0": None, "L1": None,
                "L2": None, "L3": None, "L4": None,
                "block_reason": None, "warn_reason": None,
            })

    if not candidates:
        return None
    return {
        "market_state": market_state,
        "market_score": market_score,
        "vix": vix,
        "candidates": candidates,
    }


def _parse_dashboard_top10(date_str: str) -> Optional[list[dict]]:
    """Parse docs/DAILY_DECISION_DASHBOARD_YYYYMMDD.md for Top 10."""
    fname = date_str.replace("-", "")
    path = ROOT / "docs" / f"DAILY_DECISION_DASHBOARD_{fname}.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")

    # Try the enhanced format (has "綜合分數" column)
    enhanced = "綜合分數" in text
    candidates = []

    if enhanced:
        in_table = False
        for line in text.splitlines():
            if "| Rank |" in line and "Ticker" in line:
                in_table = True
                continue
            if in_table:
                if not line.strip().startswith("|"):
                    in_table = False
                    continue
                cols = [c.strip() for c in line.split("|")]
                cols = [c for c in cols if c]
                if len(cols) < 5 or "---" in cols[0]:
                    continue
                try:
                    rank = int(cols[0])
                except ValueError:
                    continue
                ticker = cols[1]
                name = cols[2]
                signal = cols[4] if len(cols) > 4 else None
                score_raw = cols[5] if len(cols) > 5 else ""
                score = None
                try:
                    score = float(re.sub(r"[*\s]", "", score_raw))
                except ValueError:
                    pass
                candidates.append({
                    "ticker": ticker, "name": name, "rank": rank,
                    "score": score, "signal": signal,
                    "p1_result": None, "L0": None, "L1": None,
                    "L2": None, "L3": None, "L4": None,
                    "block_reason": None, "warn_reason": None,
                })
    else:
        # v0 format: rank | ticker | name | asset_type | close | scanner_score | signal ...
        in_table = False
        for line in text.splitlines():
            if "| rank |" in line.lower() and "ticker" in line.lower():
                in_table = True
                continue
            if in_table:
                if not line.strip().startswith("|"):
                    in_table = False
                    continue
                cols = [c.strip() for c in line.split("|")]
                cols = [c for c in cols if c]
                if len(cols) < 4 or "---" in cols[0]:
                    continue
                try:
                    rank = int(cols[0])
                except ValueError:
                    continue
                raw_ticker = cols[1]
                ticker = raw_ticker if "." in raw_ticker else f"{raw_ticker}.TW"
                name = cols[2]
                close = None
                signal = None
                try:
                    close = float(cols[4])
                    signal = cols[6] if len(cols) > 6 else None
                except (ValueError, IndexError):
                    pass
                candidates.append({
                    "ticker": ticker, "name": name, "rank": rank,
                    "score": close,  # only close available in v0
                    "signal": signal,
                    "p1_result": None, "L0": None, "L1": None,
                    "L2": None, "L3": None, "L4": None,
                    "block_reason": None, "warn_reason": None,
                })

    return candidates or None


def load_date_data(date_str: str) -> dict:
    """Load best available ranking data for a given date."""

    # 1. Try p1_audit_report.json (most complete, only available for latest date)
    result = load_from_p1_audit_json(date_str)
    if result:
        return result

    # 2. Try combining P1 audit MD + daily report
    fname = date_str.replace("-", "")
    audit_md_path = ROOT / "docs" / f"P1_ENTRY_AUDIT_{fname}.md"
    audit_parsed = _parse_p1_audit_md(audit_md_path, date_str)
    report_data = _parse_daily_report_top5(date_str)
    dashboard_top10 = _parse_dashboard_top10(date_str)

    if report_data or audit_parsed or dashboard_top10:
        candidates = []
        seen_tickers: set[str] = set()

        # Start with daily report top 5 (most reliable mainline scores)
        if report_data:
            for c in report_data["candidates"]:
                if c["ticker"] not in seen_tickers:
                    seen_tickers.add(c["ticker"])
                    candidates.append(c)

        # Add tickers from dashboard not already in list
        if dashboard_top10:
            for c in dashboard_top10:
                if c["ticker"] not in seen_tickers:
                    c = dict(c)
                    if report_data and len(candidates) < 10:
                        c["rank"] = len(candidates) + 1
                    seen_tickers.add(c["ticker"])
                    candidates.append(c)

        # Apply L0-L4 from audit MD
        if audit_parsed:
            for c in candidates:
                if c["ticker"] in audit_parsed["lock_map"]:
                    ldata = audit_parsed["lock_map"][c["ticker"]]
                    c.update({k: v for k, v in ldata.items() if v is not None})

        market_state = (audit_parsed or {}).get("market_state") or (report_data or {}).get("market_state")
        vix = (audit_parsed or {}).get("vix") or (report_data or {}).get("vix")
        market_score = (report_data or {}).get("market_score")

        sources = []
        if report_data:
            sources.append("daily_report")
        if audit_md_path.exists():
            sources.append("P1_ENTRY_AUDIT_md")
        if dashboard_top10:
            sources.append("DAILY_DECISION_DASHBOARD")

        return {
            "date": date_str,
            "source": " + ".join(sources),
            "market_state": market_state,
            "market_score": market_score,
            "vix": vix,
            "candidates": candidates[:10],
            "limitation": "L0-L4 partial or missing; scores from daily report only (top 5 authoritative)" if not audit_md_path.exists() else None,
        }

    return {
        "date": date_str,
        "source": "NONE",
        "market_state": None,
        "market_score": None,
        "vix": None,
        "candidates": [],
        "limitation": "No point-in-time data available for this date. Exact replay not supported.",
    }


# ──────────────────────────────────────────────────────────────
# Price fetching and forward return calculation
# ──────────────────────────────────────────────────────────────

def fetch_prices(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Fetch adjusted close prices for tickers between start and end dates."""
    if not tickers:
        return pd.DataFrame()
    try:
        raw = yf.download(
            tickers,
            start=start,
            end=end,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        if raw.empty:
            return pd.DataFrame()
        if isinstance(raw.columns, pd.MultiIndex):
            close = raw["Close"]
        else:
            close = raw[["Close"]] if "Close" in raw.columns else raw
        close.index = pd.to_datetime(close.index).date
        return close
    except Exception as e:
        print(f"[WARN] Price fetch failed: {e}")
        return pd.DataFrame()


def calc_forward_returns(
    ticker: str,
    signal_date: str,
    prices: pd.DataFrame,
    trading_days: list[str],
) -> dict:
    today_str = date.today().isoformat()

    def get_close(date_str: str) -> Optional[float]:
        d = date.fromisoformat(date_str)
        if ticker not in prices.columns:
            return None
        if d not in prices.index:
            return None
        val = prices.loc[d, ticker]
        if pd.isna(val):
            return None
        return float(val)

    base = get_close(signal_date)
    if base is None:
        return {"next_1d_return": None, "next_3d_return": None, "next_5d_return": None,
                "max_5d_runup": None, "max_5d_drawdown": None, "base_price": None,
                "note": "no base price"}

    def fwd_return(n: int) -> Optional[float]:
        fwd_date = nth_trading_day_after(signal_date, n)
        if fwd_date is None:
            return None
        if fwd_date > today_str:
            return None  # future
        p = get_close(fwd_date)
        if p is None:
            return None
        return round((p - base) / base, 4)

    # Collect 5 forward trading days' prices
    fwd_dates = []
    d = date.fromisoformat(signal_date) + timedelta(days=1)
    count = 0
    while count < 5:
        d_str = d.isoformat()
        if is_market_open("TW", d) in ("OPEN", "OPEN_EARLY_CLOSE"):
            fwd_dates.append(d_str)
            count += 1
        d += timedelta(days=1)
        if d > date.today() + timedelta(days=30):
            break

    fwd_prices = []
    for fd in fwd_dates:
        if fd > today_str:
            break
        p = get_close(fd)
        if p is not None:
            fwd_prices.append((p - base) / base)

    max_runup = round(max(fwd_prices), 4) if fwd_prices else None
    max_drawdown = round(min(fwd_prices), 4) if fwd_prices else None

    return {
        "base_price": round(base, 2),
        "next_1d_return": fwd_return(1),
        "next_3d_return": fwd_return(3),
        "next_5d_return": fwd_return(5),
        "max_5d_runup": max_runup,
        "max_5d_drawdown": max_drawdown,
        "note": f"fwd_days_available={len(fwd_prices)}/5",
    }


# ──────────────────────────────────────────────────────────────
# Analysis helpers
# ──────────────────────────────────────────────────────────────

def _avg(values: list) -> Optional[float]:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return round(sum(vals) / len(vals), 4)


def _pct_str(v: Optional[float]) -> str:
    if v is None:
        return "N/A"
    return f"{v*100:+.2f}%"


# ──────────────────────────────────────────────────────────────
# Main replay logic
# ──────────────────────────────────────────────────────────────

def run_replay(n_days: int) -> dict:
    print(f"[signal_quality_replay] Loading last {n_days} valid TW trading days...")
    trading_days = get_trading_days(n_days)
    print(f"[signal_quality_replay] Days: {trading_days}")

    # Load per-date ranking data
    date_records: list[dict] = []
    for d in trading_days:
        rec = load_date_data(d)
        n_cands = len(rec["candidates"])
        print(f"  {d}: source={rec['source']}, candidates={n_cands}, market={rec['market_state']}")
        date_records.append(rec)

    # Collect all unique tickers across all dates
    all_tickers: set[str] = set()
    for rec in date_records:
        for c in rec["candidates"]:
            all_tickers.add(c["ticker"])

    # Price range: earliest signal date - 2d to today + 14d (for forward returns)
    earliest = min(trading_days)
    price_start = (date.fromisoformat(earliest) - timedelta(days=5)).isoformat()
    price_end = (date.today() + timedelta(days=14)).isoformat()

    print(f"[signal_quality_replay] Fetching prices {price_start}→{price_end} for {len(all_tickers)} tickers...")
    prices = fetch_prices(sorted(all_tickers), price_start, price_end)
    print(f"[signal_quality_replay] Price data shape: {prices.shape}")

    # Compute per-candidate forward returns
    candidates_with_returns: list[dict] = []
    for rec in date_records:
        for c in rec["candidates"]:
            fwd = calc_forward_returns(c["ticker"], rec["date"], prices, trading_days)
            cand = {**c, **fwd, "signal_date": rec["date"],
                    "market_state": rec["market_state"], "market_score": rec.get("market_score"),
                    "vix": rec.get("vix")}
            candidates_with_returns.append(cand)

    # Per-date stats
    date_stats: list[dict] = []
    for rec in date_records:
        date_cands = [c for c in candidates_with_returns if c["signal_date"] == rec["date"]]
        stats = _compute_date_stats(date_cands, rec)
        date_stats.append(stats)

    # Aggregate stats across all dates (only where data is available)
    agg = _compute_aggregate_stats(candidates_with_returns)

    # False negatives / positives
    false_neg = _find_false_negatives(candidates_with_returns)
    false_pos = _find_false_positives(candidates_with_returns)

    # Verdict
    verdict, verdict_reason = _compute_verdict(agg, false_neg, false_pos, days_with_data=sum(1 for r in date_records if r["source"] != "NONE"))

    return {
        "run_date": date.today().isoformat(),
        "days_requested": n_days,
        "days_with_data": sum(1 for r in date_records if r["source"] != "NONE"),
        "days_no_data": sum(1 for r in date_records if r["source"] == "NONE"),
        "trading_days": trading_days,
        "limitations": [
            r["limitation"] for r in date_records if r.get("limitation")
        ],
        "date_records": [
            {k: v for k, v in r.items() if k != "candidates"} for r in date_records
        ],
        "candidates_with_returns": candidates_with_returns,
        "date_stats": date_stats,
        "aggregate": agg,
        "false_negatives": false_neg,
        "false_positives": false_pos,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
    }


def _compute_date_stats(cands: list[dict], rec: dict) -> dict:
    top3 = [c for c in cands if c.get("rank") and c["rank"] <= 3]
    top5 = [c for c in cands if c.get("rank") and c["rank"] <= 5]
    top10 = cands  # all candidates = top 10 for dates with data

    univ_1d = _avg([c["next_1d_return"] for c in cands])
    univ_3d = _avg([c["next_3d_return"] for c in cands])

    return {
        "date": rec["date"],
        "source": rec["source"],
        "market_state": rec["market_state"],
        "vix": rec.get("vix"),
        "candidate_count": len(cands),
        "universe_avg_1d": univ_1d,
        "universe_avg_3d": univ_3d,
        "top3_avg_1d": _avg([c["next_1d_return"] for c in top3]),
        "top3_avg_3d": _avg([c["next_3d_return"] for c in top3]),
        "top5_avg_1d": _avg([c["next_1d_return"] for c in top5]),
        "top5_avg_3d": _avg([c["next_3d_return"] for c in top5]),
        "top10_avg_1d": _avg([c["next_1d_return"] for c in top10]),
        "top10_avg_3d": _avg([c["next_3d_return"] for c in top10]),
        "pass_entry_avg_1d": _avg([c["next_1d_return"] for c in cands
                                    if c.get("p1_result") in ("ENTRY", "ENTRY_REDUCED")]),
        "wait_avg_1d": _avg([c["next_1d_return"] for c in cands
                              if c.get("p1_result") == "WAIT"]),
    }


def _compute_aggregate_stats(cands: list[dict]) -> dict:
    def group_returns(filter_fn, key="next_1d_return"):
        return _avg([c[key] for c in cands if filter_fn(c)])

    top3 = lambda c: c.get("rank") and c["rank"] <= 3
    top5 = lambda c: c.get("rank") and c["rank"] <= 5
    top10 = lambda c: True  # all candidates
    pass_entry = lambda c: c.get("p1_result") in ("ENTRY", "ENTRY_REDUCED")
    wait = lambda c: c.get("p1_result") == "WAIT"
    blocked_l2 = lambda c: c.get("L2") == "BLOCK"
    blocked_l3 = lambda c: c.get("L3") == "BLOCK"

    return {
        "total_candidates": len(cands),
        "top3_avg_1d": group_returns(top3, "next_1d_return"),
        "top5_avg_1d": group_returns(top5, "next_1d_return"),
        "top10_avg_1d": group_returns(top10, "next_1d_return"),
        "universe_avg_1d": group_returns(lambda c: True, "next_1d_return"),
        "top3_avg_3d": group_returns(top3, "next_3d_return"),
        "top5_avg_3d": group_returns(top5, "next_3d_return"),
        "top10_avg_3d": group_returns(top10, "next_3d_return"),
        "universe_avg_3d": group_returns(lambda c: True, "next_3d_return"),
        "pass_entry_avg_1d": group_returns(pass_entry, "next_1d_return"),
        "wait_avg_1d": group_returns(wait, "next_1d_return"),
        "pass_entry_avg_3d": group_returns(pass_entry, "next_3d_return"),
        "wait_avg_3d": group_returns(wait, "next_3d_return"),
        "blocked_l2_avg_1d": group_returns(blocked_l2, "next_1d_return"),
        "blocked_l3_avg_1d": group_returns(blocked_l3, "next_1d_return"),
        "data_coverage_1d": sum(1 for c in cands if c.get("next_1d_return") is not None),
        "data_coverage_3d": sum(1 for c in cands if c.get("next_3d_return") is not None),
        "data_coverage_5d": sum(1 for c in cands if c.get("next_5d_return") is not None),
    }


def _find_false_negatives(cands: list[dict]) -> list[dict]:
    """WAIT/BLOCK but +3% within 3D or +5% within 5D."""
    result = []
    for c in cands:
        if c.get("p1_result") != "WAIT":
            continue
        r3d = c.get("next_3d_return")
        r5d = c.get("next_5d_return")
        if (r3d is not None and r3d >= 0.03) or (r5d is not None and r5d >= 0.05):
            result.append({
                "ticker": c["ticker"], "name": c.get("name"),
                "signal_date": c["signal_date"],
                "rank": c.get("rank"), "p1_result": c.get("p1_result"),
                "block_reason": c.get("block_reason"),
                "L0": c.get("L0"), "L1": c.get("L1"), "L2": c.get("L2"),
                "L3": c.get("L3"), "L4": c.get("L4"),
                "next_3d_return": r3d, "next_5d_return": r5d,
            })
    return result


def _find_false_positives(cands: list[dict]) -> list[dict]:
    """PASS/ENTRY but -3% within 3D or -5% within 5D."""
    result = []
    for c in cands:
        if c.get("p1_result") not in ("ENTRY", "ENTRY_REDUCED"):
            continue
        r3d = c.get("next_3d_return")
        r5d = c.get("next_5d_return")
        if (r3d is not None and r3d <= -0.03) or (r5d is not None and r5d <= -0.05):
            result.append({
                "ticker": c["ticker"], "name": c.get("name"),
                "signal_date": c["signal_date"],
                "rank": c.get("rank"), "p1_result": c.get("p1_result"),
                "next_3d_return": r3d, "next_5d_return": r5d,
            })
    return result


def _compute_verdict(agg: dict, false_neg: list, false_pos: list, days_with_data: int = 0) -> tuple[str, str]:
    coverage_1d = agg.get("data_coverage_1d", 0)
    coverage_3d = agg.get("data_coverage_3d", 0)
    total = agg.get("total_candidates", 1) or 1

    if coverage_1d == 0:
        return "WARN", "No forward return data available yet — replay is incomplete. Expand window only after next trading week."

    if days_with_data < 5:
        return "WARN", (
            f"樣本不足：僅 {days_with_data} 個交易日有 point-in-time 資料（目標 10 個，最低門檻 5 個）。"
            " 請先建立更完整的歷史 snapshot，再下最終判定。"
            f" 初步觀察：Top3 1D均 {_fmt_pct(agg.get('top3_avg_1d'))} vs Universe {_fmt_pct(agg.get('universe_avg_1d'))}。"
        )

    top3_1d = agg.get("top3_avg_1d")
    univ_1d = agg.get("universe_avg_1d")
    top5_3d = agg.get("top5_avg_3d")
    univ_3d = agg.get("universe_avg_3d")

    warnings: list[str] = []
    positives: list[str] = []

    # Top 3 vs universe 1d
    if top3_1d is not None and univ_1d is not None:
        if top3_1d > univ_1d + 0.005:
            positives.append(f"Top3 1d avg {_pct_str(top3_1d)} > universe {_pct_str(univ_1d)}")
        elif top3_1d < univ_1d - 0.005:
            warnings.append(f"Top3 1d avg {_pct_str(top3_1d)} < universe {_pct_str(univ_1d)}")

    # Top 5 vs universe 3d
    if top5_3d is not None and univ_3d is not None:
        if top5_3d > univ_3d + 0.005:
            positives.append(f"Top5 3d avg {_pct_str(top5_3d)} > universe {_pct_str(univ_3d)}")
        elif top5_3d < univ_3d - 0.005:
            warnings.append(f"Top5 3d avg {_pct_str(top5_3d)} < universe {_pct_str(univ_3d)}")

    # False negative rate
    fn_rate = len(false_neg) / max(
        sum(1 for _ in [1]), 1)  # just count FNs as severity indicator
    if len(false_neg) >= 3:
        warnings.append(f"False negatives: {len(false_neg)} (WAIT/BLOCK candidates that moved +3%+ in 3D)")

    if not warnings and positives:
        return "PASS", "Top ranks outperform universe; EntryLock not excessively conservative. " + "; ".join(positives)
    elif len(warnings) >= 2:
        return "FAIL", "Multiple negative signals: " + "; ".join(warnings)
    elif warnings:
        return "WARN", "Mixed signals: " + "; ".join(warnings + positives) if positives else warnings[0]
    else:
        return "WARN", f"Insufficient data coverage (1d={coverage_1d}/{total}). Revisit after more trading days."


# ──────────────────────────────────────────────────────────────
# Report generation
# ──────────────────────────────────────────────────────────────

def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "N/A"
    return f"{v*100:+.2f}%"


def generate_report(result: dict) -> str:
    today = result["run_date"]
    verdict = result["verdict"]
    agg = result["aggregate"]
    lines: list[str] = []

    def w(*args):
        lines.append(" ".join(str(a) for a in args) if args else "")

    w(f"# Signal Quality Replay — {today}")
    w()
    w(f"**Verdict: {verdict}**")
    w()
    w(f"> {result['verdict_reason']}")
    w()

    # Coverage summary
    w("## 資料覆蓋")
    w()
    w(f"- 請求交易日數：{result['days_requested']}")
    w(f"- 有資料日數：{result['days_with_data']}")
    w(f"- 無資料日數（缺少 point-in-time snapshot）：{result['days_no_data']}")
    w(f"- 候選標的總數（跨日累計）：{agg['total_candidates']}")
    w(f"- 1D 報酬資料覆蓋：{agg['data_coverage_1d']}/{agg['total_candidates']}")
    w(f"- 3D 報酬資料覆蓋：{agg['data_coverage_3d']}/{agg['total_candidates']}")
    w(f"- 5D 報酬資料覆蓋：{agg['data_coverage_5d']}/{agg['total_candidates']}")
    w()

    # Limitations
    unique_limits = list(dict.fromkeys(result["limitations"]))
    if unique_limits:
        w("### 限制聲明")
        w()
        for lim in unique_limits:
            w(f"- {lim}")
        w()

    # Date-by-date
    w("## 逐日資料來源")
    w()
    w("| 日期 | 資料來源 | 市場狀態 | VIX | 候選數 | Universe 1D均 | Top3 1D均 |")
    w("| --- | --- | --- | --- | --- | --- | --- |")
    for ds in result["date_stats"]:
        w(f"| {ds['date']} | {ds['source']} | {ds['market_state'] or 'N/A'} | "
          f"{ds.get('vix', 'N/A')} | {ds['candidate_count']} | "
          f"{_fmt_pct(ds['universe_avg_1d'])} | {_fmt_pct(ds['top3_avg_1d'])} |")
    w()

    # Aggregate comparison table
    w("## 排名分組 vs 全宇宙比較")
    w()
    w("| 分組 | 1D 均報酬 | 3D 均報酬 |")
    w("| --- | --- | --- |")
    w(f"| 全宇宙 (Universe) | {_fmt_pct(agg['universe_avg_1d'])} | {_fmt_pct(agg['universe_avg_3d'])} |")
    w(f"| Top 3 | {_fmt_pct(agg['top3_avg_1d'])} | {_fmt_pct(agg['top3_avg_3d'])} |")
    w(f"| Top 5 | {_fmt_pct(agg['top5_avg_1d'])} | {_fmt_pct(agg['top5_avg_3d'])} |")
    w(f"| Top 10 | {_fmt_pct(agg['top10_avg_1d'])} | {_fmt_pct(agg['top10_avg_3d'])} |")
    w()

    w("## EntryLock 分組報酬")
    w()
    w("| P1 結果 | 1D 均報酬 | 3D 均報酬 |")
    w("| --- | --- | --- |")
    w(f"| ENTRY / ENTRY_REDUCED | {_fmt_pct(agg['pass_entry_avg_1d'])} | {_fmt_pct(agg['pass_entry_avg_3d'])} |")
    w(f"| WAIT | {_fmt_pct(agg['wait_avg_1d'])} | {_fmt_pct(agg['wait_avg_3d'])} |")
    w()

    w("## Lock Layer 封鎖分組")
    w()
    w("| 封鎖層 | 1D 均報酬（被封鎖者） |")
    w("| --- | --- |")
    w(f"| L2 BLOCK | {_fmt_pct(agg['blocked_l2_avg_1d'])} |")
    w(f"| L3 BLOCK | {_fmt_pct(agg['blocked_l3_avg_1d'])} |")
    w()

    # Candidate-level detail (for dates with data)
    w("## 候選標的明細（有資料日）")
    w()
    w("| 日期 | Rank | Ticker | 名稱 | 分數 | P1 | L0 | L2 | L3 | 1D | 3D | 5D |")
    w("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for c in result["candidates_with_returns"]:
        if not c.get("rank"):
            continue
        w(f"| {c['signal_date']} | {c['rank']} | {c['ticker']} | {c.get('name','')} | "
          f"{c.get('score', 'N/A')} | {c.get('p1_result', 'N/A')} | "
          f"{c.get('L0', 'N/A')} | {c.get('L2', 'N/A')} | {c.get('L3', 'N/A')} | "
          f"{_fmt_pct(c.get('next_1d_return'))} | "
          f"{_fmt_pct(c.get('next_3d_return'))} | "
          f"{_fmt_pct(c.get('next_5d_return'))} |")
    w()

    # False negatives
    w("## False Negatives（WAIT/BLOCK 但後來大漲）")
    w()
    if result["false_negatives"]:
        w("| 日期 | Ticker | 名稱 | Rank | P1 | 封鎖原因 | 3D | 5D |")
        w("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for fn in result["false_negatives"]:
            w(f"| {fn['signal_date']} | {fn['ticker']} | {fn.get('name','')} | "
              f"{fn.get('rank','N/A')} | {fn.get('p1_result','N/A')} | "
              f"{fn.get('block_reason') or fn.get('L2') or fn.get('L3') or 'N/A'} | "
              f"{_fmt_pct(fn.get('next_3d_return'))} | {_fmt_pct(fn.get('next_5d_return'))} |")
    else:
        w("（無）— 所有明確 WAIT 的標的均未超過 +3% (3D) / +5% (5D) 閾值")
    w()

    # Universe movers without P1 coverage
    universe_movers = [
        c for c in result["candidates_with_returns"]
        if c.get("p1_result") is None
        and c.get("rank")
        and ((c.get("next_3d_return") or 0) >= 0.05 or (c.get("next_5d_return") or 0) >= 0.05)
    ]
    if universe_movers:
        w("### 備注：無 P1 資料但 3D/5D 表現 ≥+5% 的候選（僅供參考）")
        w()
        w("| 日期 | Ticker | 名稱 | Rank | 3D | 5D |")
        w("| --- | --- | --- | --- | --- | --- |")
        for m in universe_movers:
            w(f"| {m['signal_date']} | {m['ticker']} | {m.get('name','')} | "
              f"{m.get('rank','N/A')} | "
              f"{_fmt_pct(m.get('next_3d_return'))} | {_fmt_pct(m.get('next_5d_return'))} |")
        w()

    # False positives
    w("## False Positives（ENTRY 但後來下跌）")
    w()
    if result["false_positives"]:
        w("| 日期 | Ticker | 名稱 | Rank | P1 | 3D | 5D |")
        w("| --- | --- | --- | --- | --- | --- | --- |")
        for fp in result["false_positives"]:
            w(f"| {fp['signal_date']} | {fp['ticker']} | {fp.get('name','')} | "
              f"{fp.get('rank','N/A')} | {fp.get('p1_result','N/A')} | "
              f"{_fmt_pct(fp.get('next_3d_return'))} | {_fmt_pct(fp.get('next_5d_return'))} |")
    else:
        w("（無）— 所有 ENTRY/ENTRY_REDUCED 標的均未跌超 -3% (3D) / -5% (5D) 閾值")
    w()

    # Questions answered
    w("## 任務問題回答")
    w()

    top3_vs_univ_1d = agg.get("top3_avg_1d")
    univ_1d = agg.get("universe_avg_1d")
    if top3_vs_univ_1d is not None and univ_1d is not None:
        direction = "優於" if top3_vs_univ_1d > univ_1d else "未優於"
        w(f"**Q1. Top 3/5/10 是否跑贏候選宇宙？**")
        w(f"- Top 3 1D 均: {_fmt_pct(top3_vs_univ_1d)} vs Universe {_fmt_pct(univ_1d)} → {direction}")
        w(f"- Top 5 1D 均: {_fmt_pct(agg.get('top5_avg_1d'))} | Top 10 1D 均: {_fmt_pct(agg.get('top10_avg_1d'))}")
    else:
        w("**Q1. Top 3/5/10 是否跑贏候選宇宙？** → 資料不足，無法評估")
    w()

    pass_1d = agg.get("pass_entry_avg_1d")
    wait_1d = agg.get("wait_avg_1d")
    if pass_1d is not None or wait_1d is not None:
        w("**Q2. WAIT/BLOCK 標籤是否過於保守？**")
        w(f"- ENTRY/ENTRY_REDUCED 1D 均: {_fmt_pct(pass_1d)}")
        w(f"- WAIT 1D 均: {_fmt_pct(wait_1d)}")
        w(f"- False Negatives 數量: {len(result['false_negatives'])}")
    else:
        w("**Q2. WAIT/BLOCK 是否過保守？** → P1 資料不足（僅2026-05-07/08有L0-L4）")
    w()

    l2_1d = agg.get("blocked_l2_avg_1d")
    l3_1d = agg.get("blocked_l3_avg_1d")
    w("**Q3. 哪個封鎖層造成最多錯失機會？**")
    w(f"- L2 封鎖後 1D 均: {_fmt_pct(l2_1d)}")
    w(f"- L3 封鎖後 1D 均: {_fmt_pct(l3_1d)}")
    fn_by_layer: dict[str, int] = {}
    for fn in result["false_negatives"]:
        layer = fn.get("block_reason") or (fn.get("L3") == "BLOCK" and "L3") or (fn.get("L2") == "BLOCK" and "L2") or "unknown"
        fn_by_layer[str(layer)] = fn_by_layer.get(str(layer), 0) + 1
    if fn_by_layer:
        w(f"  False Negative 分布: {fn_by_layer}")
    w()

    w("**Q4. 目前雷達是否能及早捕捉主升段？**")
    max_runup_vals = [c.get("max_5d_runup") for c in result["candidates_with_returns"]
                      if c.get("max_5d_runup") is not None and c.get("rank") and c["rank"] <= 3]
    if max_runup_vals:
        avg_runup = _avg(max_runup_vals)
        w(f"- Top 3 5D 最大漲幅均值: {_fmt_pct(avg_runup)}")
    else:
        w("- 5D 最大漲幅資料不足（需更多前瞻資料）")
    w()

    w("**Q5. 是否應擴展至 20 交易日？**")
    if verdict == "PASS":
        w("→ **建議：擴展至最近 20 個有效交易日**（根據決策規則：PASS → expand）")
    elif verdict == "WARN":
        w("→ **暫緩擴展，先釐清根因**（WARN → review root cause before expansion）")
    else:
        w("→ **停止擴展，重新檢視訊號設計**（FAIL → stop and review signal design）")
    w()

    # Final verdict
    w("---")
    w()
    w(f"## 最終結果")
    w()
    w(f"```")
    w(f"{verdict}")
    w(f"```")
    w()
    w(f"**理由：** {result['verdict_reason']}")
    w()

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=10)
    args = parser.parse_args()

    result = run_replay(args.days)

    today = result["run_date"]
    out_dir_report = ROOT / "reports" / "validation"
    out_dir_data = ROOT / "data" / "validation"
    out_dir_report.mkdir(parents=True, exist_ok=True)
    out_dir_data.mkdir(parents=True, exist_ok=True)

    report_path = out_dir_report / f"{today}_signal_quality_replay.md"
    data_path = out_dir_data / f"{today}_signal_quality_replay.json"

    report_text = generate_report(result)
    report_path.write_text(report_text, encoding="utf-8")
    data_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print(f"[signal_quality_replay] Report: {report_path}")
    print(f"[signal_quality_replay] Data:   {data_path}")
    print(f"[signal_quality_replay] Verdict: {result['verdict']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
