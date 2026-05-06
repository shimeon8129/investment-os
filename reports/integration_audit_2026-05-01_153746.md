# Investment OS Integration Audit

Generated at: 2026-05-01 15:37:46

## 1. Runtime Files

agents/ai_safe.py
agents/claude_agent.py
agents/gemini_agent.py
agents/gpt_agent.py
agents/groq_agent.py
.claude/settings.local.json
config/settings.py
controller/main.py
data/candidates.json
data/candidates_smoke_test.json
data/chips/2026-04-29.json
data/chips/latest.json
data/decision.json
data/final_narrative.json
data/master/ai_watchlist_source.csv
data/master/tw_ticker_master.json
data/narrative_daily/2026-04-29.json
data/narrative_daily/latest.json
data/narrative_raw/claude.json
data/narrative_raw/gemini.json
data/narrative_raw/latest.json
data/narrative_raw/perplexity.json
data_node/fetch_news.py
data_node/fetch_tw.py
data_node/fetch_us.py
data_node/__init__.py
data_node/loader.py
data_node/sources/finmind.py
data_node/sources/news_api.py
data_node/sources/yfinance.py
data/portfolio/current_holdings.json
data/processed/signal_snapshot.json
data/raw_news.json
data/ready_tracker.json
data/trade_log.json
data/universe_tw.csv
data/universe_us.csv
data/watchlist.json
decision/decision_engine.py
decision/entry_engine.py
decision/entry_lock.py
decision/entry_tracker.py
decision/lock.py
decision/market.py
decision/mode.py
decision/position_lock.py
decision/ready_predictor.py
decision/risk_lock.py
decision/risk.py
docker/hermes-agent/run_investment_os_daily.sh
docs/CANDIDATE_REVIEW_20260426.md
docs/CANDIDATE_REVIEW_SMOKE_TEST.md
docs/CLAUDE_CANDIDATE_REVIEW_REPORT_20260426.md
docs/CLAUDE_DAILY_DECISION_DASHBOARD_REPORT_20260426.md
docs/CLAUDE_HOTFIX_6830_NAME_REPORT_20260426.md
docs/CLAUDE_PORTFOLIO_CANDIDATE_REVIEW_REPORT_20260426.md
docs/CLAUDE_PORTFOLIO_UPDATE_REPORT_20260426.md
docs/CLAUDE_TICKER_MASTER_SCHEMA_ADAPTER_REPORT_20260426.md
docs/CLAUDE_UPDATE_REPORT_20260426.md
docs/DAILY_DECISION_DASHBOARD_20260426.md
docs/DAILY_DECISION_DASHBOARD_20260501.md
docs/DAILY_DECISION_DASHBOARD_SMOKE_TEST.md
docs/PORTFOLIO_CANDIDATE_REVIEW_20260426.md
docs/PORTFOLIO_CANDIDATE_REVIEW_SMOKE_TEST.md
execution/broker.py
execution/exit.py
execution/notifier.py
execution/portfolio_dashboard.py
execution/portfolio.py
execution/risk.py
execution/trade_log_writer.py
execution/trade.py
feedback/performance.py
feedback/review.py
feedback/trade_log.py
jobs/daily_run.py
metadata/__init__.py
metadata/ticker_master.py
pipeline/chips_loader.py
pipeline/main_backup.py
pipeline/main.py
pipeline/narrative_loader.py
pipeline/news_heat_loader.py
pipeline/ranking_engine.py
portfolio/broker_valuation.py
portfolio/holdings_loader.py
portfolio/__init__.py
portfolio/valuation_report.py
processing/ai_interpret.py
processing/features.py
processing/__init__.py
processing/structuring.py
processing/transform.py
PROJECT_SNAPSHOT_2026-03-21.md
README.md
reporting/candidate_review.py
reporting/daily_decision_dashboard.py
reporting/__init__.py
reporting/portfolio_candidate_review.py
reports/daily/2026-05-01_daily_report.md
reports/daily/2026-05-01_human_summary.md
reports/integration_audit_2026-05-01_153746.md
scanner/alpha.py
scanner/basic_scanner.py
scanner/breakout_scan.py
scanner/minervini_scanner.py
scanner/pre_scanner.py
scanner/ranking.py
scanner/universe.py
scripts/run_daily.sh
signal_engine/breakout.py
signal_engine/entry.py
signal_engine/gear_shift.py
signal_engine/inference.py
signal_engine/__init__.py
signal_engine/reversal.py
signal_engine/rotation.py
steps/auto_narrative.py
steps/classify_roles.py
steps/consensus.py
steps/fetch_chips.py
steps/fetch_news_heat.py
steps/generate_prompt.py
steps/input_narrative.py
steps/narrative.py
steps/theme_leader.py
tests/__init__.py
tests/smoke_broker_valuation.py
tests/smoke_candidate_review.py
tests/smoke_chips.py
tests/smoke_daily_decision_dashboard.py
tests/smoke_minervini_scanner.py
tests/smoke_narrative_ranking.py
tests/smoke_news_heat.py
tests/smoke_portfolio_candidate_review.py
tests/smoke_portfolio_holdings.py
tests/smoke_ticker_master.py
tests/smoke_tw_scanner.py
tests/test_data.py
tests/test_pipeline.py
tools/build_watchlist.py

## 2. Main Entrypoints

### jobs/daily_run.py
```text
#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
REPORT_DIR = ROOT / "reports" / "daily"
PROCESSED_DIR = ROOT / "data" / "processed"

LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

log_file = LOG_DIR / "daily_run.log"
report_file = REPORT_DIR / f"{today}_daily_report.md"
snapshot_file = PROCESSED_DIR / "signal_snapshot.json"

def log(msg: str) -> None:
    line = f"[{now}] {msg}"
    print(line)
    with log_file.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"[WARN] Failed to read {path}: {e}")
        return fallback

def run_module_or_script(label: str, command: list[str]) -> dict:
    log(f"[RUN] {label}: {' '.join(command)}")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    try:
        p = subprocess.run(
            command,
            cwd=str(ROOT),
            env=env,
            text=True,
            capture_output=True,
            timeout=90,
        )
        result = {
            "label": label,
            "command": command,
            "returncode": p.returncode,
            "stdout": p.stdout[-4000:],
            "stderr": p.stderr[-4000:],
            "status": "PASS" if p.returncode == 0 else "FAIL",
        }
        log(f"[{result['status']}] {label}")
        if p.stderr:
            log(f"[STDERR] {label}: {p.stderr[-1000:]}")
        return result
    except Exception as e:
        log(f"[FAIL] {label}: {e}")
        return {
            "label": label,
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(e),
            "status": "FAIL",
        }

def main() -> int:
    log("=== Investment OS daily_run start ===")

    watchlist = read_json(ROOT / "data" / "watchlist.json", fallback={})
    holdings = read_json(ROOT / "data" / "portfolio" / "current_holdings.json", fallback={})

    checks = []

    if (ROOT / "reporting" / "daily_decision_dashboard.py").exists():
        checks.append(
            run_module_or_script(
                "daily_decision_dashboard",
                [sys.executable, "-m", "reporting.daily_decision_dashboard"],
            )
        )
    else:
        log("[WARN] reporting/daily_decision_dashboard.py not found")

    if (ROOT / "tests" / "smoke_daily_decision_dashboard.py").exists():
        checks.append(
            run_module_or_script(
                "smoke_daily_decision_dashboard",
                [sys.executable, "tests/smoke_daily_decision_dashboard.py"],
            )
        )

    if (ROOT / "tests" / "smoke_portfolio_holdings.py").exists():
        checks.append(
            run_module_or_script(
                "smoke_portfolio_holdings",
                [sys.executable, "tests/smoke_portfolio_holdings.py"],
            )
        )

    snapshot = {
        "date": today,
        "generated_at": now,
        "runtime": "Investment OS v0.2 bootstrap",
        "watchlist_loaded": bool(watchlist),
        "watchlist_count": len(watchlist.get("tickers", [])) if isinstance(watchlist, dict) else 0,
        "holdings_loaded": bool(holdings),
        "holdings_count": len(holdings.get("holdings", [])) if isinstance(holdings, dict) else 0,
        "checks": checks,
        "status": "PASS" if all(c.get("status") == "PASS" for c in checks) else "PARTIAL",
        "safety": {
            "broker_login": False,
            "auto_trade": False,
            "advisory_only": True,
        },
    }

    snapshot_file.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report_lines = [
        f"# Investment OS Daily Report - {today}",
        "",
        f"Generated at: {now}",
        "",
        "## Runtime Status",
        "",
        f"- Status: {snapshot['status']}",
        f"- Watchlist loaded: {snapshot['watchlist_loaded']}",
        f"- Watchlist count: {snapshot['watchlist_count']}",
        f"- Holdings loaded: {snapshot['holdings_loaded']}",
        f"- Holdings count: {snapshot['holdings_count']}",
        "",
        "## Checks",
        "",
    ]

    for c in checks:
        report_lines.append(f"### {c['label']}")
        report_lines.append("")
        report_lines.append(f"- Status: {c['status']}")
        report_lines.append(f"- Return code: {c['returncode']}")
        if c.get("stderr"):
            report_lines.append("")
            report_lines.append("```text")
            report_lines.append(c["stderr"][-1500:])
            report_lines.append("```")
        report_lines.append("")

    report_lines.extend([
        "## Safety",
        "",
        "- Broker login: disabled",
        "- Auto trading: disabled",
        "- Advisory only: true",
        "",
        "## Output Files",
        "",
        f"- `{snapshot_file}`",
        f"- `{report_file}`",
        f"- `{log_file}`",
        "",
    ])

    report_file.write_text("\n".join(report_lines), encoding="utf-8")

    log(f"[WRITE] {snapshot_file}")
    log(f"[WRITE] {report_file}")
    log("=== Investment OS daily_run done ===")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

### docker/hermes-agent/run_investment_os_daily.sh
```text
#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/home/shimeon/investment_os"
COMPOSE_DIR="$BASE_DIR/docker/hermes-agent"
SNAPSHOT="$BASE_DIR/data/processed/signal_snapshot.json"
WATCHLIST="$BASE_DIR/data/watchlist.json"
HOLDINGS="$BASE_DIR/data/portfolio/current_holdings.json"
LOG_FILE="$BASE_DIR/logs/daily_run.log"

cd "$COMPOSE_DIR"

echo
echo "============================================================"
echo "  Investment OS Daily Runner"
echo "============================================================"
echo "Run time : $(date '+%Y-%m-%d %H:%M:%S')"
echo "Runner   : Hermes Docker Container"
echo "Mode     : Advisory only / No broker login / No auto-trade"
echo "============================================================"
echo

echo "[1/3] Build watchlist from editable source..."
docker compose exec hermes sh -lc 'cd /workspace/investment_os && python3 tools/build_watchlist.py'

echo
echo "[2/3] Run daily pipeline..."
docker compose exec hermes sh -lc 'cd /workspace/investment_os && bash scripts/run_daily.sh'

echo
echo "[3/3] Human readable summary..."
echo

export BASE_DIR SNAPSHOT WATCHLIST HOLDINGS LOG_FILE

python3 - <<'PY'
import json
from collections import Counter, defaultdict
from pathlib import Path
import re

snapshot_path = Path(__import__('os').environ['SNAPSHOT'])
watchlist_path = Path(__import__('os').environ['WATCHLIST'])
holdings_path = Path(__import__('os').environ['HOLDINGS'])
log_path = Path(__import__('os').environ['LOG_FILE'])
report_dir = Path(__import__('os').environ['BASE_DIR']) / 'reports' / 'daily'

snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
watchlist = json.loads(watchlist_path.read_text(encoding="utf-8"))
holdings_data = json.loads(holdings_path.read_text(encoding="utf-8")) if holdings_path.exists() else {}

summary_lines = []

def emit(line=""):
    print(line)
    summary_lines.append(str(line))

def normalize_symbol(value):
    return str(value or "").replace(".TW", "").replace(".TWO", "").strip()

def get_item_symbol(item):
    if not isinstance(item, dict):
        return ""
    return normalize_symbol(
        item.get("symbol")
        or item.get("ticker")
        or item.get("code")
        or item.get("stock_id")
        or item.get("yf_symbol")
    )

tickers = watchlist.get("tickers", [])
active_tickers = [x for x in tickers if x.get("active", True)]

watchlist_by_symbol = {
    normalize_symbol(x.get("symbol")): x
    for x in active_tickers
    if x.get("symbol")
}

holding_items = holdings_data.get("holdings", []) if isinstance(holdings_data, dict) else []
holdings_by_symbol = {
    get_item_symbol(x): x
    for x in holding_items
    if get_item_symbol(x)
}

def watchlist_sort_key(symbol):
    item = watchlist_by_symbol.get(symbol, {})
    meta = item.get("meta", {})
    return (
        meta.get("layer_order", 99),
        meta.get("industry", ""),
        symbol,
    )

def holdings_sort_key(symbol):
    item = holdings_by_symbol.get(symbol, {})
    return (
        item.get("asset_type", ""),
        symbol,
    )

held_and_watchlist = sorted(
    set(holdings_by_symbol) & set(watchlist_by_symbol),
    key=watchlist_sort_key,
)
held_not_watchlist = sorted(
    set(holdings_by_symbol) - set(watchlist_by_symbol),
    key=holdings_sort_key,
)
watchlist_not_held = sorted(
    set(watchlist_by_symbol) - set(holdings_by_symbol),
    key=watchlist_sort_key,
)

layer_count = Counter()
industry_map = defaultdict(list)

for item in active_tickers:
    meta = item.get("meta", {})
    layer = meta.get("layer", "未分類")
    industry = meta.get("industry", "未分類")
    layer_count[layer] += 1
    industry_map[layer].append((industry, item.get("symbol", ""), item.get("name", "")))

layer_order = ["第一層", "第二層", "第三層", "第四層", "第五層", "未分類"]

emit("============================================================")
emit("  Investment OS Daily Summary")
emit("============================================================")
emit(f"Date          : {snapshot.get('date')}")
emit(f"Generated at  : {snapshot.get('generated_at')}")
emit(f"Runtime       : {snapshot.get('runtime')}")
emit(f"Overall status: {snapshot.get('status')}")
emit()

emit("Data Inputs")
emit("------------------------------------------------------------")
emit(f"Watchlist     : {'Loaded' if snapshot.get('watchlist_loaded') else 'Missing'}")
emit(f"Watchlist cnt : {snapshot.get('watchlist_count')}")
emit(f"Active cnt    : {len(active_tickers)}")
emit(f"Holdings      : {'Loaded' if snapshot.get('holdings_loaded') else 'Missing'}")
emit(f"Holdings cnt  : {snapshot.get('holdings_count')}")
emit()

emit("AI Cake Layer Distribution")
emit("------------------------------------------------------------")
for layer in layer_order:
    if layer_count.get(layer, 0):
        emit(f"{layer:<6} : {layer_count[layer]} 檔")
emit()

emit("Layer Detail")
emit("------------------------------------------------------------")
for layer in layer_order:
    rows = industry_map.get(layer)
    if not rows:
        continue
    emit(f"[{layer}]")
    for industry, symbol, name in rows:
        emit(f"  - {symbol} {name} | {industry}")
    emit()

emit("Portfolio Coverage")
emit("------------------------------------------------------------")
emit(f"持有且在 Watchlist : {len(held_and_watchlist)} 檔")
emit(f"持有但不在 Watchlist: {len(held_not_watchlist)} 檔")
emit(f"Watchlist 尚未持有 : {len(watchlist_not_held)} 檔")
emit()

if held_and_watchlist:
    emit("持有且在 Watchlist")
    for symbol in held_and_watchlist:
        w = watchlist_by_symbol[symbol]
        h = holdings_by_symbol[symbol]
        meta = w.get("meta", {})
        qty = h.get("quantity", h.get("shares", h.get("qty", "")))
        emit(f"  - {symbol} {w.get('name', '')} | {meta.get('layer', '未分類')} | {meta.get('industry', '未分類')} | qty={qty}")
        emit(f"    note: {meta.get('ai_note', '')}")
        emit()

if held_not_watchlist:
    emit("持有但不在 Watchlist")
    for symbol in held_not_watchlist:
        h = holdings_by_symbol[symbol]
        emit(f"  - {symbol} {h.get('name', '')} | qty={h.get('quantity', h.get('shares', h.get('qty', '')))}")
        emit()

if watchlist_not_held:
    emit("Watchlist 尚未持有")
    for symbol in watchlist_not_held:
        w = watchlist_by_symbol[symbol]
        meta = w.get("meta", {})
        emit(f"  - {symbol} {w.get('name', '')} | {meta.get('layer', '未分類')} | {meta.get('industry', '未分類')}")
        emit(f"    note: {meta.get('ai_note', '')}")
        emit()

emit("Pipeline Checks")
emit("------------------------------------------------------------")
checks = snapshot.get("checks", [])
for c in checks:
    emit(f"[{c.get('status', 'UNKNOWN'):<7}] {c.get('label')}  returncode={c.get('returncode')}")
emit()

emit("Safety")
emit("------------------------------------------------------------")
safety = snapshot.get("safety", {})
emit(f"Broker login  : {safety.get('broker_login', False)}")
emit(f"Auto trading  : {safety.get('auto_trade', False)}")
emit(f"Advisory only : {safety.get('advisory_only', True)}")
emit()

emit("Human Result")
emit("------------------------------------------------------------")
failed = [c for c in checks if c.get("status") != "PASS"]
if snapshot.get("status") == "PASS" and not failed:
    emit("Result: PASS")
    emit("Meaning: Runtime, watchlist build, and smoke checks completed.")
else:
```

### reporting/daily_decision_dashboard.py
```text
from pathlib import Path
import json
from datetime import datetime

from portfolio.holdings_loader import load_current_holdings
from metadata.ticker_master import (
    load_ticker_master,
    normalize_ticker,
    resolve_canonical_name,
    resolve_asset_type,
)
from reporting.candidate_review import (
    find_existing_candidates_file,
    normalize_candidates,
    adapt_candidate_schema,
)
from reporting.portfolio_candidate_review import build_review_rows


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_HOLDINGS_PATH = PROJECT_ROOT / "data" / "portfolio" / "current_holdings.json"
DEFAULT_REPORT_PATH = (
    PROJECT_ROOT
    / "docs"
    / f"DAILY_DECISION_DASHBOARD_{datetime.now().strftime('%Y%m%d')}.md"
)


def _load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_value(value, default="-"):
    if value is None:
        return default
    if isinstance(value, float):
        return round(value, 4)
    return value


def load_candidates(candidate_path=None):
    if candidate_path is None:
        candidate_path = find_existing_candidates_file()
    else:
        candidate_path = Path(candidate_path)

    ticker_master = load_ticker_master()
    raw_data = _load_json(candidate_path)
    raw_candidates = normalize_candidates(raw_data)

    candidates = [
        adapt_candidate_schema(row, ticker_master=ticker_master)
        for row in raw_candidates
    ]

    return candidate_path, candidates


def load_holdings(holdings_path=DEFAULT_HOLDINGS_PATH):
    holdings_path = Path(holdings_path)
    data = load_current_holdings(holdings_path)

    ticker_master = load_ticker_master()
    holdings = []

    for item in data.get("holdings", []):
        ticker = normalize_ticker(item.get("ticker"))
        name = resolve_canonical_name(
            ticker,
            fallback_name=item.get("name"),
            master=ticker_master,
        )
        asset_type = resolve_asset_type(
            ticker,
            fallback_asset_type=item.get("asset_type"),
            master=ticker_master,
        )

        holdings.append({
            **item,
            "ticker": ticker,
            "name": name,
            "asset_type": asset_type,
        })

    return holdings_path, data, holdings


def sort_candidates(candidates: list) -> list:
    def score_key(row: dict):
        score = row.get("scanner_score")
        if isinstance(score, (int, float)):
            return score
        return -999

    return sorted(candidates, key=score_key, reverse=True)


def build_market_state_section(candidates: list) -> str:
    """
    Dashboard v0 does not infer true market regime.
    It only summarizes candidate signal distribution.
    """
    signal_counts = {}

    for row in candidates:
        signal = str(row.get("signal", "UNKNOWN"))
        signal_counts[signal] = signal_counts.get(signal, 0) + 1

    lines = [
        "## 1. Market / Signal State",
        "",
        "Dashboard v0 does not make a new market regime decision.",
        "It summarizes current candidate output only.",
        "",
        "### Candidate Signal Counts",
        "",
    ]

    if signal_counts:
        for signal, count in sorted(signal_counts.items()):
            lines.append(f"- {signal}: {count}")
    else:
        lines.append("- No candidates found")

    return "\n".join(lines)


def build_top_candidates_section(candidates: list, top_n: int = 10) -> str:
    rows = sort_candidates(candidates)[:top_n]

    headers = [
        "rank",
        "ticker",
        "name",
        "asset_type",
        "close",
        "scanner_score",
        "signal",
        "raw_score",
        "raw_level",
        "raw_price",
    ]

    lines = [
        "## 2. Top Candidates",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for idx, row in enumerate(rows, start=1):
        values = [
            idx,
            safe_value(row.get("ticker")),
            safe_value(row.get("name")),
            safe_value(row.get("asset_type")),
            safe_value(row.get("close")),
            safe_value(row.get("scanner_score")),
            safe_value(row.get("signal")),
            safe_value(row.get("raw_score")),
            safe_value(row.get("raw_level")),
            safe_value(row.get("raw_price")),
        ]

        values = [str(v).replace("|", "/") for v in values]
        lines.append("| " + " | ".join(values) + " |")

    if not rows:
        lines.append("")
        lines.append("No candidate data available.")

    return "\n".join(lines)


def build_current_holdings_section(holdings_data: dict, holdings: list) -> str:
    headers = [
        "ticker",
        "name",
        "shares",
        "asset_type",
        "market",
    ]

    lines = [
        "## 3. Current Holdings",
        "",
        f"- Holdings as_of: `{holdings_data.get('as_of', '-')}`",
        f"- Currency: `{holdings_data.get('currency', '-')}`",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in holdings:
        values = [
            safe_value(row.get("ticker")),
            safe_value(row.get("name")),
            safe_value(row.get("shares")),
            safe_value(row.get("asset_type")),
            safe_value(row.get("market")),
        ]

        values = [str(v).replace("|", "/") for v in values]
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)


def build_portfolio_candidate_sections(review_rows: list) -> str:
    buckets = {
        "HELD_AND_CANDIDATE": [],
        "HELD_NOT_CANDIDATE": [],
        "CANDIDATE_NOT_HELD": [],
    }

    for row in review_rows:
        status = row.get("position_status")
```

### decision/decision_engine.py
```text
# =========================================================
# decision/decision_engine.py
# FINAL VERSION（含 Entry + Lock）
# =========================================================

import json
import os

from data_node.loader import load_price_data
from decision.entry_engine import generate_entry_signal
from decision.entry_lock import apply_entry_lock


# =========================
# 載入 candidates（Scanner 輸出）
# =========================
def load_candidates():

    path = "data/candidates.json"

    if not os.path.exists(path):
        print("❌ candidates.json 不存在")
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


# =========================
# 載入 narrative 共識
# =========================
def load_narrative_map():

    path = "data/final_narrative.json"

    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {d["ticker"]: d for d in data}


# =========================
# 主流程
# =========================
def run_decision():

    print("🚀 Running Decision Engine...")

    # =========================================
    # 1️⃣ Load Candidates + Narrative
    # =========================================
    candidates = load_candidates()

    if not candidates:
        print("❌ 無 candidates")
        return

    narrative_map = load_narrative_map()

    if narrative_map:
        print(f"\n📖 Narrative filter active — {len(narrative_map)} STRONG tickers")
        candidates = [c for c in candidates if c["ticker"] in narrative_map]
        print(f"✅ Filtered to {len(candidates)} narrative-confirmed candidates\n")

    tickers = [c["ticker"] for c in candidates]
    name_map = {c["ticker"]: c.get("name", c["ticker"]) for c in candidates}

    # =========================================
    # 2️⃣ Load Market Data
    # =========================================
    print("\n📡 Loading market data...")

    close, volume = load_price_data(tickers)

    # =========================================
    # 3️⃣ Entry Signal
    # =========================================
    entry_signals = generate_entry_signal(close, volume)
    from decision.entry_tracker import track_entry_transition

    from decision.ready_predictor import predict_ready_breakout

    ready_prediction = predict_ready_breakout(close, volume, entry_signals)

    print("\n=== READY PREDICTION ===")

    for r in ready_prediction:
        print(f"{r['ticker']} | {r['level']} | score={r['score']} | price={r['price']}")

    transition = track_entry_transition(entry_signals)

    print("\n=== ENTRY TRANSITION ===")

    print("\n🔥 BREAKOUT (READY → BUY)")
    for t in transition["breakout"]:
        print(t)

    print("\n👀 STILL READY")
    for t in transition["still_ready"]:
        print(t)

    print("\n❌ FAILED")
    for t in transition["failed"]:
        print(t)


    print("\n=== ENTRY SIGNAL ===")
    for e in entry_signals:
        if e["signal"]:
            name = name_map.get(e["ticker"], "")
            nscore = narrative_map.get(e["ticker"], {}).get("consensus_score", "-")
            print(f"{e['ticker']} {name} | {e['signal']} | price={e['price']} | narrative={nscore}")

    # =========================================
    # 4️⃣ Entry Lock（🔥核心）
    # =========================================
    entry_decisions = apply_entry_lock(close, volume, entry_signals)

    print("\n=== ENTRY DECISION ===")
    for d in entry_decisions:
        name = name_map.get(d["ticker"], "")
        print(f"{d['ticker']} {name} | {d['decision']} | price={d['price']}")

    # =========================================
    # 5️⃣ 分類
    # =========================================
    buy_list = []
    watch_list = []

    for d in entry_decisions:
        ticker = d["ticker"]
        if ticker in narrative_map:
            d["narrative_score"] = narrative_map[ticker]["consensus_score"]
            d["narrative_strength"] = narrative_map[ticker]["strength"]

        if d["decision"] == "BUY":
            buy_list.append(d)

        elif d["decision"] == "BUY_PARTIAL":
            watch_list.append(d)

    # sort by narrative score
    buy_list.sort(key=lambda x: x.get("narrative_score", 0), reverse=True)
    watch_list.sort(key=lambda x: x.get("narrative_score", 0), reverse=True)

    # =========================================
    # 6️⃣ 輸出 JSON
    # =========================================
    result = {
        "buy": buy_list,
        "watch": watch_list
    }

    os.makedirs("data", exist_ok=True)

    with open("data/decision.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n✅ decision.json 已產生")

    # =========================================
    # 7️⃣ 顯示結果
    # =========================================
    print("\n=== BUY LIST ===")
    for b in buy_list:
        name = name_map.get(b["ticker"], "")
        nscore = b.get("narrative_score", "-")
        print(f"{b['ticker']} {name} | price={b['price']} | narrative={nscore}")

    print("\n=== WATCH LIST ===")
    for w in watch_list:
        name = name_map.get(w["ticker"], "")
        nscore = w.get("narrative_score", "-")
        print(f"{w['ticker']} {name} | price={w['price']} | narrative={nscore}")


# =========================
# 主程式
# =========================
if __name__ == "__main__":

    run_decision()
```

### pipeline/main.py
```text
# pipeline/main.py

import sys
import os

# === PATH SETUP ===
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# === DATA ===
from scanner.universe import get_tw_universe, get_us_universe
from scanner.basic_scanner import scan_candidates
from scanner.minervini_scanner import build_minervini_map, scan_minervini_candidates
from data_node.loader import load_price_data

# === RANKING===
from pipeline.ranking_engine import rank_stocks, print_top_picks
from pipeline.narrative_loader import load_narrative_map
from pipeline.news_heat_loader import load_news_heat_map
from pipeline.chips_loader import load_chips_map

# === PROCESSING ===
from processing.features import compute_features

# === SIGNAL ===
from signal_engine.entry import generate_entry_signal

# === DECISION ===
from execution.trade import execute_trade

# === EXIT ===
from execution.exit import check_exit

# === PORTFOLIO + LOG ===
from execution.portfolio import load_portfolio
from execution.trade_log_writer import write_trade_log

# === MARKET ===
from decision.market import market_filter

# === LOCK ===
from decision.lock import apply_market_lock
from decision.position_lock import apply_position_lock
from decision.risk_lock import apply_risk_lock

# === FEEDBACK ===
from feedback.performance import analyze_performance

# === DASHBOARD ===
from execution.portfolio_dashboard import build_daily_dashboard

# === DEBUG ===
print("FILE LOADED")

# =========================================
# 🧠 MAIN PIPELINE
# =========================================

def run_pipeline():

    print("\n==============================")
    print("🚀 Investment OS Running")
    print("==============================")

    # =========================================
    # 🟦 1. Universe
    # =========================================

    tw_universe = get_tw_universe()
    us_universe = get_us_universe()

    tw_tickers = tw_universe["ticker"].tolist()
    us_tickers = us_universe["ticker"].tolist()

    # =========================================
    # 🟨 2. Market Engine（US）
    # =========================================

    us_close, us_volume = load_price_data(us_tickers)

    global_score = us_close.pct_change().iloc[-1].mean()
    market_state = market_filter(global_score)

    print("\n=== MARKET ===")
    print(f"State: {market_state} | Score: {round(global_score, 4)}")

    # =========================================
    # 🟩 3. TW Data
    # =========================================

    close, volume = load_price_data(tw_tickers, period="2y")
    features = compute_features(close, volume)

    # =========================================
    # 🔍 3.5 SCANNER（🔥補回來）
    # =========================================

    print("\n=== SCANNER ===")

    candidates = scan_candidates(close, volume, features)

    # 防呆（避免 None）
    if candidates is None:
        print("⚠️ Scanner returned None")
        candidates = []

    # 取前10
    top_candidates = candidates[:10]

    # 給 Ranking 用
    scanner_results = {}

    for c in top_candidates:

        ticker = c["ticker"]
        scanner_results[ticker] = c["score"]

        # 🔥 加名稱
        row = tw_universe[tw_universe["ticker"] == ticker]
        name = row["name"].values[0] if not row.empty else ""

        tag = ""

        if c["level"] == "ATTACK":
            tag = "🔥ATTACK"
        elif c["level"] == "READY":
            tag = "⚡️READY"
        else:
            tag = "👀EARLY"


        print(f"{ticker} {name} → Score: {c['score']} | {c['level']} {tag} | Price: {c['price']}")


    # =========================================
    # 🔍 4. Signal（🔥整合 READY 升級版）
    # =========================================

    # 👉 從 Scanner 拿 ticker（避免抓不到資料）
    candidate_tickers = [
        c["ticker"] for c in top_candidates
        if c.get("ticker") in close.columns
    ]

    print("\n=== SIGNAL ===")

    # 👉 建立 scanner map（🔥關鍵）
    candidate_info = {c["ticker"]: c for c in top_candidates}

    # 👉 防止空資料 crash
    if not candidate_tickers:
        print("No valid candidates")
        signals = {}
    else:
        # 👉 過濾資料
        filtered_close = close[candidate_tickers]
        filtered_volume = volume[candidate_tickers]

        # 👉 跑 Signal（🔥多傳一個參數）
        signals = generate_entry_signal(
            filtered_close,
            filtered_volume,
            features,
            candidate_info   # 🔥 關鍵在這
        )

    # 👉 收集結果
    signal_results = []

    for c in top_candidates:
        ticker = c["ticker"]

        row = tw_universe[tw_universe["ticker"] == ticker]
        name = row["name"].values[0] if not row.empty else ""

        sig = signals.get(ticker, "")

        if sig:
            print(f"{ticker} {name} → {sig}")

            signal_results.append({
                "ticker": ticker,
                "signal": sig,
                "level": c["level"]
            })


    # =========================================
    # 🧠 RANKING ENGINE（🔥新增）
    # =========================================

    name_map = dict(zip(tw_universe["ticker"], tw_universe["name"]))
    sector_map = dict(zip(tw_universe["ticker"], tw_universe["sector"]))

    ranked = rank_stocks(
        signal_results,
        scanner_results,
        sector_map,
        name_map
    )

    print_top_picks(ranked, top_n=3)

# ==========================================================
# 🔄 5. 整合入 main.py 的方式
# ==========================================================


# pipeline/main.py（修復版 - 只改 DECISION 段落）
# 
# 問題：decisions 沒有被正確初始化
# 解決方案：先檢查 ranked 是否為空，確保 decisions 一定會被創建
# ───────────────────────────────────────────────────────

import sys
import os

# === PATH SETUP ===
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# === DATA ===
```

### controller/main.py
```text
# =========================================================
# controller/main.py
# Interactive Control Layer v1
# =========================================================

import subprocess

def run_command(cmd):
    try:
        full_cmd = f"PYTHONPATH=. {cmd}"
        subprocess.run(full_cmd, shell=True)
#       subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ Error running:", cmd)


def choose_pool():
    print("\nSelect Pool:")
    print("1 Universe Pool")
    print("2 Watchlist Pool")

    choice = input("Enter (1/2): ")

    if choice == "1":
        return "universe"
    elif choice == "2":
        return "watchlist"
    else:
        print("Invalid choice, default = universe")
        return "universe"


def ask_yes_no(question):
    ans = input(f"{question} (y/n): ").lower()
    return ans == "y"


def main():

    print("🚀 Interactive Investment OS")

    # Step 1: Pool selection
    pool = choose_pool()
    print(f"✅ Selected pool: {pool}")

    # Step 2: Scanner
    if ask_yes_no("Run Scanner?"):
        print("📡 Running Scanner...")
        run_command(f"python3 scanner/basic_scanner.py {pool}")
    else:
        print("⏭ Skip Scanner")

    # Step 3: AI Narrative
    if ask_yes_no("Run AI Narrative input?"):
        print("🧠 Input AI Narrative...")
        run_command("PYTHONPATH=. python3 steps/input_narrative.py")
    else:
        print("⏭ Skip AI")

    # Step 4: Consensus
    if ask_yes_no("Run Consensus?"):
        print("🤝 Running Consensus...")
        run_command("PYTHONPATH=. python3 steps/consensus.py")
    else:
        print("⏭ Skip Consensus")

    # Step 5: Decision
    if ask_yes_no("Run Decision Engine?"):
        print("📊 Running Decision Engine...")
        run_command("PYTHONPATH=. python3 decision/decision_engine.py")
    else:
        print("⏭ Skip Decision")

    print("\n✅ Flow Completed")


if __name__ == "__main__":
    main()
```

## 3. Existing Data Files

### data/watchlist.json
-rw-rw-r-- 1 shimeon shimeon 8.8K May  1 15:25 /home/shimeon/investment_os/data/watchlist.json
```json
{
  "version": "0.4",
  "name": "AI Investment OS Watchlist",
  "market": "TW",
  "currency": "TWD",
  "updated_at": "2026-05-01 07:25:28",
  "editable_source": "data/master/ai_watchlist_source.csv",
  "schema": {
    "machine_fields": [
      "symbol",
      "name",
      "yf_symbol",
      "active"
    ],
    "annotation_fields": [
      "meta.layer",
      "meta.industry",
      "meta.ai_note"
    ]
  },
  "tickers": [
    {
      "symbol": "2454",
      "name": "聯發科",
      "yf_symbol": "2454.TW",
      "active": true,
      "meta": {
        "layer": "第一層",
        "layer_order": 1,
        "industry": "ASIC/IC 設計",
        "ai_note": "跨足雲端大廠 (CSP) 自研晶片，AI 邊緣運算指標。"
      }
    },
    {
      "symbol": "6187",
      "name": "萬潤",
      "yf_symbol": "6187.TWO",
      "active": true,
      "meta": {
        "layer": "第一層",
        "layer_order": 1,
        "industry": "先進封裝設備",
        "ai_note": "CoWoS 點膠與檢測設備，台積電擴產主要受惠者。"
      }
    },
    {
      "symbol": "3711",
      "name": "日月光投控",
      "yf_symbol": "3711.TW",
      "active": true,
      "meta": {
        "layer": "第一層",
        "layer_order": 1,
        "industry": "先進封裝龍頭",
        "ai_note": "全球封測龍頭，與台積電合作異質整合封裝。"
      }
    },
    {
      "symbol": "2330",
      "name": "台積電",
      "yf_symbol": "2330.TW",
      "active": true,
      "meta": {
        "layer": "第一層",
        "layer_order": 1,
        "industry": "晶圓代工",
        "ai_note": "全球 AI 算力唯一物理核心，CoWoS 產能指標。"
      }
    },
    {
      "symbol": "6830",
      "name": "汎銓",
      "yf_symbol": "6830.TW",
      "active": true,
      "meta": {
        "layer": "第一層",
        "layer_order": 1,
        "industry": "材料分析 (MA)",
        "ai_note": "2nm/先進製程研發先行指標，確認良率門神。"
      }
    },
    {
      "symbol": "7769",
      "name": "鴻勁",
      "yf_symbol": "7769.TWO",
      "active": true,
      "meta": {
        "layer": "第一層",
        "layer_order": 1,
        "industry": "測試設備",
        "ai_note": "AI 晶片高階測試分選機 (ATC)，掌握極限溫控技術。"
      }
    },
    {
      "symbol": "3661",
      "name": "世芯-KY",
      "yf_symbol": "3661.TWO",
      "active": true,
      "meta": {
        "layer": "第一層",
        "layer_order": 1,
        "industry": "矽智財 (IP)",
        "ai_note": "高階 AI ASIC 設計龍頭，主要客戶為美系雲端廠。"
      }
    },
    {
      "symbol": "3105",
      "name": "穩懋",
      "yf_symbol": "3105.TWO",
      "active": true,
      "meta": {
        "layer": "第二層",
        "layer_order": 2,
        "industry": "二類半導體",
        "ai_note": "化合物半導體龍頭，供應光通訊 VCSEL 與感測元件。"
      }
    },
    {
      "symbol": "4979",
      "name": "華星光",
      "yf_symbol": "4979.TWO",
      "active": true,
      "meta": {
        "layer": "第二層",
        "layer_order": 2,
        "industry": "光收發模組",
        "ai_note": "800G 高速光模組，與美系網通廠連動性極強。"
      }
    },
    {
      "symbol": "3363",
      "name": "上詮",
      "yf_symbol": "3363.TWO",
      "active": true,
      "meta": {
        "layer": "第二層",
        "layer_order": 2,
        "industry": "矽光子 / CPO",
        "ai_note": "台積電 CPO 封裝體系夥伴，解決數據傳輸能耗瓶頸。"
      }
    },
    {
      "symbol": "3081",
      "name": "聯亞",
      "yf_symbol": "3081.TWO",
      "active": true,
      "meta": {
        "layer": "第二層",
        "layer_order": 2,
        "industry": "矽光子磊晶",
        "ai_note": "關鍵雷射源 (LD) 供應，矽光子理論物理層核心。"
      }
    },
    {
      "symbol": "2345",
      "name": "智邦",
      "yf_symbol": "2345.TW",
      "active": true,
      "meta": {
        "layer": "第二層",
```

### data/master/ai_watchlist_source.csv
-rw-rw-r-- 1 shimeon shimeon 2.9K May  1 14:20 /home/shimeon/investment_os/data/master/ai_watchlist_source.csv
```json
股票代號,股票名稱,蛋糕第幾層,產業類別,核心角色與 AI 關鍵觀察點,啟用
6830,汎銓,第一層,材料分析 (MA),2nm/先進製程研發先行指標，確認良率門神。,true
7769,鴻勁,第一層,測試設備,AI 晶片高階測試分選機 (ATC)，掌握極限溫控技術。,true
6187,萬潤,第一層,先進封裝設備,CoWoS 點膠與檢測設備，台積電擴產主要受惠者。,true
3711,日月光投控,第一層,先進封裝龍頭,全球封測龍頭，與台積電合作異質整合封裝。,true
2330,台積電,第一層,晶圓代工,全球 AI 算力唯一物理核心，CoWoS 產能指標。,true
2454,聯發科,第一層,ASIC/IC 設計,跨足雲端大廠 (CSP) 自研晶片，AI 邊緣運算指標。,true
3661,世芯-KY,第一層,矽智財 (IP),高階 AI ASIC 設計龍頭，主要客戶為美系雲端廠。,true
2345,智邦,第二層,高速交換器,800G/1.6T 高速交換器，AI 集群的交通部長。,true
3363,上詮,第二層,矽光子 / CPO,台積電 CPO 封裝體系夥伴，解決數據傳輸能耗瓶頸。,true
3081,聯亞,第二層,矽光子磊晶,關鍵雷射源 (LD) 供應，矽光子理論物理層核心。,true
3105,穩懋,第二層,二類半導體,化合物半導體龍頭，供應光通訊 VCSEL 與感測元件。,true
4979,華星光,第二層,光收發模組,800G 高速光模組，與美系網通廠連動性極強。,true
3017,奇鋐,第三層,散熱模組,液冷 (Cold Plate) 領頭羊，提供完整 CDU 方案。,true
3324,雙鴻,第三層,散熱模組,水冷系統整合能力強，GB200 關鍵供應商。,true
2308,台達電,第三層,電源 / 能源,伺服器高效率供電方案，全球資料中心標準配備。,true
6781,AES-KY,第三層,伺服器 BBU,AI 伺服器備援電池系統，近期市場資金熱點。,true
2059,川湖,第三層,伺服器導軌,壟斷性高毛利標的，受惠 AI 機櫃重型化趨勢。,true
6515,穎崴,第四層,記憶體介面,AI 晶片測試座 (Socket) 指標，掌握高階客測訂單。,true
3260,威剛,第四層,記憶體模組,AI PC/Phone 換機潮帶動 DDR5 與 SSD 出貨。,true
2337,旺宏,第四層,NOR Flash,伺服器與邊緣裝置韌體儲存，AI 啟動關鍵件。,true
8299,群聯,第四層,記憶體控制,引領大容量 AI SSD 解決方案與在地化運算技術。,true
2449,京元電子,第四層,封裝測試,高階 AI 晶片最終測試 (FT)，產能利用率指標。,true
2317,鴻海,第五層,系統代工 (ODM),具備最強垂直整合力，GB200 全機櫃出貨指標。,true
2382,廣達,第五層,系統代工 (ODM),與雲端三巨頭深度合作，AI 伺服器研發實力最強。,true
6669,緯穎,第五層,雲端代工 (ODM),100% 純 AI 伺服器供應商，主要客戶為 Meta/MSFT。,true
3231,緯創,第五層,GPU 系統板,掌握 GPU 加速卡與 Baseboard 代工，獲利結構改善。,true
2376,技嘉,第五層,系統品牌,二線伺服器彈性之王，散熱技術整合具優勢。,true
```

### data/portfolio/current_holdings.json
-rw-rw-r-- 1 shimeon shimeon 2.0K Apr 29 01:14 /home/shimeon/investment_os/data/portfolio/current_holdings.json
```json
{
  "as_of": "2026-04-29",
  "currency": "TWD",
  "market": "TW",
  "source": "manual_user_input",
  "holdings": [
    {
      "ticker": "009816",
      "name": "富邦台灣TOP50",
      "shares": 5000,
      "entry_price": 11.42,
      "cost_basis": 57080,
      "broker_market_value": 65750,
      "asset_type": "ETF",
      "market": "TW"
    },
    {
      "ticker": "00992A",
      "name": "主動群益台灣科技創新",
      "shares": 5000,
      "entry_price": 16.85,
      "cost_basis": 84249,
      "broker_market_value": 85200,
      "asset_type": "ETF",
      "market": "TW"
    },
    {
      "ticker": "2330",
      "name": "台積電",
      "shares": 50,
      "entry_price": 1767.5,
      "cost_basis": 88375,
      "broker_market_value": 110750,
      "asset_type": "stock",
      "market": "TW"
    },
    {
      "ticker": "2408",
      "name": "南亞科",
      "shares": 120,
      "entry_price": 236,
      "cost_basis": 28360,
      "broker_market_value": 28500,
      "asset_type": "stock",
      "market": "TW"
    },
    {
      "ticker": "2345",
      "name": "智邦",
      "shares": 55,
      "entry_price": 1830.75,
      "cost_basis": 100691,
      "broker_market_value": 126225,
      "asset_type": "stock",
      "market": "TW"
    },
    {
      "ticker": "3017",
      "name": "奇鋐",
      "shares": 20,
      "entry_price": 2803.95,
      "cost_basis": 56079,
      "broker_market_value": 55600,
      "asset_type": "stock",
      "market": "TW"
    },
    {
      "ticker": "3711",
      "name": "日月光",
      "shares": 50,
      "entry_price": 412.58,
      "cost_basis": 20629,
      "broker_market_value": 24775,
      "asset_type": "stock",
      "market": "TW"
    },
    {
      "ticker": "6830",
      "name": "汎銓",
      "shares": 20,
      "entry_price": 460,
      "cost_basis": 9200,
      "broker_market_value": 14320,
      "asset_type": "stock",
      "market": "TW"
    }
  ]
}
```

### data/candidates.json
-rw-rw-r-- 1 shimeon shimeon 3.7K Apr 29 01:31 /home/shimeon/investment_os/data/candidates.json
```json
[
  {
    "ticker": "3583.TW",
    "name": "3583.TW",
    "score": 2,
    "level": "READY",
    "price": 736.0
  },
  {
    "ticker": "6187.TWO",
    "name": "6187.TWO",
    "score": 2,
    "level": "READY",
    "price": 1080.0
  },
  {
    "ticker": "3680.TWO",
    "name": "3680.TWO",
    "score": 2,
    "level": "READY",
    "price": 449.0
  },
  {
    "ticker": "2464.TW",
    "name": "2464.TW",
    "score": 2,
    "level": "READY",
    "price": 97.0
  },
  {
    "ticker": "3711.TW",
    "name": "3711.TW",
    "score": 2,
    "level": "READY",
    "price": 495.5
  },
  {
    "ticker": "6669.TW",
    "name": "6669.TW",
    "score": 2,
    "level": "READY",
    "price": 4890.0
  },
  {
    "ticker": "2377.TW",
    "name": "2377.TW",
    "score": 2,
    "level": "READY",
    "price": 93.4000015258789
  },
  {
    "ticker": "3037.TW",
    "name": "3037.TW",
    "score": 2,
    "level": "READY",
    "price": 839.0
  },
  {
    "ticker": "3044.TW",
    "name": "3044.TW",
    "score": 2,
    "level": "READY",
    "price": 485.0
  },
  {
    "ticker": "8155.TWO",
    "name": "8155.TWO",
    "score": 2,
    "level": "READY",
    "price": 416.5
  },
  {
    "ticker": "2330.TW",
    "name": "2330.TW",
    "score": 2,
    "level": "READY",
    "price": 2265.0
  },
  {
    "ticker": "2454.TW",
    "name": "2454.TW",
    "score": 2,
    "level": "READY",
    "price": 2435.0
  },
  {
    "ticker": "2467.TW",
    "name": "2467.TW",
    "score": 1,
    "level": "EARLY",
    "price": 495.5
  },
  {
    "ticker": "6830.TW",
    "name": "6830.TW",
    "score": 1,
    "level": "EARLY",
    "price": 651.0
  },
  {
    "ticker": "6139.TW",
    "name": "6139.TW",
    "score": 1,
    "level": "EARLY",
    "price": 666.0
  },
  {
    "ticker": "2449.TW",
    "name": "2449.TW",
    "score": 1,
    "level": "EARLY",
    "price": 283.5
  },
  {
    "ticker": "6239.TW",
    "name": "6239.TW",
    "score": 1,
    "level": "EARLY",
    "price": 217.0
  },
  {
    "ticker": "6147.TWO",
    "name": "6147.TWO",
    "score": 1,
    "level": "EARLY",
    "price": 131.0
  },
  {
    "ticker": "6257.TW",
    "name": "6257.TW",
    "score": 1,
    "level": "EARLY",
    "price": 178.0
  },
  {
    "ticker": "2382.TW",
    "name": "2382.TW",
    "score": 1,
    "level": "EARLY",
    "price": 325.5
  },
  {
    "ticker": "3231.TW",
    "name": "3231.TW",
    "score": 1,
    "level": "EARLY",
    "price": 142.5
  },
  {
    "ticker": "2356.TW",
    "name": "2356.TW",
    "score": 1,
    "level": "EARLY",
    "price": 46.70000076293945
  },
  {
    "ticker": "3706.TW",
    "name": "3706.TW",
    "score": 1,
    "level": "EARLY",
```

### data/final_narrative.json
-rw-rw-r-- 1 shimeon shimeon 1.4K Apr 20 23:12 /home/shimeon/investment_os/data/final_narrative.json
```json
[
  {
    "ticker": "2330.TW",
    "name": "台積電",
    "consensus_score": 97.0,
    "consensus_count": 3,
    "strength": "STRONG"
  },
  {
    "ticker": "3711.TW",
    "name": "日月光投控",
    "consensus_score": 93.33,
    "consensus_count": 3,
    "strength": "STRONG"
  },
  {
    "ticker": "2454.TW",
    "name": "聯發科",
    "consensus_score": 91.67,
    "consensus_count": 3,
    "strength": "STRONG"
  },
  {
    "ticker": "3413.TW",
    "name": "京鼎",
    "consensus_score": 86.67,
    "consensus_count": 3,
    "strength": "STRONG"
  },
  {
    "ticker": "2356.TW",
    "name": "英業達",
    "consensus_score": 86.67,
    "consensus_count": 3,
    "strength": "STRONG"
  },
  {
    "ticker": "2449.TW",
    "name": "京元電子",
    "consensus_score": 85.0,
    "consensus_count": 3,
    "strength": "STRONG"
  },
  {
    "ticker": "2376.TW",
    "name": "技嘉",
    "consensus_score": 85.0,
    "consensus_count": 3,
    "strength": "STRONG"
  },
  {
    "ticker": "3231.TW",
    "name": "緯創",
    "consensus_score": 81.67,
    "consensus_count": 3,
    "strength": "STRONG"
  },
  {
    "ticker": "2377.TW",
    "name": "微星",
    "consensus_score": 80.0,
    "consensus_count": 3,
    "strength": "STRONG"
  },
  {
    "ticker": "3661.TW",
    "name": "世芯-KY",
    "consensus_score": 80.0,
    "consensus_count": 3,
    "strength": "STRONG"
  }
]```

### data/decision.json
-rw-rw-r-- 1 shimeon shimeon 30 Apr 20 23:14 /home/shimeon/investment_os/data/decision.json
```json
{
  "buy": [],
  "watch": []
}```

### data/processed/signal_snapshot.json
-rw-rw-r-- 1 shimeon shimeon 1.8K May  1 15:25 /home/shimeon/investment_os/data/processed/signal_snapshot.json
```json
{
  "date": "2026-05-01",
  "generated_at": "2026-05-01 07:25:28",
  "runtime": "Investment OS v0.2 bootstrap",
  "watchlist_loaded": true,
  "watchlist_count": 27,
  "holdings_loaded": true,
  "holdings_count": 8,
  "checks": [
    {
      "label": "daily_decision_dashboard",
      "command": [
        "/usr/bin/python3",
        "-m",
        "reporting.daily_decision_dashboard"
      ],
      "returncode": 0,
      "stdout": "Candidate source: /workspace/investment_os/data/candidates.json\nDaily decision dashboard written to: /workspace/investment_os/docs/DAILY_DECISION_DASHBOARD_20260501.md\n",
      "stderr": "",
      "status": "PASS"
    },
    {
      "label": "smoke_daily_decision_dashboard",
      "command": [
        "/usr/bin/python3",
        "tests/smoke_daily_decision_dashboard.py"
      ],
      "returncode": 0,
      "stdout": "Smoke dashboard generated: /workspace/investment_os/docs/DAILY_DECISION_DASHBOARD_SMOKE_TEST.md\nDaily decision dashboard smoke test passed.\n",
      "stderr": "",
      "status": "PASS"
    },
    {
      "label": "smoke_portfolio_holdings",
      "command": [
        "/usr/bin/python3",
        "tests/smoke_portfolio_holdings.py"
      ],
      "returncode": 0,
      "stdout": "As of: 2026-04-29\nCurrency: TWD\nMarket: TW\nPosition count: 8\n009816 富邦台灣TOP50 5000 ETF\n00992A 主動群益台灣科技創新 5000 ETF\n2330 台積電 50 stock\n2408 南亞科 120 stock\n2345 智邦 55 stock\n3017 奇鋐 20 stock\n3711 日月光 50 stock\n6830 汎銓 20 stock\nPortfolio holdings smoke test passed.\n",
      "stderr": "",
      "status": "PASS"
    }
  ],
  "status": "PASS",
  "safety": {
    "broker_login": false,
    "auto_trade": false,
    "advisory_only": true
  }
}```

## 4. Python Imports Map
```text
data_node/loader.py:import pandas as pd
data_node/loader.py:import yfinance as yf
decision/decision_engine.py:from data_node.loader import load_price_data
decision/decision_engine.py:from decision.entry_engine import generate_entry_signal
decision/decision_engine.py:from decision.entry_lock import apply_entry_lock
decision/decision_engine.py:    from decision.entry_tracker import track_entry_transition
decision/decision_engine.py:    from decision.ready_predictor import predict_ready_breakout
decision/decision_engine.py:import json
decision/decision_engine.py:import os
decision/entry_tracker.py:import json
decision/entry_tracker.py:import os
execution/portfolio.py:import json
execution/risk.py:import pandas as pd
execution/trade_log_writer.py:from datetime import datetime
execution/trade_log_writer.py:import json
execution/trade_log_writer.py:import os
feedback/performance.py:import json
jobs/daily_run.py:from datetime import datetime
jobs/daily_run.py:from __future__ import annotations
jobs/daily_run.py:from pathlib import Path
jobs/daily_run.py:import json
jobs/daily_run.py:import os
jobs/daily_run.py:import subprocess
jobs/daily_run.py:import sys
pipeline/chips_loader.py:import json
pipeline/chips_loader.py:import os
pipeline/main_backup.py:from data_node.loader import load_price_data
pipeline/main_backup.py:from decision.lock import apply_market_lock
pipeline/main_backup.py:from decision.market import market_filter
pipeline/main_backup.py:from decision.position_lock import apply_position_lock
pipeline/main_backup.py:from decision.risk_lock import apply_risk_lock
pipeline/main_backup.py:from execution.exit import check_exit
pipeline/main_backup.py:from execution.portfolio import load_portfolio
pipeline/main_backup.py:from execution.trade import execute_trade
pipeline/main_backup.py:from execution.trade_log_writer import write_trade_log
pipeline/main_backup.py:from feedback.performance import analyze_performance
pipeline/main_backup.py:from pipeline.ranking_engine import rank_stocks, print_top_picks
pipeline/main_backup.py:from processing.features import compute_features
pipeline/main_backup.py:from scanner.basic_scanner import scan_candidates
pipeline/main_backup.py:from scanner.universe import get_tw_universe, get_us_universe
pipeline/main_backup.py:from signal_engine.entry import generate_entry_signal
pipeline/main_backup.py:import os
pipeline/main_backup.py:import sys
pipeline/main.py:from data_node.loader import load_price_data
pipeline/main.py:from data_node.loader import load_price_data
pipeline/main.py:from decision.lock import apply_market_lock
pipeline/main.py:from decision.lock import apply_market_lock
pipeline/main.py:from decision.market import market_filter
pipeline/main.py:from decision.market import market_filter
pipeline/main.py:from decision.position_lock import apply_position_lock
pipeline/main.py:from decision.position_lock import apply_position_lock
pipeline/main.py:from decision.risk_lock import apply_risk_lock
pipeline/main.py:from execution.exit import check_exit
pipeline/main.py:from execution.exit import check_exit
pipeline/main.py:from execution.portfolio_dashboard import build_daily_dashboard
pipeline/main.py:from execution.portfolio import load_portfolio
pipeline/main.py:from execution.portfolio import load_portfolio
pipeline/main.py:from execution.risk import apply_risk_filters
pipeline/main.py:from execution.trade import execute_trade
pipeline/main.py:from execution.trade import execute_trade
pipeline/main.py:from execution.trade_log_writer import write_trade_log
pipeline/main.py:from execution.trade_log_writer import write_trade_log
pipeline/main.py:from feedback.performance import analyze_performance
pipeline/main.py:from feedback.performance import analyze_performance
pipeline/main.py:from pipeline.chips_loader import load_chips_map
pipeline/main.py:from pipeline.chips_loader import load_chips_map
pipeline/main.py:from pipeline.narrative_loader import load_narrative_map
pipeline/main.py:from pipeline.narrative_loader import load_narrative_map
pipeline/main.py:from pipeline.news_heat_loader import load_news_heat_map
pipeline/main.py:from pipeline.news_heat_loader import load_news_heat_map
pipeline/main.py:from pipeline.ranking_engine import rank_stocks, print_top_picks
pipeline/main.py:from pipeline.ranking_engine import rank_stocks, print_top_picks
pipeline/main.py:from processing.features import compute_features
pipeline/main.py:from processing.features import compute_features
pipeline/main.py:from scanner.basic_scanner import scan_candidates
pipeline/main.py:from scanner.basic_scanner import scan_candidates
pipeline/main.py:from scanner.minervini_scanner import build_minervini_map, scan_minervini_candidates
pipeline/main.py:from scanner.minervini_scanner import build_minervini_map, scan_minervini_candidates
pipeline/main.py:from scanner.universe import get_tw_universe, get_us_universe
pipeline/main.py:from scanner.universe import get_tw_universe, get_us_universe
pipeline/main.py:from signal_engine.entry import generate_entry_signal
pipeline/main.py:from signal_engine.entry import generate_entry_signal
pipeline/main.py:import os
pipeline/main.py:import os
pipeline/main.py:import sys
pipeline/main.py:import sys
pipeline/narrative_loader.py:import json
pipeline/narrative_loader.py:import os
pipeline/news_heat_loader.py:import json
pipeline/news_heat_loader.py:import os
reporting/candidate_review.py:from datetime import datetime
reporting/candidate_review.py:from metadata.ticker_master import (
reporting/candidate_review.py:from pathlib import Path
reporting/candidate_review.py:import json
reporting/candidate_review.py:    Preserves raw values and resolves canonical name from ticker master.
reporting/daily_decision_dashboard.py:from datetime import datetime
reporting/daily_decision_dashboard.py:from metadata.ticker_master import (
reporting/daily_decision_dashboard.py:from pathlib import Path
reporting/daily_decision_dashboard.py:from portfolio.holdings_loader import load_current_holdings
reporting/daily_decision_dashboard.py:from reporting.candidate_review import (
reporting/daily_decision_dashboard.py:from reporting.portfolio_candidate_review import build_review_rows
reporting/daily_decision_dashboard.py:import json
reporting/portfolio_candidate_review.py:from datetime import datetime
reporting/portfolio_candidate_review.py:from metadata.ticker_master import (
reporting/portfolio_candidate_review.py:from pathlib import Path
reporting/portfolio_candidate_review.py:from portfolio.holdings_loader import load_current_holdings
reporting/portfolio_candidate_review.py:import json
reporting/portfolio_candidate_review.py:        "- [ ] No execution decision is made directly from this report",
scanner/basic_scanner.py:from data_node.loader import load_price_data
scanner/basic_scanner.py:# from pre_scanner import run_pre_scanner
scanner/basic_scanner.py:# from scanner.pre_scanner import run_pre_scanner
scanner/basic_scanner.py:import json
scanner/basic_scanner.py:import os
scanner/basic_scanner.py:import pandas as pd
scanner/basic_scanner.py:import sys
scanner/minervini_scanner.py:from processing.features import compute_features
scanner/pre_scanner.py:import pandas as pd
scanner/universe.py:import pandas as pd
```

## 5. Direct Module Smoke Tests

### python3 -m reporting.daily_decision_dashboard
```text
Candidate source: /home/shimeon/investment_os/data/candidates.json
Daily decision dashboard written to: /home/shimeon/investment_os/docs/DAILY_DECISION_DASHBOARD_20260501.md
exit_code=0
```

### python3 -m decision.decision_engine
```text
🚀 Running Decision Engine...

📖 Narrative filter active — 10 STRONG tickers
✅ Filtered to 10 narrative-confirmed candidates


📡 Loading market data...
✔ 3711.TW loaded
✔ 2377.TW loaded
✔ 2330.TW loaded
✔ 2454.TW loaded
✔ 2449.TW loaded
✔ 3231.TW loaded
✔ 2356.TW loaded
✔ 2376.TW loaded
✔ 3661.TW loaded
✔ 3413.TW loaded

📊 Loaded tickers (10): ['3711.TW', '2377.TW', '2330.TW', '2454.TW', '2449.TW', '3231.TW', '2356.TW', '2376.TW', '3661.TW', '3413.TW']

=== READY PREDICTION ===
2377.TW | READY_A | score=4 | price=97.69999694824219
2356.TW | READY_A | score=4 | price=45.900001525878906
2376.TW | READY_A | score=4 | price=273.0
3661.TW | READY_A | score=4 | price=4135.0
3413.TW | READY_B | score=3 | price=309.5

=== ENTRY TRANSITION ===

🔥 BREAKOUT (READY → BUY)

👀 STILL READY
3413.TW
2356.TW
2377.TW
2376.TW
3661.TW

❌ FAILED
2330.TW

=== ENTRY SIGNAL ===
2377.TW 2377.TW | READY | price=97.69999694824219 | narrative=80.0
2356.TW 2356.TW | READY | price=45.900001525878906 | narrative=86.67
2376.TW 2376.TW | READY | price=273.0 | narrative=85.0
3661.TW 3661.TW | READY | price=4135.0 | narrative=80.0
3413.TW 3413.TW | READY | price=309.5 | narrative=86.67

=== ENTRY DECISION ===

✅ decision.json 已產生

=== BUY LIST ===

=== WATCH LIST ===
exit_code=0
```

### python3 -m pipeline.main
```text
$8046.TWO: possibly delisted; no price data found  (period=2y)

1 Failed download:
['8046.TWO']: possibly delisted; no price data found  (period=2y)
$3189.TWO: possibly delisted; no price data found  (period=2y)

1 Failed download:
['3189.TWO']: possibly delisted; no price data found  (period=2y)
FILE LOADED
FILE LOADED
 ENTRY CHECK

==============================
🚀 Investment OS Running
==============================
✔ NVDA loaded
✔ SMH loaded
✔ TSM loaded
✔ ^IXIC loaded
✔ ^VIX loaded

📊 Loaded tickers (5): ['NVDA', 'SMH', 'TSM', '^IXIC', '^VIX']

=== MARKET ===
State: RANGE | Score: 0.0077
VIX: 17.02
✔ 2467.TW loaded
✔ 3131.TWO loaded
✔ 3583.TW loaded
✔ 6640.TWO loaded
✔ 6830.TW loaded
✔ 6187.TWO loaded
✔ 5443.TWO loaded
✔ 6139.TW loaded
✔ 3680.TWO loaded
✔ 2464.TW loaded
✔ 3413.TW loaded
✔ 3711.TW loaded
✔ 2449.TW loaded
✔ 6239.TW loaded
✔ 6147.TWO loaded
✔ 6257.TW loaded
✔ 2382.TW loaded
✔ 3231.TW loaded
✔ 6669.TW loaded
✔ 2356.TW loaded
✔ 3706.TW loaded
✔ 2376.TW loaded
✔ 2377.TW loaded
✔ 2313.TW loaded
✔ 3037.TW loaded
❌ 8046.TWO 無資料
❌ 3189.TWO 無資料
✔ 2368.TW loaded
✔ 3044.TW loaded
✔ 8155.TWO loaded
✔ 2330.TW loaded
✔ 2454.TW loaded
✔ 3661.TW loaded
✔ 3443.TW loaded

📊 Loaded tickers (32): ['2467.TW', '3131.TWO', '3583.TW', '6640.TWO', '6830.TW', '6187.TWO', '5443.TWO', '6139.TW', '3680.TWO', '2464.TW', '3413.TW', '3711.TW', '2449.TW', '6239.TW', '6147.TWO', '6257.TW', '2382.TW', '3231.TW', '6669.TW', '2356.TW', '3706.TW', '2376.TW', '2377.TW', '2313.TW', '3037.TW', '2368.TW', '3044.TW', '8155.TWO', '2330.TW', '2454.TW', '3661.TW', '3443.TW']

=== SCANNER ===

✅ Candidates: 32
2467.TW 志聖 → Score: 2 | Minervini: 80 | READY ⚡️READY | Price: 609.0
3583.TW 辛耘 → Score: 2 | Minervini: 80 | READY ⚡️READY | Price: 792.0
5443.TWO 均豪 → Score: 2 | Minervini: 80 | READY ⚡️READY | Price: 129.5
3680.TWO 家登 → Score: 2 | Minervini: 80 | READY ⚡️READY | Price: 537.0
2464.TW 盟立 → Score: 2 | Minervini: 80 | READY ⚡️READY | Price: 113.5
3711.TW 日月光投控 → Score: 2 | Minervini: 80 | READY ⚡️READY | Price: 478.0
2449.TW 京元電子 → Score: 2 | Minervini: 80 | READY ⚡️READY | Price: 302.5
6147.TWO 頎邦 → Score: 2 | Minervini: 80 | READY ⚡️READY | Price: 163.0
2377.TW 微星 → Score: 2 | Minervini: 10 | READY ⚡️READY | Price: 97.69999694824219
3037.TW 欣興 → Score: 2 | Minervini: 80 | READY ⚡️READY | Price: 883.0

=== SIGNAL ===
2467.TW 志聖 → BUY
3583.TW 辛耘 → BUY
5443.TWO 均豪 → BUY
3680.TWO 家登 → BUY
2464.TW 盟立 → BUY
3711.TW 日月光投控 → BUY
2449.TW 京元電子 → BUY
6147.TWO 頎邦 → BUY
2377.TW 微星 → BUY
3037.TW 欣興 → BUY

=== TOP PICKS ===

#1 3711.TW 日月光投控 (Packaging)
   Score: 241.5 | Signal: BUY | Level: READY
   Minervini: 80 | Narrative: STRONG 93.33 (count=3) | NewsHeat: 48 (news=2, sources=2) | Chips: 85 BUY (total=2,324,129)

#2 2464.TW 盟立 (Equipment)
   Score: 219.4 | Signal: BUY | Level: READY
   Minervini: 80 | Narrative: NONE 0 (count=0) | NewsHeat: 86 (news=5, sources=4) | Chips: 80 BUY (total=6,619,976)

#3 2449.TW 京元電子 (Packaging)
   Score: 213.2 | Signal: BUY | Level: READY
   Minervini: 80 | Narrative: STRONG 85.0 (count=3) | NewsHeat: 0 (news=0, sources=0) | Chips: 0 NONE (total=0)


=== DECISION ===
2464.TW 盟立 → HOLD (ALREADY_IN_POSITION)
3711.TW 日月光投控 → HOLD (ALREADY_IN_POSITION)
2449.TW 京元電子 → BUY | 倉位: 10.0% | 停損: 5.0% (REDUCED_BY_MARKET) [Risk: PASS_ADJUSTED]

=== NEW TRADES ===
2449.TW → BUY @ 302.5 | size: 10.0%

=== EXIT CHECK ===
3583.TW → EXIT_ALL
6187.TWO → EXIT_ALL
3680.TWO → EXIT_ALL
3711.TW → REDUCE
2464.TW → HOLD

=== PERFORMANCE ===
Trades: 0
Win Rate: 0.0%
Avg Return: 0.00%
Total Return: 0.00%
Max Drawdown: 0.00%

==============================
✅ Pipeline Done
==============================
exit_code=0
```

### python3 -m controller.main
```text
🚀 Interactive Investment OS

Select Pool:
1 Universe Pool
2 Watchlist Pool
Enter (1/2): exit_code=124
```

## 6. Current Reports
```text
total 12K
-rw-rw-r-- 1 shimeon shimeon  694 May  1 15:25 2026-05-01_daily_report.md
-rw-rw-r-- 1 shimeon shimeon 5.6K May  1 15:25 2026-05-01_human_summary.md
```

## 7. Current Snapshot

```json
{
  "date": "2026-05-01",
  "generated_at": "2026-05-01 07:25:28",
  "runtime": "Investment OS v0.2 bootstrap",
  "watchlist_loaded": true,
  "watchlist_count": 27,
  "holdings_loaded": true,
  "holdings_count": 8,
  "checks": [
    {
      "label": "daily_decision_dashboard",
      "command": [
        "/usr/bin/python3",
        "-m",
        "reporting.daily_decision_dashboard"
      ],
      "returncode": 0,
      "stdout": "Candidate source: /workspace/investment_os/data/candidates.json\nDaily decision dashboard written to: /workspace/investment_os/docs/DAILY_DECISION_DASHBOARD_20260501.md\n",
      "stderr": "",
      "status": "PASS"
    },
    {
      "label": "smoke_daily_decision_dashboard",
      "command": [
        "/usr/bin/python3",
        "tests/smoke_daily_decision_dashboard.py"
      ],
      "returncode": 0,
      "stdout": "Smoke dashboard generated: /workspace/investment_os/docs/DAILY_DECISION_DASHBOARD_SMOKE_TEST.md\nDaily decision dashboard smoke test passed.\n",
      "stderr": "",
      "status": "PASS"
    },
    {
      "label": "smoke_portfolio_holdings",
      "command": [
        "/usr/bin/python3",
        "tests/smoke_portfolio_holdings.py"
      ],
      "returncode": 0,
      "stdout": "As of: 2026-04-29\nCurrency: TWD\nMarket: TW\nPosition count: 8\n009816 富邦台灣TOP50 5000 ETF\n00992A 主動群益台灣科技創新 5000 ETF\n2330 台積電 50 stock\n2408 南亞科 120 stock\n2345 智邦 55 stock\n3017 奇鋐 20 stock\n3711 日月光 50 stock\n6830 汎銓 20 stock\nPortfolio holdings smoke test passed.\n",
      "stderr": "",
      "status": "PASS"
    }
  ],
  "status": "PASS",
  "safety": {
    "broker_login": false,
    "auto_trade": false,
    "advisory_only": true
  }
}```
