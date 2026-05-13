#!/usr/bin/env python3
"""
Role-Based Signal Replay v0.2
Evaluates signal quality by role (CORE / CORE_ETF / SATELLITE / WAVE_SWING)
using role-appropriate evaluation windows.

Usage:
    python3 analysis/role_based_signal_replay.py --days 20

Reads:
    data/portfolio/role_map.json
    data/validation/2026-05-10_signal_quality_replay.json  (PIT reference)
Writes:
    reports/validation/YYYY-MM-DD_role_based_signal_replay.md
    data/validation/YYYY-MM-DD_role_based_signal_replay.json

Analysis only. No trading logic or holdings modified.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import warnings
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
import yfinance as yf

from analysis.signal_quality_replay import get_trading_days, nth_trading_day_after

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────

RUN_DATE = date.today().isoformat()

# Evaluation windows per active_role (in trading days)
WINDOWS = {
    "CORE":     [10, 20],
    "CORE_ETF": [10, 20],
    "SATELLITE":[5, 10, 20],
    "WAVE_SWING":[3, 5, 10],
}

# Role-aware false-positive thresholds (N-day return below threshold = FP candidate)
FP_THRESHOLDS = {
    "CORE":      {"window": 20, "threshold": -0.05},
    "CORE_ETF":  {"window": 20, "threshold": -0.05},
    "SATELLITE": {"window": 10, "threshold": -0.03},
    "WAVE_SWING":{"window": 5,  "threshold": -0.03},
}

# False-negative thresholds (N-day return above threshold without role signal = FN candidate)
FN_THRESHOLDS = {
    "CORE":      {"window": 20, "threshold": 0.08},
    "CORE_ETF":  {"window": 20, "threshold": 0.05},
    "SATELLITE": {"window": 10, "threshold": 0.05},
    "WAVE_SWING":{"window": 5,  "threshold": 0.05},
}

# PIT snapshot dates (from signal_quality_replay.py run on 2026-05-10)
PIT_DATES = {"2026-05-05", "2026-05-07", "2026-05-08"}


# ──────────────────────────────────────────────────────────────
# Data loading
# ──────────────────────────────────────────────────────────────

def load_role_map() -> dict:
    """Returns dict: normalized_ticker -> entry dict."""
    path = ROOT / "data/portfolio/role_map.json"
    with open(path) as f:
        data = json.load(f)
    result = {}
    for e in data["entries"]:
        key = e["ticker"].replace(".TWO", "").replace(".TW", "")
        result[key] = e
    return result


def build_role_groups(role_map: dict) -> dict[str, list[str]]:
    """Returns {active_role: [yf_ticker, ...]}"""
    groups: dict[str, list[str]] = {}
    for key, entry in role_map.items():
        role = entry["active_role"]
        ticker = entry["ticker"]
        # Normalise to yfinance-compatible ticker
        if role == "CORE_ETF":
            yf_ticker = ticker + ".TW" if "." not in ticker else ticker
        elif "." in ticker:
            yf_ticker = ticker
        else:
            yf_ticker = ticker + ".TW"
        groups.setdefault(role, []).append(yf_ticker)
    return groups


def download_ohlcv(tickers: list[str], start: str, end: str) -> dict[str, pd.DataFrame]:
    """Download adj-close OHLCV for all tickers. Returns {yf_ticker: df}."""
    if not tickers:
        return {}
    try:
        raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
        if raw.empty:
            return {}
        result = {}
        for t in tickers:
            try:
                if isinstance(raw.columns, pd.MultiIndex):
                    df = raw.xs(t, axis=1, level=1)[["Open", "High", "Low", "Close"]]
                else:
                    df = raw[["Open", "High", "Low", "Close"]]
                if not df.empty:
                    result[t] = df.dropna(how="all")
            except Exception:
                pass
        return result
    except Exception:
        return {}


# ──────────────────────────────────────────────────────────────
# Return calculations
# ──────────────────────────────────────────────────────────────

def calc_forward_return(df: pd.DataFrame, entry_date_str: str, n_days: int,
                        all_trading_days: list[str]) -> Optional[float]:
    """Return N-day forward return from entry_date close. None if data unavailable."""
    exit_date_str = nth_trading_day_after(entry_date_str, n_days)
    if exit_date_str is None:
        return None
    if exit_date_str > RUN_DATE:
        return None  # future data
    try:
        entry_idx = pd.Timestamp(entry_date_str)
        exit_idx = pd.Timestamp(exit_date_str)
        # Find closest available date on or before entry/exit
        avail = df.index
        entry_prices = df.loc[:entry_idx, "Close"]
        exit_prices  = df.loc[:exit_idx,  "Close"]
        if entry_prices.empty or exit_prices.empty:
            return None
        p0 = float(entry_prices.iloc[-1])
        p1 = float(exit_prices.iloc[-1])
        if p0 <= 0:
            return None
        return (p1 - p0) / p0
    except Exception:
        return None


def calc_max_runup(df: pd.DataFrame, entry_date_str: str, n_days: int) -> Optional[float]:
    """Max high between entry+1 and entry+N relative to entry close."""
    exit_date_str = nth_trading_day_after(entry_date_str, n_days)
    if exit_date_str is None or exit_date_str > RUN_DATE:
        return None
    try:
        entry_idx = pd.Timestamp(entry_date_str)
        exit_idx  = pd.Timestamp(exit_date_str)
        entry_prices = df.loc[:entry_idx, "Close"]
        if entry_prices.empty:
            return None
        p0 = float(entry_prices.iloc[-1])
        window_high = df.loc[entry_idx:exit_idx, "High"]
        if window_high.empty or p0 <= 0:
            return None
        return (float(window_high.max()) - p0) / p0
    except Exception:
        return None


def calc_max_drawdown(df: pd.DataFrame, entry_date_str: str, n_days: int) -> Optional[float]:
    """Max low between entry+1 and entry+N relative to entry close (negative value)."""
    exit_date_str = nth_trading_day_after(entry_date_str, n_days)
    if exit_date_str is None or exit_date_str > RUN_DATE:
        return None
    try:
        entry_idx = pd.Timestamp(entry_date_str)
        exit_idx  = pd.Timestamp(exit_date_str)
        entry_prices = df.loc[:entry_idx, "Close"]
        if entry_prices.empty:
            return None
        p0 = float(entry_prices.iloc[-1])
        window_low = df.loc[entry_idx:exit_idx, "Low"]
        if window_low.empty or p0 <= 0:
            return None
        return (float(window_low.min()) - p0) / p0
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────
# Aggregation helpers
# ──────────────────────────────────────────────────────────────

def safe_avg(vals: list[float]) -> Optional[float]:
    v = [x for x in vals if x is not None]
    return round(sum(v) / len(v), 4) if v else None


def safe_median(vals: list[float]) -> Optional[float]:
    v = [x for x in vals if x is not None]
    return round(statistics.median(v), 4) if v else None


def hit_rate(vals: list[float]) -> Optional[float]:
    v = [x for x in vals if x is not None]
    if not v:
        return None
    return round(sum(1 for x in v if x > 0) / len(v), 4)


def fmt_pct(val: Optional[float]) -> str:
    if val is None:
        return "N/A"
    return f"{val*100:+.2f}%"


def replay_quality(d: str) -> str:
    if d in PIT_DATES:
        return "PIT_SNAPSHOT"
    if d > RUN_DATE:
        return "INCOMPLETE"
    return "HISTORICAL_RECONSTRUCTED"


# ──────────────────────────────────────────────────────────────
# Core evaluation
# ──────────────────────────────────────────────────────────────

def evaluate_role_group(role: str, tickers: list[str], ohlcv: dict,
                        trading_days: list[str]) -> dict:
    """
    For each entry date × ticker, calculate role-appropriate forward returns.
    Returns aggregated stats.
    """
    windows = WINDOWS.get(role, [5, 10])
    fp_rule = FP_THRESHOLDS.get(role, {"window": 10, "threshold": -0.03})
    fn_rule = FN_THRESHOLDS.get(role, {"window": 10, "threshold": 0.05})

    # Per-window: list of all (date, ticker, return) observations
    window_returns: dict[int, list[float]] = {w: [] for w in windows}
    runup_window   = max(windows)
    drawdown_window= max(windows)
    runups: list[float]    = []
    drawdowns: list[float] = []

    date_entries: list[dict] = []
    fp_candidates: list[dict] = []
    fn_candidates: list[dict] = []

    for d in trading_days:
        day_obs = []
        for t in tickers:
            df = ohlcv.get(t)
            if df is None or df.empty:
                continue
            obs = {"date": d, "ticker": t, "quality": replay_quality(d)}
            for w in windows:
                r = calc_forward_return(df, d, w, trading_days)
                obs[f"r_{w}d"] = r
                if r is not None:
                    window_returns[w].append(r)
            ru = calc_max_runup(df, d, runup_window)
            dd = calc_max_drawdown(df, d, drawdown_window)
            obs["max_runup"]    = ru
            obs["max_drawdown"] = dd
            if ru is not None:
                runups.append(ru)
            if dd is not None:
                drawdowns.append(dd)
            day_obs.append(obs)

            # FP detection: held in role but underperforms
            fp_r = obs.get(f"r_{fp_rule['window']}d")
            if fp_r is not None and fp_r < fp_rule["threshold"]:
                fp_candidates.append({"date": d, "ticker": t,
                                      f"r_{fp_rule['window']}d": fp_r})

        if day_obs:
            date_entries.append({
                "date": d, "quality": replay_quality(d), "observations": day_obs
            })

    # Aggregate
    agg = {}
    for w in windows:
        vals = window_returns[w]
        agg[f"{w}D"] = {
            "n": len(vals),
            "avg": safe_avg(vals),
            "median": safe_median(vals),
            "hit_rate": hit_rate(vals),
        }

    max_runup_val    = max(runups)    if runups    else None
    min_drawdown_val = min(drawdowns) if drawdowns else None

    return {
        "role": role,
        "tickers": tickers,
        "ticker_count": len(tickers),
        "entry_dates_evaluated": len(trading_days),
        "agg": agg,
        "max_runup_overall":    round(max_runup_val, 4)    if max_runup_val    is not None else None,
        "max_drawdown_overall": round(min_drawdown_val, 4) if min_drawdown_val is not None else None,
        "false_positives": fp_candidates,
        "date_entries": date_entries,
    }


def evaluate_universe(all_tickers: list[str], ohlcv: dict,
                      trading_days: list[str]) -> dict:
    """Universe baseline (all non-ETF tickers)."""
    window_returns: dict[int, list[float]] = {1: [], 3: [], 5: [], 10: [], 20: []}
    for d in trading_days:
        for t in all_tickers:
            df = ohlcv.get(t)
            if df is None or df.empty:
                continue
            for w in [1, 3, 5, 10, 20]:
                r = calc_forward_return(df, d, w, trading_days)
                if r is not None:
                    window_returns[w].append(r)
    return {w: {"avg": safe_avg(v), "n": len(v)} for w, v in window_returns.items()}


# ──────────────────────────────────────────────────────────────
# Report generation
# ──────────────────────────────────────────────────────────────

def determine_verdict(role_results: dict, trading_days: list[str]) -> tuple[str, str]:
    """Returns (PASS|WARN|FAIL, reasoning)."""
    roles_with_data = 0
    useful_roles = 0

    for role, res in role_results.items():
        has_data = any(
            res["agg"].get(f"{w}D", {}).get("n", 0) >= 3
            for w in WINDOWS.get(role, [5])
        )
        if has_data:
            roles_with_data += 1
            primary_w = WINDOWS.get(role, [5])[0]
            agg_w = res["agg"].get(f"{primary_w}D", {})
            avg = agg_w.get("avg")
            hit = agg_w.get("hit_rate")
            if avg is not None or hit is not None:
                useful_roles += 1

    pit_count  = sum(1 for d in trading_days if d in PIT_DATES)
    total_days = len(trading_days)
    reconstructed = total_days - pit_count

    # Structural WARN: most days are HISTORICAL_RECONSTRUCTED (not true PIT replay)
    if pit_count < 5:
        return (
            "WARN",
            f"PIT snapshot 僅 {pit_count}/{total_days} 天，{reconstructed} 天為 HISTORICAL_RECONSTRUCTED。"
            f"角色分組有助解讀（{useful_roles}/4 角色顯示訊號），但資料來源可信度有限，"
            f"需累積更多 PIT snapshot 後才能確認 PASS。",
        )
    if roles_with_data < 2:
        return "WARN", f"僅 {roles_with_data}/4 個角色有足夠資料（需 ≥2）"
    if useful_roles >= 3:
        return "PASS", f"{useful_roles}/4 個角色顯示可用訊號，PIT={pit_count} 天"
    return "WARN", f"角色分層有助於解讀，但樣本量不足（PIT={pit_count}/{total_days}）"


def generate_report(
    trading_days: list[str],
    role_results: dict,
    universe: dict,
    verdict: str,
    verdict_reason: str,
) -> str:
    lines = [
        f"# Role-Based Signal Replay — {RUN_DATE}",
        "",
        f"**Verdict: {verdict}**",
        "",
        f"> {verdict_reason}",
        "",
        "---",
        "",
        "## 資料覆蓋",
        "",
        f"- 請求交易日數：{len(trading_days)}",
        f"- PIT_SNAPSHOT 日數：{sum(1 for d in trading_days if d in PIT_DATES)}",
        f"- HISTORICAL_RECONSTRUCTED 日數：{sum(1 for d in trading_days if d not in PIT_DATES and d <= RUN_DATE)}",
        "",
        "### 逐日 Replay Quality",
        "",
        "| 日期 | Replay 品質 |",
        "| --- | --- |",
    ]
    for d in trading_days:
        q = replay_quality(d)
        lines.append(f"| {d} | {q} |")

    lines += ["", "---", "", "## 角色分組統計", ""]

    for role in ["CORE", "CORE_ETF", "SATELLITE", "WAVE_SWING"]:
        res = role_results.get(role)
        if not res:
            continue
        lines += [f"### {role} （{res['ticker_count']} 個 ticker）", ""]
        lines.append(f"**Tickers：** {', '.join(res['tickers'])}")
        lines.append("")
        windows = WINDOWS.get(role, [5, 10])
        lines += [
            "| 窗口 | 樣本數 | 平均報酬 | 中位數 | Hit Rate |",
            "| --- | --- | --- | --- | --- |",
        ]
        for w in windows:
            agg = res["agg"].get(f"{w}D", {})
            n   = agg.get("n", 0)
            avg = fmt_pct(agg.get("avg"))
            med = fmt_pct(agg.get("median"))
            hit = f"{agg.get('hit_rate', 0)*100:.0f}%" if agg.get("hit_rate") is not None else "N/A"
            lines.append(f"| {w}D | {n} | {avg} | {med} | {hit} |")

        lines += [
            "",
            f"- **最大漲幅（{max(windows)}D 窗口）：** {fmt_pct(res.get('max_runup_overall'))}",
            f"- **最大跌幅（{max(windows)}D 窗口）：** {fmt_pct(res.get('max_drawdown_overall'))}",
            f"- **False Positives：** {len(res.get('false_positives', []))}",
            "",
        ]

    # Universe comparison table
    lines += [
        "---",
        "",
        "## 角色 vs 全宇宙比較",
        "",
        "| 角色 | 3D 平均 | 5D 平均 | 10D 平均 | 20D 平均 |",
        "| --- | --- | --- | --- | --- |",
    ]
    univ_row = "| Universe |"
    for w in [3, 5, 10, 20]:
        univ_row += f" {fmt_pct(universe.get(w, {}).get('avg'))} |"
    lines.append(univ_row)
    for role in ["CORE", "CORE_ETF", "SATELLITE", "WAVE_SWING"]:
        res = role_results.get(role)
        if not res:
            continue
        row = f"| {role} |"
        for w in [3, 5, 10, 20]:
            agg = res["agg"].get(f"{w}D", {})
            row += f" {fmt_pct(agg.get('avg'))} |"
        lines.append(row)

    # Answer the 5 questions
    lines += [
        "",
        "---",
        "",
        "## 任務問題回答",
        "",
    ]
    core_res  = role_results.get("CORE", {})
    sat_res   = role_results.get("SATELLITE", {})
    wave_res  = role_results.get("WAVE_SWING", {})

    def _agg(res, w):
        return res.get("agg", {}).get(f"{w}D", {}) if res else {}

    core_10d  = _agg(core_res, 10).get("avg")
    core_20d  = _agg(core_res, 20).get("avg")
    sat_10d   = _agg(sat_res, 10).get("avg")
    sat_20d   = _agg(sat_res, 20).get("avg")
    wave_3d   = _agg(wave_res, 3).get("avg")
    wave_5d   = _agg(wave_res, 5).get("avg")
    wave_10d  = _agg(wave_res, 10).get("avg")

    lines.append(f"**Q1. CORE 標的是否表現如核心持倉？**")
    if core_10d is not None:
        note = "偏弱" if core_10d < -0.02 else ("正常" if core_10d > 0 else "中性偏弱")
        lines.append(f"- CORE 10D 均報酬：{fmt_pct(core_10d)}，20D：{fmt_pct(core_20d)} → {note}")
        lines.append(f"- 注意：CORE 不應以 1D/3D 短期波動論斷，應以 10D/20D 趨勢評估")
    else:
        lines.append("- 資料不足，無法評估")
    lines.append("")

    lines.append(f"**Q2. SATELLITE 標的是否適合 5D–20D 波段擴張？**")
    if sat_10d is not None:
        note = "有潛力" if sat_10d and sat_10d > 0 else "尚未顯現"
        lines.append(f"- SATELLITE 5D：{fmt_pct(_agg(sat_res,5).get('avg'))}，10D：{fmt_pct(sat_10d)}，20D：{fmt_pct(sat_20d)} → {note}")
    else:
        lines.append("- 資料不足，無法評估")
    lines.append("")

    lines.append(f"**Q3. WAVE_SWING 標的是否適合 3D–10D 波動操作？**")
    if wave_3d is not None:
        note = "有訊號" if wave_5d and wave_5d > 0 else "訊號不明"
        lines.append(f"- WAVE_SWING 3D：{fmt_pct(wave_3d)}，5D：{fmt_pct(wave_5d)}，10D：{fmt_pct(wave_10d)} → {note}")
    else:
        lines.append("- 資料不足，無法評估")
    lines.append("")

    lines.append("**Q4. 前次 Top3 弱勢是否因角色混合所致？**")
    wave_3d_n = _agg(wave_res, 3).get("n", 0)
    if wave_3d_n > 0:
        prev_top3 = -0.0317
        wave_3d_v = _agg(wave_res, 3).get("avg")
        if wave_3d_v is not None:
            if abs(wave_3d_v - prev_top3) > 0.01:
                lines.append(f"- 前次 all-in-one Top3 1D均 -3.17%，WAVE_SWING 3D均 {fmt_pct(wave_3d_v)} → 分組後表現有差異，混合評估確實掩蓋角色差異")
            else:
                lines.append(f"- 前次 Top3 1D均 -3.17%，WAVE_SWING 3D均 {fmt_pct(wave_3d_v)} → 差異不顯著，需更多資料確認")
    else:
        lines.append("- WAVE_SWING 3D 資料不足，無法直接比較")
    lines.append("")

    lines.append("**Q5. 目前雷達按角色是否可用？**")
    roles_with_n = sum(
        1 for r in ["CORE", "SATELLITE", "WAVE_SWING"]
        if any(role_results.get(r, {}).get("agg", {}).get(f"{w}D", {}).get("n", 0) >= 3
               for w in WINDOWS.get(r, [5]))
    )
    lines.append(f"- {roles_with_n}/3 個主要角色有足夠資料（n≥3）→ {'初步可用，建議持續累積' if roles_with_n >= 2 else '資料不足，暫緩結論'}")
    lines.append("")

    # Final verdict
    lines += [
        "---",
        "",
        "## 最終結果",
        "",
        f"```",
        verdict,
        f"```",
        "",
        f"**理由：** {verdict_reason}",
        "",
        "---",
        "",
        f"*報告產生時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "*分析腳本：`analysis/role_based_signal_replay.py`*",
        "*無任何持倉或交易資料被修改。*",
    ]
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def run(days: int = 20):
    print(f"=== Role-Based Signal Replay v0.2 ===")
    print(f"Run date: {RUN_DATE}  | Requested days: {days}")
    print()

    # 1. Load role map
    role_map    = load_role_map()
    role_groups = build_role_groups(role_map)
    print("Role groups:")
    for role, tickers in sorted(role_groups.items()):
        print(f"  {role:12}: {len(tickers)} tickers → {tickers}")
    print()

    # 2. Get trading days
    trading_days = get_trading_days(days)
    print(f"Trading days ({len(trading_days)}): {trading_days[0]} … {trading_days[-1]}")
    pit_count = sum(1 for d in trading_days if d in PIT_DATES)
    print(f"PIT_SNAPSHOT: {pit_count}  HISTORICAL_RECONSTRUCTED: {len(trading_days)-pit_count}")
    print()

    # 3. Download OHLCV — need enough history for 20D forward from earliest entry day
    all_stock_tickers = [t for role, tickers in role_groups.items()
                         if role not in ("CORE_ETF",) for t in tickers]
    etf_tickers = role_groups.get("CORE_ETF", [])
    all_tickers  = all_stock_tickers + etf_tickers

    # Start far enough back to cover oldest entry + 20D forward
    oldest_day = trading_days[-1]
    earliest_start = (
        datetime.strptime(oldest_day, "%Y-%m-%d") - timedelta(days=5)
    ).strftime("%Y-%m-%d")
    download_end = (
        datetime.strptime(RUN_DATE, "%Y-%m-%d") + timedelta(days=32)
    ).strftime("%Y-%m-%d")

    print(f"Downloading OHLCV for {len(all_tickers)} tickers: {earliest_start} → {download_end}")
    ohlcv = download_ohlcv(all_tickers, earliest_start, download_end)
    print(f"Downloaded: {len(ohlcv)}/{len(all_tickers)} tickers with data")
    print()

    # 4. Evaluate each role
    role_results = {}
    for role in ["CORE", "CORE_ETF", "SATELLITE", "WAVE_SWING"]:
        tickers = role_groups.get(role, [])
        if not tickers:
            continue
        print(f"Evaluating {role} ({len(tickers)} tickers)…")
        res = evaluate_role_group(role, tickers, ohlcv, trading_days)
        role_results[role] = res
        for w, agg in res["agg"].items():
            n = agg.get("n", 0)
            avg = fmt_pct(agg.get("avg"))
            hit = f"{agg.get('hit_rate',0)*100:.0f}%" if agg.get("hit_rate") is not None else "N/A"
            print(f"  {w}: n={n:3d}  avg={avg}  hit={hit}")

    print()

    # 5. Universe baseline (all non-ETF tickers in role_map)
    print("Computing universe baseline…")
    universe = evaluate_universe(all_stock_tickers, ohlcv, trading_days)
    for w in [3, 5, 10, 20]:
        print(f"  Universe {w}D: n={universe[w]['n']:3d}  avg={fmt_pct(universe[w].get('avg'))}")
    print()

    # 6. Verdict
    verdict, verdict_reason = determine_verdict(role_results, trading_days)
    print(f"Verdict: {verdict}")
    print(f"Reason:  {verdict_reason}")
    print()

    # 7. Write outputs
    report_md = generate_report(trading_days, role_results, universe, verdict, verdict_reason)

    md_path = ROOT / f"reports/validation/{RUN_DATE}_role_based_signal_replay.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(report_md)
    print(f"Report:  {md_path}")

    # Serialise role_results for JSON (strip DataFrames, keep primitives)
    def _serialise(obj):
        if isinstance(obj, dict):
            return {k: _serialise(v) for k, v in obj.items() if k != "date_entries"}
        if isinstance(obj, list):
            return [_serialise(x) for x in obj]
        if isinstance(obj, float) and (obj != obj):
            return None
        return obj

    json_out = {
        "run_date": RUN_DATE,
        "generated_at": datetime.now().isoformat(),
        "days_requested": days,
        "trading_days": trading_days,
        "pit_dates": sorted(PIT_DATES),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "universe": universe,
        "roles": {r: _serialise(v) for r, v in role_results.items()},
    }
    json_path = ROOT / f"data/validation/{RUN_DATE}_role_based_signal_replay.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(json_out, indent=2, ensure_ascii=False))
    print(f"JSON:    {json_path}")

    return role_results, universe, verdict, verdict_reason


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=20)
    args = parser.parse_args()
    run(args.days)


if __name__ == "__main__":
    main()
