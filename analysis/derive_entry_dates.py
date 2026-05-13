#!/usr/bin/env python3
"""
Derive Holdings Entry Dates v0.1
Analysis-only: does NOT modify current_holdings.json or trade_log.json.

Derivation priority:
1. Explicit broker-verified entry date (field in holdings) — none currently available
2. Trade log matching buy event with price within 2% of holdings entry_price
3. Daily report ALREADY_IN_POSITION / first-BUY-signal evidence
4. yfinance price matching: find trading days where close ≈ entry_price (±2%)
5. UNKNOWN if no reliable source

Output:
  reports/validation/YYYY-MM-DD_entry_date_derivation.md
  data/validation/YYYY-MM-DD_entry_date_derivation.json
"""

import json
import os
from datetime import datetime, date, timedelta

import yfinance as yf

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_DATE = date.today().isoformat()

PRICE_TOLERANCE = 0.02  # ±2%
PRICE_SEARCH_START = "2024-01-01"

# yfinance ticker mapping for Taiwan market
TICKER_MAP = {
    "009816": "009816.TW",
    "00992A": "00992A.TW",
    "2330": "2330.TW",
    "2345": "2345.TW",
    "2408": "2408.TW",
    "3711": "3711.TW",
    "6830": "6830.TW",
}


def load_holdings():
    path = os.path.join(REPO_ROOT, "data/portfolio/current_holdings.json")
    with open(path) as f:
        return json.load(f)


def load_trade_log():
    path = os.path.join(REPO_ROOT, "data/trade_log.json")
    with open(path) as f:
        return json.load(f)


def scan_daily_reports_for_position_clues():
    """
    Scan daily reports for ALREADY_IN_POSITION and first-BUY signals.
    Returns dict: ticker -> list of {"date", "action", "reason", "source"}
    """
    reports_dir = os.path.join(REPO_ROOT, "reports/daily")
    clues = {}

    for fname in sorted(os.listdir(reports_dir)):
        if not fname.endswith("_daily_report.md"):
            continue
        report_date = fname[:10]
        path = os.path.join(reports_dir, fname)
        with open(path) as f:
            content = f.read()

        # Find Decisions table rows
        in_decisions = False
        for line in content.splitlines():
            if "### Decisions" in line:
                in_decisions = True
                continue
            if in_decisions and line.startswith("|") and not line.startswith("| ---") and "Ticker" not in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 3:
                    ticker_raw = parts[0]
                    action = parts[1]
                    reason = parts[2]
                    # Normalize ticker: strip .TW/.TWO suffix for matching
                    ticker = ticker_raw.replace(".TW", "").replace(".TWO", "")
                    if ticker not in clues:
                        clues[ticker] = []
                    clues[ticker].append({
                        "date": report_date,
                        "action": action,
                        "reason": reason,
                        "source": f"reports/daily/{fname}",
                    })
            if in_decisions and line.startswith("##") and "Decisions" not in line:
                in_decisions = False

    return clues


def price_match(ticker_yf, entry_price, tolerance=PRICE_TOLERANCE, upper_bound=None):
    """
    Search yfinance price history for dates where close ≈ entry_price.
    upper_bound: optional date string (YYYY-MM-DD) — only include dates on or before this.
    Returns list of {"date", "close", "pct_diff"} sorted most-recent first.
    """
    try:
        data = yf.download(
            ticker_yf,
            start=PRICE_SEARCH_START,
            end=RUN_DATE,
            progress=False,
            auto_adjust=True,
        )
        if data.empty:
            return []

        # Handle MultiIndex columns (yfinance returns ('Close', 'TICKER') format)
        if hasattr(data.columns, "levels"):
            close = data[("Close", ticker_yf)]
        else:
            close = data["Close"]

        matches = []
        for dt, price_val in close.items():
            p = float(price_val)
            if p <= 0:
                continue
            dt_str = str(dt.date())
            if upper_bound and dt_str > upper_bound:
                continue
            pct = (p - entry_price) / entry_price
            if abs(pct) <= tolerance:
                matches.append({
                    "date": dt_str,
                    "close": round(p, 2),
                    "pct_diff": round(pct * 100, 2),
                })

        matches.sort(key=lambda x: x["date"], reverse=True)
        return matches
    except Exception:
        return []


def derive_holding(holding, trade_log, daily_clues):
    """
    Derive entry date for a single holding.
    Returns enriched dict with: proposed_entry_date, source_used, confidence, reason, notes, price_candidates
    """
    ticker = holding["ticker"]
    entry_price = holding.get("entry_price")
    name = holding.get("name", ticker)
    ticker_yf = TICKER_MAP.get(ticker, ticker + ".TW")

    result = {
        "ticker": ticker,
        "name": name,
        "quantity": holding.get("shares"),
        "cost_basis": holding.get("cost_basis"),
        "entry_price": entry_price,
        "proposed_entry_date": "UNKNOWN",
        "source_used": "NONE",
        "confidence": "UNKNOWN",
        "reason": "",
        "notes": "",
        "price_candidates": [],
    }

    evidence_lines = []

    # All holdings confirmed present by 2026-05-07 (current_holdings.json as_of date)
    # Holdings count was 8 on 2026-05-01, so most holdings predate 2026-05-01
    upper_bound = "2026-04-30"

    # --- Source 1: trade_log buy event ---
    tl_matches = [
        e for e in trade_log
        if e.get("action") == "BUY"
        and e.get("ticker", "").replace(".TW", "").replace(".TWO", "") == ticker
    ]
    for tl in tl_matches:
        tl_price = tl.get("price", 0)
        pct_diff = abs(tl_price - entry_price) / max(entry_price, 1) if entry_price else 1
        if entry_price and pct_diff <= 0.02:
            result["proposed_entry_date"] = tl["date"]
            result["source_used"] = "trade_log.json (price match ±2%)"
            result["confidence"] = "MEDIUM"
            result["reason"] = (
                f"trade_log BUY on {tl['date']} at {tl_price} matches holdings entry_price {entry_price} (±2%)"
            )
            evidence_lines.append(f"trade_log: BUY {tl['date']} @ {tl_price} ✓ price match")
        else:
            diff_pct = round((tl_price - entry_price) / max(entry_price, 1) * 100, 1) if entry_price else "N/A"
            evidence_lines.append(
                f"trade_log: BUY {tl['date']} @ {tl_price} — ADVISORY MISMATCH "
                f"(holdings entry_price={entry_price}, diff={diff_pct}%) — not used"
            )

    # --- Source 2: daily report clues ---
    clue_key = ticker
    dc = daily_clues.get(clue_key, [])
    if dc:
        first_appear = dc[0]
        last_appear = dc[-1]
        evidence_lines.append(
            f"daily_report: first seen {first_appear['date']} "
            f"({first_appear['action']}/{first_appear['reason']}), last seen {last_appear['date']}"
        )
        first_alip = next((c for c in dc if "ALREADY_IN_POSITION" in c.get("reason", "")), None)
        if first_alip:
            result["notes"] = (
                f"ALREADY_IN_POSITION in pipeline since {first_alip['date']} "
                f"(pipeline position lock uses trade_log, not current_holdings)"
            )

    # --- Source 3: yfinance price matching (with upper_bound) ---
    if entry_price:
        price_matches = price_match(ticker_yf, entry_price, upper_bound=upper_bound)
        result["price_candidates"] = price_matches[:10]

        if price_matches and result["confidence"] == "UNKNOWN":
            best = price_matches[0]  # most recent match within upper_bound
            result["proposed_entry_date"] = best["date"]
            result["source_used"] = (
                f"yfinance price match ±2% before {upper_bound} "
                f"(best: {best['date']} @ {best['close']})"
            )
            result["confidence"] = "LOW"
            result["reason"] = (
                f"No repo evidence of exact entry date. "
                f"Most recent date (before {upper_bound}) with close ≈ entry_price {entry_price}: "
                f"{best['date']} (close={best['close']}, diff={best['pct_diff']:+.1f}%). "
                f"Price match is not conclusive — {len(price_matches)} candidate date(s) found."
            )
        elif not price_matches and result["confidence"] == "UNKNOWN":
            result["notes"] += (
                f" No price match found within ±2% of {entry_price} before {upper_bound}. "
                f"Owner must provide entry date manually."
            )

    result["evidence_lines"] = evidence_lines
    return result


def classify_action(confidence, proposed_date):
    if confidence in ("HIGH", "MEDIUM") and proposed_date != "UNKNOWN":
        return "safe-to-apply"
    elif confidence == "LOW" and proposed_date != "UNKNOWN":
        return "needs-owner-review"
    else:
        return "unknown"


def generate_report(results, output_date):
    lines = [
        f"# Holdings Entry Date Derivation — {output_date}",
        "",
        "**分析目的：** 為 `current_holdings.json` 中的每筆持倉推導 `entry_date`，供 Role-Based Position Model 使用。",
        "**限制：** 此為分析報告，不修改任何持倉檔案。所有結果待 owner/GPT 審閱後方可套用。",
        "",
        "---",
        "",
        "## 摘要表",
        "",
        "| Ticker | 名稱 | 提議進場日 | 信心度 | 資料來源 | 建議動作 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for r in results:
        action = classify_action(r["confidence"], r["proposed_entry_date"])
        action_label = {
            "safe-to-apply": "✅ 可套用",
            "needs-owner-review": "⚠️ 需 owner 確認",
            "unknown": "❓ 未知",
        }[action]
        lines.append(
            f"| {r['ticker']} | {r['name']} | {r['proposed_entry_date']} "
            f"| {r['confidence']} | {r['source_used'][:50]}{'...' if len(r['source_used'])>50 else ''} "
            f"| {action_label} |"
        )

    # Confidence distribution
    conf_dist = {}
    for r in results:
        conf_dist[r["confidence"]] = conf_dist.get(r["confidence"], 0) + 1

    lines += [
        "",
        "---",
        "",
        "## 信心度分佈",
        "",
        "| 信心度 | 筆數 |",
        "| --- | --- |",
    ]
    for k, v in sorted(conf_dist.items()):
        lines.append(f"| {k} | {v} |")

    # Per-holding details
    lines += [
        "",
        "---",
        "",
        "## 各持倉推導明細",
        "",
    ]

    for r in results:
        action = classify_action(r["confidence"], r["proposed_entry_date"])
        action_label = {"safe-to-apply": "✅ 可套用", "needs-owner-review": "⚠️ 需 owner 確認", "unknown": "❓ 未知"}[action]
        lines += [
            f"### {r['ticker']} {r['name']}",
            "",
            f"- **數量：** {r['quantity']}",
            f"- **進場價：** {r['entry_price']}",
            f"- **成本：** {r['cost_basis']}",
            f"- **提議進場日：** `{r['proposed_entry_date']}`",
            f"- **信心度：** {r['confidence']}",
            f"- **資料來源：** {r['source_used']}",
            f"- **推導理由：** {r['reason']}",
        ]
        if r.get("notes"):
            lines.append(f"- **備注：** {r['notes']}")
        if r.get("evidence_lines"):
            lines.append("- **佐證資料：**")
            for ev in r["evidence_lines"]:
                lines.append(f"  - {ev}")
        if r.get("price_candidates"):
            top = r["price_candidates"][:5]
            lines.append("- **價格比對候選日（前5筆，最近優先）：**")
            for pc in top:
                lines.append(f"  - {pc['date']} close={pc['close']} ({pc['pct_diff']:+.1f}%)")
        lines.append(f"- **建議動作：** {action_label}")
        lines.append("")

    # Unknown / low-confidence section
    low_items = [r for r in results if r["confidence"] in ("LOW", "UNKNOWN")]
    lines += [
        "---",
        "",
        "## 需 Owner 確認 / 未知項目",
        "",
        f"以下 {len(low_items)} 筆持倉信心度為 LOW 或 UNKNOWN，須 owner 人工確認：",
        "",
        "| Ticker | 名稱 | 提議日 | 信心度 | 主要限制 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in low_items:
        limit = "無任何佐證資料" if r["confidence"] == "UNKNOWN" else "僅有間接佐證，非確認成交日"
        lines.append(f"| {r['ticker']} | {r['name']} | {r['proposed_entry_date']} | {r['confidence']} | {limit} |")

    # Recommended next action
    safe_count = sum(1 for r in results if classify_action(r["confidence"], r["proposed_entry_date"]) == "safe-to-apply")
    review_count = sum(1 for r in results if classify_action(r["confidence"], r["proposed_entry_date"]) == "needs-owner-review")
    unknown_count = sum(1 for r in results if classify_action(r["confidence"], r["proposed_entry_date"]) == "unknown")

    lines += [
        "",
        "---",
        "",
        "## 建議後續行動",
        "",
        f"- **可直接套用：** {safe_count} 筆（HIGH/MEDIUM 信心度）",
        f"- **需 owner 確認：** {review_count} 筆（LOW 信心度）",
        f"- **未知，需人工輸入：** {unknown_count} 筆",
        "",
    ]

    if safe_count == len(results) and unknown_count == 0 and review_count == 0:
        lines.append("**建議任務：** `Apply Entry Dates to current_holdings.json v0.1`")
    else:
        lines.append("**建議任務：** `Manual Owner Review Required for Low-Confidence Entry Dates`")
        lines.append("")
        lines.append(
            "> 建議 owner 從券商後台查詢以下持倉的實際成交日期，確認後補入 `current_holdings.json` 的 `entry_date` 欄位："
        )
        for r in results:
            if classify_action(r["confidence"], r["proposed_entry_date"]) in ("needs-owner-review", "unknown"):
                lines.append(
                    f"> - **{r['ticker']} {r['name']}** — 系統推估日期：{r['proposed_entry_date']}（{r['confidence']}）"
                    f"，進場價參考：{r['entry_price']}"
                )

    lines += [
        "",
        "---",
        "",
        f"*報告產生時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "*分析腳本：`analysis/derive_entry_dates.py`*",
        "*無任何持倉或交易資料被修改。*",
    ]

    return "\n".join(lines)


def run():
    print("=== Derive Holdings Entry Dates v0.1 ===")
    print(f"Run date: {RUN_DATE}")
    print(f"Repo root: {REPO_ROOT}")
    print()

    holdings_data = load_holdings()
    trade_log = load_trade_log()
    daily_clues = scan_daily_reports_for_position_clues()

    print(f"Holdings loaded: {len(holdings_data['holdings'])}")
    print(f"Trade log entries: {len(trade_log)}")
    print(f"Tickers with daily report clues: {list(daily_clues.keys())}")
    print()

    results = []
    for holding in holdings_data["holdings"]:
        ticker = holding["ticker"]
        print(f"Processing {ticker} {holding.get('name', '')}...")
        r = derive_holding(holding, trade_log, daily_clues)
        results.append(r)
        print(f"  → proposed_entry_date={r['proposed_entry_date']} confidence={r['confidence']}")

    print()

    # Generate report
    report_md = generate_report(results, RUN_DATE)
    md_path = os.path.join(REPO_ROOT, f"reports/validation/{RUN_DATE}_entry_date_derivation.md")
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w") as f:
        f.write(report_md)
    print(f"Report written: {md_path}")

    # Generate JSON
    json_output = {
        "run_date": RUN_DATE,
        "generated_at": datetime.now().isoformat(),
        "holdings_as_of": holdings_data.get("as_of"),
        "derivation_results": [
            {k: v for k, v in r.items() if k != "evidence_lines"}
            for r in results
        ],
        "summary": {
            "total": len(results),
            "safe_to_apply": sum(
                1 for r in results if classify_action(r["confidence"], r["proposed_entry_date"]) == "safe-to-apply"
            ),
            "needs_owner_review": sum(
                1 for r in results if classify_action(r["confidence"], r["proposed_entry_date"]) == "needs-owner-review"
            ),
            "unknown": sum(
                1 for r in results if classify_action(r["confidence"], r["proposed_entry_date"]) == "unknown"
            ),
            "confidence_distribution": {},
        },
    }
    for r in results:
        c = r["confidence"]
        json_output["summary"]["confidence_distribution"][c] = (
            json_output["summary"]["confidence_distribution"].get(c, 0) + 1
        )

    json_path = os.path.join(REPO_ROOT, f"data/validation/{RUN_DATE}_entry_date_derivation.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)
    print(f"JSON written: {json_path}")

    # Print summary
    print()
    print("=== Summary ===")
    for r in results:
        action = classify_action(r["confidence"], r["proposed_entry_date"])
        print(f"{r['ticker']:8} {r['name']:12} → {r['proposed_entry_date']:12} [{r['confidence']:7}] {action}")

    return results, md_path, json_path


if __name__ == "__main__":
    run()
