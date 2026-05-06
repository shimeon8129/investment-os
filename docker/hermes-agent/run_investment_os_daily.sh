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
    emit("Result: NEED REVIEW")
    emit("Meaning: Some pipeline checks failed or snapshot status is not PASS.")
emit()

report_dir.mkdir(parents=True, exist_ok=True)
summary_path = report_dir / f"{snapshot.get('date')}_human_summary.md"

md = []
md.append(f"# Investment OS Human Summary - {snapshot.get('date')}")
md.append("")

section_map = {
    "Investment OS Daily Summary": "## Runtime Status",
    "Investment OS Daily Human Summary": "## Runtime Status",
    "Data Inputs": "## Data Inputs",
    "AI Cake Layer Distribution": "## AI Cake Layer Distribution",
    "Layer Detail": "## Layer Detail",
    "Portfolio Coverage": "## Portfolio Core Watch",
    "持有且在 Watchlist": "### 持有且在 Watchlist",
    "持有但不在 Watchlist": "### 持有但不在 Watchlist",
    "Watchlist 尚未持有": "### Watchlist 尚未持有",
    "Pipeline Checks": "## Pipeline Checks",
    "Safety": "## Safety",
    "Human Result": "## Human Result",
}

for line in summary_lines:
    clean = line.rstrip()

    if not clean.strip():
        continue

    stripped = clean.strip()

    # Skip separator bars only
    if set(stripped) <= {"=", "-"} and len(stripped) >= 3:
        continue

    # Major sections
    if stripped in section_map:
        md.append("")
        md.append(section_map[stripped])
        md.append("")
        continue

    # Layer subsection
    if stripped.startswith("[") and stripped.endswith("]"):
        md.append("")
        md.append(f"### {stripped}")
        md.append("")
        continue

    # Notes
    if stripped.startswith("note:"):
        md.append(f"  - {stripped}")
        continue

    # Existing bullet rows
    if stripped.startswith("- "):
        md.append(stripped)
        continue

    # Key/value rows
    if ":" in stripped:
        key, value = stripped.split(":", 1)
        md.append(f"- **{key.strip()}**: {value.strip()}")
        continue

    # Default line
    md.append(f"- {stripped}")

md.append("")
md.append("## Source Files")
md.append("")
md.append(f"- Watchlist: `{watchlist_path}`")
md.append(f"- Signal snapshot: `{snapshot_path}`")
md.append(f"- Holdings: `{holdings_path}`")
md.append(f"- Runtime log: `{log_path}`")
md.append("")

summary_path.write_text("\n".join(md), encoding="utf-8")
emit(f"Human summary markdown written: {summary_path}")
PY

REPORT_FILE="$(ls -t "$BASE_DIR"/reports/daily/*_daily_report.md 2>/dev/null | head -1 || true)"
HUMAN_SUMMARY="$(ls -t "$BASE_DIR"/reports/daily/*_human_summary.md 2>/dev/null | head -1 || true)"

echo
echo "Output Files"
echo "------------------------------------------------------------"
echo "Watchlist      : $WATCHLIST"
echo "Signal snapshot: $SNAPSHOT"
echo "Runtime log    : $LOG_FILE"
echo "Daily report   : ${REPORT_FILE:-Not found}"
echo "Human summary  : ${HUMAN_SUMMARY:-Not found}"
echo
echo "============================================================"
echo "  Done"
echo "============================================================"
echo
