#!/usr/bin/env python3
"""
Role Classifier v0.1
Classifies current holdings and watchlist/candidate tickers into:
  CORE / CORE_ETF / SATELLITE / WAVE_SWING

Classification priority:
  1. Owner-approved seed mapping (HIGH)
  2. Current holdings + watchlist layer (MEDIUM)
  3. Watchlist layer prior only (MEDIUM)
  4. Recent candidate from snapshot (LOW)
  5. UNKNOWN

Does NOT modify current_holdings.json, trade_log.json, or any pipeline logic.

Usage:
  python3 -m portfolio.role_classifier
"""

import json
import os
from datetime import date, datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_DATE = date.today().isoformat()

# ---------------------------------------------------------------------------
# Owner-approved seed mapping (v0.1, per Notion task decision)
# Keys are normalized symbols (stripped of .TW/.TWO suffix)
# ---------------------------------------------------------------------------
SEED_MAP = {
    "009816": {
        "base_role": "CORE_ETF",
        "active_role": "CORE_ETF",
        "intent": None,
        "upgrade_path": None,
    },
    "00992A": {
        "base_role": "CORE_ETF",
        "active_role": "CORE_ETF",
        "intent": None,
        "upgrade_path": None,
    },
    "2330": {
        "base_role": "CORE",
        "active_role": "CORE",
        "intent": None,
        "upgrade_path": None,
    },
    "6830": {
        "base_role": "SATELLITE",
        "active_role": "WAVE_SWING",
        "intent": None,
        "upgrade_path": None,
    },
    "2345": {
        "base_role": "CORE",
        "active_role": "SATELLITE",
        "intent": "HOLD_OR_ADD_ON_PULLBACK",
        "upgrade_path": "WAVE_SWING",
    },
    "3711": {
        "base_role": "CORE",
        "active_role": "CORE",
        "intent": None,
        "upgrade_path": None,
    },
    "2408": {
        "base_role": "SATELLITE",
        "active_role": "SATELLITE",
        "intent": None,
        "upgrade_path": None,
    },
}

# Watchlist layer → base_role / active_role prior
LAYER_ROLE_MAP = {
    1: ("CORE", "CORE"),
    2: ("SATELLITE", "SATELLITE"),
    3: ("SATELLITE", "SATELLITE"),
    4: ("WAVE_SWING", "WAVE_SWING"),
    5: ("WAVE_SWING", "WAVE_SWING"),
}


def norm(ticker: str) -> str:
    """Strip .TW / .TWO suffix for key lookups."""
    return ticker.replace(".TWO", "").replace(".TW", "")


def load_json(rel_path: str) -> dict | list:
    path = os.path.join(REPO_ROOT, rel_path)
    with open(path) as f:
        return json.load(f)


def build_holdings_map(holdings_data: dict) -> dict:
    """Return dict keyed by normalized ticker with holdings info."""
    out = {}
    for h in holdings_data.get("holdings", []):
        key = norm(h["ticker"])
        out[key] = {
            "ticker_raw": h["ticker"],
            "name": h.get("name", h["ticker"]),
            "shares": h.get("shares"),
            "entry_price": h.get("entry_price"),
            "cost_basis": h.get("cost_basis"),
            "entry_date": h.get("entry_date", "UNKNOWN"),
            "entry_date_confidence": h.get("entry_date_confidence", "UNKNOWN"),
        }
    return out


def build_watchlist_map(watchlist_data: dict) -> dict:
    """Return dict keyed by normalized ticker with layer info."""
    out = {}
    for t in watchlist_data.get("tickers", []):
        key = norm(t["symbol"])
        out[key] = {
            "ticker_raw": t["yf_symbol"],
            "name": t.get("name", t["symbol"]),
            "layer": t.get("meta", {}).get("layer_order"),
            "industry": t.get("meta", {}).get("industry"),
        }
    return out


def build_p1_map(p1_data: dict) -> dict:
    """Return dict keyed by normalized ticker with latest P1 audit result."""
    out = {}
    for entry in p1_data.get("audit_entries", []):
        key = norm(entry["ticker"])
        out[key] = {
            "p1_action": entry.get("p1_audit_action"),
            "entry_lock_status": entry.get("entry_lock", {}).get("entry_lock_status"),
            "score": None,  # score not in p1 entry directly
        }
    return out


def build_snapshot_map(snapshot_data: dict) -> dict:
    """Return dict keyed by normalized ticker with ranking/score data."""
    out = {}
    for r in snapshot_data.get("ranked", []):
        key = norm(r["ticker"])
        out[key] = {
            "ticker_raw": r["ticker"],
            "name": r.get("name", r["ticker"]),
            "score": r.get("score"),
            "signal": r.get("signal"),
            "level": r.get("level"),
            "narrative_strength": r.get("narrative_strength"),
        }
    return out


def classify(
    ticker_norm: str,
    ticker_canonical: str,
    name: str,
    holdings_map: dict,
    watchlist_map: dict,
    p1_map: dict,
    snapshot_map: dict,
) -> dict:
    """
    Produce a single role_map entry for one ticker.
    """
    holding = holdings_map.get(ticker_norm)
    watchlist = watchlist_map.get(ticker_norm)
    p1 = p1_map.get(ticker_norm)
    snap = snapshot_map.get(ticker_norm)

    entry_date = "UNKNOWN"
    entry_date_confidence = "UNKNOWN"
    if holding:
        entry_date = holding.get("entry_date", "UNKNOWN") or "UNKNOWN"
        entry_date_confidence = holding.get("entry_date_confidence", "UNKNOWN") or "UNKNOWN"

    role_reasons = []
    base_role = "UNKNOWN"
    active_role = "UNKNOWN"
    role_confidence = "UNKNOWN"
    intent = None
    upgrade_path = None

    # --- Priority 1: owner seed mapping ---
    if ticker_norm in SEED_MAP:
        seed = SEED_MAP[ticker_norm]
        base_role = seed["base_role"]
        active_role = seed["active_role"]
        intent = seed.get("intent")
        upgrade_path = seed.get("upgrade_path")
        role_confidence = "HIGH"
        role_reasons.append("owner_seed_mapping")
        if holding:
            role_reasons.append("current_holding")
        if entry_date == "UNKNOWN":
            role_reasons.append("entry_date_missing")

    # --- Priority 2: current holdings + watchlist layer ---
    elif holding and watchlist:
        layer = watchlist.get("layer")
        if layer and layer in LAYER_ROLE_MAP:
            base_role, active_role = LAYER_ROLE_MAP[layer]
            role_confidence = "MEDIUM"
            role_reasons.extend(["current_holding", "watchlist_layer_prior"])
        else:
            base_role = "UNKNOWN"
            active_role = "UNKNOWN"
            role_confidence = "LOW"
            role_reasons.extend(["current_holding", "watchlist_layer_missing"])
        if entry_date == "UNKNOWN":
            role_reasons.append("entry_date_missing")

    # --- Priority 3: watchlist only (not currently held) ---
    elif watchlist:
        layer = watchlist.get("layer")
        if layer and layer in LAYER_ROLE_MAP:
            base_role, active_role = LAYER_ROLE_MAP[layer]
            role_confidence = "MEDIUM"
            role_reasons.append("watchlist_layer_prior")
        else:
            role_confidence = "LOW"
            role_reasons.append("watchlist_layer_missing")

        # Supplement with technical context if available
        if snap:
            role_reasons.append(f"snapshot_score_{snap.get('score', 'N/A')}")
        if p1:
            role_reasons.append(f"p1_audit_{p1.get('p1_action', 'N/A')}")

    # --- Priority 4: recent candidate from snapshot only ---
    elif snap:
        base_role = "WAVE_SWING"
        active_role = "WAVE_SWING"
        role_confidence = "LOW"
        role_reasons.append("snapshot_candidate_only")
        role_reasons.append(f"score_{snap.get('score', 'N/A')}")
        if p1:
            role_reasons.append(f"p1_audit_{p1.get('p1_action', 'N/A')}")

    # --- Priority 5: holding but not in watchlist or snapshot ---
    elif holding:
        role_confidence = "UNKNOWN"
        role_reasons.extend(["current_holding", "no_watchlist_context"])
        if entry_date == "UNKNOWN":
            role_reasons.append("entry_date_missing")

    else:
        role_confidence = "UNKNOWN"
        role_reasons.append("insufficient_data")

    # Add p1/trend context as annotation (does not change role/confidence)
    if p1 and "p1_audit" not in " ".join(role_reasons):
        role_reasons.append(f"p1_context_{p1.get('p1_action', 'N/A')}")

    return {
        "ticker": ticker_canonical,
        "name": name,
        "base_role": base_role,
        "active_role": active_role,
        "role_confidence": role_confidence,
        "entry_date": entry_date,
        "entry_date_confidence": entry_date_confidence,
        "intent": intent,
        "upgrade_path": upgrade_path,
        "role_reason": role_reasons,
        "is_held": holding is not None,
        "last_updated": RUN_DATE,
    }


def run():
    print("=== Role Classifier v0.1 ===")
    print(f"Run date: {RUN_DATE}")
    print()

    # Load data
    holdings_data = load_json("data/portfolio/current_holdings.json")
    watchlist_data = load_json("data/watchlist.json")
    snapshot_data = load_json("data/processed/mainline_snapshot.json")
    p1_data = load_json("data/processed/p1_audit_report.json")

    holdings_map = build_holdings_map(holdings_data)
    watchlist_map = build_watchlist_map(watchlist_data)
    snapshot_map = build_snapshot_map(snapshot_data)
    p1_map = build_p1_map(p1_data)

    print(f"Holdings: {len(holdings_map)}")
    print(f"Watchlist tickers: {len(watchlist_map)}")
    print(f"Snapshot candidates: {len(snapshot_map)}")
    print(f"P1 audit entries: {len(p1_map)}")
    print()

    # Collect all unique tickers to classify
    # Order: holdings first, then watchlist, then snapshot-only
    all_tickers = {}  # norm_key -> (canonical, name)

    for key, h in holdings_map.items():
        canonical = h["ticker_raw"]
        # Ensure canonical has .TW suffix for stock holdings
        if "." not in canonical and key not in ("009816", "00992A"):
            canonical = canonical + ".TW"
        all_tickers[key] = (canonical, h["name"])

    for key, w in watchlist_map.items():
        if key not in all_tickers:
            all_tickers[key] = (w["ticker_raw"], w["name"])

    for key, s in snapshot_map.items():
        if key not in all_tickers:
            all_tickers[key] = (s["ticker_raw"], s["name"])

    # Classify all
    results = []
    for key, (canonical, name) in sorted(all_tickers.items()):
        r = classify(key, canonical, name, holdings_map, watchlist_map, p1_map, snapshot_map)
        results.append(r)
        held_marker = "★" if r["is_held"] else " "
        print(f"{held_marker} {r['ticker']:12} {r['name'][:12]:12} "
              f"base={r['base_role']:10} active={r['active_role']:10} "
              f"conf={r['role_confidence']:7}")

    print()

    # Write role_map.json
    role_map = {
        "generated_at": datetime.now().isoformat(),
        "run_date": RUN_DATE,
        "data_sources": {
            "holdings_as_of": holdings_data.get("as_of"),
            "snapshot_as_of": snapshot_data.get("generated_at", "unknown"),
            "p1_audit_as_of": p1_data.get("generated_at", "unknown"),
        },
        "seed_map_version": "v0.1",
        "entries": results,
    }

    out_path = os.path.join(REPO_ROOT, "data/portfolio/role_map.json")
    with open(out_path, "w") as f:
        json.dump(role_map, f, indent=2, ensure_ascii=False)
    print(f"role_map.json written: {out_path} ({len(results)} entries)")

    # Write report
    report = _build_report(results, role_map)
    report_path = os.path.join(
        REPO_ROOT, f"reports/validation/{RUN_DATE}_role_classifier_report.md"
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Report written: {report_path}")

    return results, out_path, report_path


def _build_report(results: list, role_map: dict) -> str:
    lines = [
        f"# Role Classifier Report — {RUN_DATE}",
        "",
        f"**產生時間：** {role_map['generated_at']}",
        f"**Seed Map 版本：** {role_map['seed_map_version']}",
        f"**持倉資料截至：** {role_map['data_sources']['holdings_as_of']}",
        "",
        "---",
        "",
    ]

    # Role count
    from collections import Counter
    base_counts = Counter(r["base_role"] for r in results)
    active_counts = Counter(r["active_role"] for r in results)
    conf_counts = Counter(r["role_confidence"] for r in results)

    lines += [
        "## 角色分佈",
        "",
        "### base_role",
        "",
        "| 角色 | 筆數 |",
        "| --- | --- |",
    ]
    for role, cnt in sorted(base_counts.items()):
        lines.append(f"| {role} | {cnt} |")

    lines += [
        "",
        "### active_role",
        "",
        "| 角色 | 筆數 |",
        "| --- | --- |",
    ]
    for role, cnt in sorted(active_counts.items()):
        lines.append(f"| {role} | {cnt} |")

    lines += [
        "",
        "### 信心度分佈",
        "",
        "| 信心度 | 筆數 |",
        "| --- | --- |",
    ]
    for conf, cnt in sorted(conf_counts.items()):
        lines.append(f"| {conf} | {cnt} |")

    lines += ["", "---", ""]

    # Holdings summary
    held = [r for r in results if r["is_held"]]
    lines += [
        "## 持倉分類（current_holdings）",
        "",
        f"共 {len(held)} 筆持倉",
        "",
        "| Ticker | 名稱 | base_role | active_role | 信心度 | entry_date | 來源 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in held:
        reasons = " / ".join(r["role_reason"][:3])
        lines.append(
            f"| {r['ticker']} | {r['name']} | {r['base_role']} | {r['active_role']} "
            f"| {r['role_confidence']} | {r['entry_date']} | {reasons} |"
        )

    # entry_date UNKNOWN
    unknown_ed = [r for r in results if r["is_held"] and r["entry_date"] == "UNKNOWN"]
    lines += [
        "",
        f"### entry_date = UNKNOWN（{len(unknown_ed)} 筆持倉）",
        "",
    ]
    if unknown_ed:
        for r in unknown_ed:
            lines.append(f"- {r['ticker']} {r['name']}")
    else:
        lines.append("（無）")

    # Seed-mapped tickers
    seed_entries = [r for r in results if "owner_seed_mapping" in r["role_reason"]]
    lines += [
        "",
        "---",
        "",
        f"## Seed Mapping 套用（{len(seed_entries)} 筆）",
        "",
        "| Ticker | 名稱 | base_role | active_role | intent | upgrade_path |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in seed_entries:
        lines.append(
            f"| {r['ticker']} | {r['name']} | {r['base_role']} | {r['active_role']} "
            f"| {r['intent'] or '—'} | {r['upgrade_path'] or '—'} |"
        )

    # Watchlist-only entries
    wl_only = [r for r in results if not r["is_held"] and "watchlist_layer_prior" in r["role_reason"]]
    lines += [
        "",
        "---",
        "",
        f"## Watchlist Prior 分類（{len(wl_only)} 筆非持倉）",
        "",
        "| Ticker | 名稱 | base_role | active_role | 信心度 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in wl_only:
        lines.append(
            f"| {r['ticker']} | {r['name']} | {r['base_role']} | {r['active_role']} "
            f"| {r['role_confidence']} |"
        )

    # Candidate-only entries
    cand_only = [r for r in results if "snapshot_candidate_only" in r["role_reason"]]
    if cand_only:
        lines += [
            "",
            "---",
            "",
            f"## 快照候選（非 watchlist，{len(cand_only)} 筆）",
            "",
            "| Ticker | 名稱 | active_role | 信心度 | Score |",
            "| --- | --- | --- | --- | --- |",
        ]
        for r in cand_only:
            score = next(
                (x.split("_")[-1] for x in r["role_reason"] if x.startswith("score_")), "N/A"
            )
            lines.append(
                f"| {r['ticker']} | {r['name']} | {r['active_role']} "
                f"| {r['role_confidence']} | {score} |"
            )

    # Unknown / incomplete
    unknown_entries = [r for r in results if r["role_confidence"] == "UNKNOWN"]
    lines += [
        "",
        "---",
        "",
        f"## 未知 / 不完整分類（{len(unknown_entries)} 筆）",
        "",
    ]
    if unknown_entries:
        for r in unknown_entries:
            lines.append(f"- {r['ticker']} {r['name']} — {', '.join(r['role_reason'])}")
    else:
        lines.append("（無）")

    lines += [
        "",
        "---",
        "",
        "## 開放問題",
        "",
        "1. `entry_date` 全部為 UNKNOWN（待 owner 從券商後台補入後重新執行）",
        "2. `2408 南亞科` active_role=SATELLITE — owner 確認中",
        "3. 角色分類目前未接入 daily trading decisions（v0.2 規劃）",
        "4. Watchlist 外的 snapshot 候選暫以 WAVE_SWING 分類，準確度 LOW",
        "",
        "---",
        "",
        "*分析腳本：`portfolio/role_classifier.py`*",
        "*無任何持倉或交易資料被修改。*",
        f"*報告產生：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    run()
