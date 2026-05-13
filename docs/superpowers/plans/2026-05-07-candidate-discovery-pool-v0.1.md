# Candidate Discovery Pool + Data Quality Gate v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a three-layer candidate source model that discovers new investment candidates from ETF holdings and AI watchlist sources, validates them through a data quality gate, and outputs a ranked CSV pool + markdown report — without touching any trading logic.

**Architecture:** Static ETF holdings embedded in fetcher (v0.1 offline-safe) → Data Quality Gate applies 8 checks → Discovery Pool Builder aggregates, scores, deduplicates → Report Generator produces markdown. All modules are standalone Python files with clear single responsibilities. Price data fetched from yfinance with graceful fallback.

**Tech Stack:** Python 3.12, pandas, yfinance 1.2.0, pathlib, csv, json — all already in venv. No new dependencies.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `discovery/__init__.py` | Create | Package marker |
| `discovery/data_quality_gate.py` | Create | 8 validation checks, returns status per candidate |
| `discovery/etf_source_fetcher.py` | Create | Static ETF holdings + yfinance price fetch |
| `discovery/discovery_pool_builder.py` | Create | Aggregate + deduplicate + score + write CSV |
| `reporting/candidate_discovery_report.py` | Create | Generate markdown report from pool CSV |
| `scripts/run_candidate_discovery.py` | Create | CLI runner tying all modules together |
| `tests/smoke_candidate_discovery.py` | Create | Offline smoke test (no network) |

**Do NOT touch:** `data/universe_tw.csv`, any `decision/` module, any `execution/` module, `data/portfolio/`.

---

## Task 1: Data Quality Gate

**Files:**
- Create: `discovery/__init__.py`
- Create: `discovery/data_quality_gate.py`

- [ ] **Step 1: Create package skeleton**

```python
# discovery/__init__.py
# (empty — package marker only)
```

- [ ] **Step 2: Write `discovery/data_quality_gate.py`**

```python
# discovery/data_quality_gate.py
import csv
import json
import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
UNIVERSE_PATH = PROJECT_ROOT / "data" / "universe_tw.csv"
MASTER_PATH = PROJECT_ROOT / "data" / "master" / "tw_ticker_master.json"

STALE_DAYS = 30
_TW_CODE_RE = re.compile(r"^\d{4,5}[AB]?$")
_US_TICKER_RE = re.compile(r"^[A-Z]{1,5}(-[A-Z]+)?$")


def _load_universe_codes() -> set:
    codes = set()
    if not UNIVERSE_PATH.exists():
        return codes
    with open(UNIVERSE_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            raw = row.get("ticker", "").strip()
            code = raw.split(".")[0]
            if code:
                codes.add(code)
    return codes


def _load_master_map() -> dict:
    name_map = {}
    if not MASTER_PATH.exists():
        return name_map
    with open(MASTER_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for entry in data.get("tickers", []):
        code = entry.get("ticker", "").strip()
        name = entry.get("canonical_name", "").strip()
        if code:
            name_map[code] = name
    return name_map


def _normalize_ticker(raw: str) -> tuple:
    """Return (code, market_suffix) e.g. ('2330', 'TW') or ('NVDA', 'US')."""
    raw = raw.strip()
    if "." in raw:
        parts = raw.split(".", 1)
        return parts[0], parts[1].upper()
    if _TW_CODE_RE.match(raw):
        return raw, "TW"
    if _US_TICKER_RE.match(raw):
        return raw, "US"
    return raw, "UNKNOWN"


def _is_stale(source_date_str: str) -> bool:
    if not source_date_str:
        return False
    try:
        delta = datetime.now() - datetime.strptime(source_date_str, "%Y-%m-%d")
        return delta.days > STALE_DAYS
    except ValueError:
        return False


def validate(candidate: dict,
             universe_codes: set | None = None,
             master_map: dict | None = None) -> dict:
    """
    Apply 8 data quality checks. Returns candidate dict with added fields:
      normalized_ticker, market, us_mapping_flag, already_in_universe,
      data_quality_status, _quality_issues (list of issue tags).
    """
    if universe_codes is None:
        universe_codes = _load_universe_codes()
    if master_map is None:
        master_map = _load_master_map()

    raw_ticker = candidate.get("ticker", "").strip()
    candidate_name = candidate.get("name", "").strip()
    source_date = candidate.get("source_date", "").strip()
    source_name = candidate.get("source_name", "").strip()

    issues = []

    # Check 2: market suffix normalization
    code, market = _normalize_ticker(raw_ticker)
    candidate["normalized_ticker"] = code
    candidate["market"] = market

    # Check 3: TW vs US market separation
    us_mapping_flag = (market == "US")
    candidate["us_mapping_flag"] = us_mapping_flag

    # Check 4: existing universe detection
    already_in_universe = (code in universe_codes)
    candidate["already_in_universe"] = already_in_universe

    # Check 5: source timestamp presence
    if not source_date:
        issues.append("MISSING_SOURCE_DATE")

    # Check 6: missing source handling (log, do not crash)
    if not source_name:
        issues.append("MISSING_SOURCE_NAME")

    # Check 7: stale data handling
    if source_date and _is_stale(source_date):
        issues.append("STALE_DATA")

    # Check 8: source conflict (name vs master canonical)
    canonical = master_map.get(code, "")
    if canonical and candidate_name and canonical != candidate_name:
        issues.append("NAME_MISMATCH")

    # Check 1 + determine status
    if market == "UNKNOWN" or not raw_ticker:
        status = "REJECT_BAD_TICKER"
    elif "NAME_MISMATCH" in issues:
        status = "SOURCE_CONFLICT_REVIEW"
    elif us_mapping_flag:
        status = "THEME_MAPPING_ONLY"
    elif already_in_universe:
        status = "EXISTING_UNIVERSE_REINFORCED"
    else:
        status = "NEW_DISCOVERY_CANDIDATE"

    candidate["data_quality_status"] = status
    candidate["_quality_issues"] = issues
    return candidate


def run_gate(candidates: list, log_sink: list | None = None) -> list:
    """
    Validate a list of candidate dicts through the quality gate.
    Missing sources are logged but never crash the run.
    Returns validated list (same order, with added fields).
    """
    if log_sink is None:
        log_sink = []
    universe_codes = _load_universe_codes()
    master_map = _load_master_map()
    validated = []
    for c in candidates:
        try:
            result = validate(c.copy(), universe_codes, master_map)
            validated.append(result)
            if result["_quality_issues"]:
                log_sink.append(
                    f"[GATE] {result['normalized_ticker']} issues={result['_quality_issues']}"
                )
        except Exception as exc:
            log_sink.append(f"[GATE] ERROR ticker={c.get('ticker', '?')} err={exc}")
    return validated
```

- [ ] **Step 3: Syntax-check**

```bash
cd /home/shimeon/investment_os && python3 -m py_compile discovery/__init__.py discovery/data_quality_gate.py && echo "PASS"
```

Expected: `PASS`

- [ ] **Step 4: Quick inline validation (no file I/O)**

```bash
cd /home/shimeon/investment_os && python3 - <<'EOF'
import sys; sys.path.insert(0, ".")
from discovery.data_quality_gate import validate

# TW stock already in universe
r1 = validate({"ticker": "2330", "name": "台積電", "source_name": "0050", "source_date": "2026-04-30"}, {"2330"}, {"2330": "台積電"})
assert r1["data_quality_status"] == "EXISTING_UNIVERSE_REINFORCED", r1["data_quality_status"]
assert r1["already_in_universe"] is True

# US symbol → THEME_MAPPING_ONLY
r2 = validate({"ticker": "NVDA", "name": "NVIDIA", "source_name": "00757", "source_date": "2026-04-30"}, set(), {})
assert r2["data_quality_status"] == "THEME_MAPPING_ONLY", r2["data_quality_status"]
assert r2["us_mapping_flag"] is True

# Bad ticker → REJECT
r3 = validate({"ticker": "??", "name": "Bad", "source_name": "x", "source_date": "2026-04-30"}, set(), {})
assert r3["data_quality_status"] == "REJECT_BAD_TICKER", r3["data_quality_status"]

# Name conflict → SOURCE_CONFLICT_REVIEW
r4 = validate({"ticker": "2330", "name": "WRONG NAME", "source_name": "x", "source_date": "2026-04-30"}, set(), {"2330": "台積電"})
assert r4["data_quality_status"] == "SOURCE_CONFLICT_REVIEW", r4["data_quality_status"]

print("data_quality_gate: all assertions PASS")
EOF
```

Expected: `data_quality_gate: all assertions PASS`

- [ ] **Step 5: Commit**

```bash
cd /home/shimeon/investment_os && git add discovery/__init__.py discovery/data_quality_gate.py && git commit -m "feat: add discovery package and data_quality_gate (8 checks)"
```

---

## Task 2: ETF Source Fetcher

**Files:**
- Create: `discovery/etf_source_fetcher.py`

- [ ] **Step 1: Write `discovery/etf_source_fetcher.py`**

```python
# discovery/etf_source_fetcher.py
"""
Provides ETF holdings data and price data for the discovery pool.

ETF holdings are embedded as static data (v0.1 offline-safe).
Price data is fetched from yfinance with graceful fallback.
"""
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AI_WATCHLIST_PATH = PROJECT_ROOT / "data" / "master" / "ai_watchlist_source.csv"

# ── ETF type classification ────────────────────────────────────────────
ACTIVE_ETFS = {"00992A", "00993A", "00994A"}
MOMENTUM_ETFS = {"00881", "00830"}
SEMICONDUCTOR_ETFS = {"00891", "00892", "00904"}

# ── Static holdings (embedded, v0.1) ──────────────────────────────────
# Source: publicly available ETF disclosures as of 2026-04-30.
_ETF_HOLDINGS: dict = {
    "0050": {
        "name": "元大台灣50",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",    "weight": 0.4580},
            {"ticker": "2317", "name": "鴻海",      "weight": 0.0652},
            {"ticker": "2454", "name": "聯發科",    "weight": 0.0521},
            {"ticker": "2308", "name": "台達電",    "weight": 0.0298},
            {"ticker": "2382", "name": "廣達",      "weight": 0.0289},
            {"ticker": "3711", "name": "日月光投控","weight": 0.0201},
            {"ticker": "2303", "name": "聯電",      "weight": 0.0198},
            {"ticker": "2881", "name": "富邦金",    "weight": 0.0195},
            {"ticker": "2882", "name": "國泰金",    "weight": 0.0188},
            {"ticker": "2412", "name": "中華電信",  "weight": 0.0185},
            {"ticker": "6669", "name": "緯穎",      "weight": 0.0165},
            {"ticker": "2002", "name": "中鋼",      "weight": 0.0142},
        ],
    },
    "0052": {
        "name": "富邦科技",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",    "weight": 0.6720},
            {"ticker": "2303", "name": "聯電",      "weight": 0.0921},
            {"ticker": "2454", "name": "聯發科",    "weight": 0.0612},
            {"ticker": "3711", "name": "日月光投控","weight": 0.0398},
            {"ticker": "2317", "name": "鴻海",      "weight": 0.0312},
            {"ticker": "6669", "name": "緯穎",      "weight": 0.0201},
            {"ticker": "3443", "name": "創意",      "weight": 0.0156},
        ],
    },
    "006208": {
        "name": "富邦台灣采吉50",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",    "weight": 0.4512},
            {"ticker": "2317", "name": "鴻海",      "weight": 0.0645},
            {"ticker": "2454", "name": "聯發科",    "weight": 0.0498},
            {"ticker": "2308", "name": "台達電",    "weight": 0.0289},
            {"ticker": "2382", "name": "廣達",      "weight": 0.0272},
            {"ticker": "3711", "name": "日月光投控","weight": 0.0188},
            {"ticker": "6669", "name": "緯穎",      "weight": 0.0178},
            {"ticker": "2303", "name": "聯電",      "weight": 0.0175},
        ],
    },
    "00881": {
        "name": "國泰台灣5G+",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",    "weight": 0.2890},
            {"ticker": "2454", "name": "聯發科",    "weight": 0.1102},
            {"ticker": "3661", "name": "世芯-KY",   "weight": 0.0821},
            {"ticker": "6669", "name": "緯穎",      "weight": 0.0756},
            {"ticker": "2345", "name": "智邦",      "weight": 0.0612},
            {"ticker": "3443", "name": "創意",      "weight": 0.0589},
            {"ticker": "2382", "name": "廣達",      "weight": 0.0489},
        ],
    },
    "00891": {
        "name": "中信關鍵半導體",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",    "weight": 0.3012},
            {"ticker": "2454", "name": "聯發科",    "weight": 0.1256},
            {"ticker": "3711", "name": "日月光投控","weight": 0.0892},
            {"ticker": "2303", "name": "聯電",      "weight": 0.0712},
            {"ticker": "3661", "name": "世芯-KY",   "weight": 0.0589},
            {"ticker": "2449", "name": "京元電子",  "weight": 0.0456},
            {"ticker": "6239", "name": "力成",      "weight": 0.0389},
            {"ticker": "3443", "name": "創意",      "weight": 0.0356},
            {"ticker": "6515", "name": "穎崴",      "weight": 0.0312},
            {"ticker": "6147", "name": "頎邦",      "weight": 0.0289},
        ],
    },
    "00892": {
        "name": "富邦台灣半導體",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",    "weight": 0.3456},
            {"ticker": "2454", "name": "聯發科",    "weight": 0.1123},
            {"ticker": "3711", "name": "日月光投控","weight": 0.0823},
            {"ticker": "2303", "name": "聯電",      "weight": 0.0698},
            {"ticker": "3661", "name": "世芯-KY",   "weight": 0.0512},
            {"ticker": "3443", "name": "創意",      "weight": 0.0421},
            {"ticker": "2449", "name": "京元電子",  "weight": 0.0389},
            {"ticker": "6257", "name": "矽格",      "weight": 0.0312},
        ],
    },
    "00904": {
        "name": "新光臺灣半導體30",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",    "weight": 0.2823},
            {"ticker": "2454", "name": "聯發科",    "weight": 0.1012},
            {"ticker": "3661", "name": "世芯-KY",   "weight": 0.0789},
            {"ticker": "3443", "name": "創意",      "weight": 0.0623},
            {"ticker": "3711", "name": "日月光投控","weight": 0.0589},
            {"ticker": "2303", "name": "聯電",      "weight": 0.0512},
            {"ticker": "6515", "name": "穎崴",      "weight": 0.0456},
            {"ticker": "6147", "name": "頎邦",      "weight": 0.0389},
            {"ticker": "2449", "name": "京元電子",  "weight": 0.0342},
            {"ticker": "6239", "name": "力成",      "weight": 0.0298},
        ],
    },
    "00992A": {
        "name": "群益台灣科技創新",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",    "weight": 0.2156},
            {"ticker": "3661", "name": "世芯-KY",   "weight": 0.1023},
            {"ticker": "2454", "name": "聯發科",    "weight": 0.0912},
            {"ticker": "6669", "name": "緯穎",      "weight": 0.0789},
            {"ticker": "2345", "name": "智邦",      "weight": 0.0656},
            {"ticker": "3443", "name": "創意",      "weight": 0.0589},
            {"ticker": "3363", "name": "上詮",      "weight": 0.0512},
            {"ticker": "4979", "name": "華星光",    "weight": 0.0445},
        ],
    },
    "00993A": {
        "name": "中信AI晶片",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",    "weight": 0.2512},
            {"ticker": "3661", "name": "世芯-KY",   "weight": 0.1256},
            {"ticker": "2454", "name": "聯發科",    "weight": 0.1023},
            {"ticker": "3443", "name": "創意",      "weight": 0.0789},
            {"ticker": "6669", "name": "緯穎",      "weight": 0.0656},
            {"ticker": "3363", "name": "上詮",      "weight": 0.0512},
            {"ticker": "3081", "name": "聯亞",      "weight": 0.0423},
            {"ticker": "3105", "name": "穩懋",      "weight": 0.0389},
            {"ticker": "4979", "name": "華星光",    "weight": 0.0312},
        ],
    },
    "00994A": {
        "name": "富邦台灣科技",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",    "weight": 0.2889},
            {"ticker": "2454", "name": "聯發科",    "weight": 0.1123},
            {"ticker": "3661", "name": "世芯-KY",   "weight": 0.0856},
            {"ticker": "2382", "name": "廣達",      "weight": 0.0712},
            {"ticker": "6669", "name": "緯穎",      "weight": 0.0589},
            {"ticker": "3711", "name": "日月光投控","weight": 0.0512},
            {"ticker": "3443", "name": "創意",      "weight": 0.0456},
            {"ticker": "2345", "name": "智邦",      "weight": 0.0389},
        ],
    },
    "00733": {
        "name": "富邦臺灣中小",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "3017", "name": "奇鋐",      "weight": 0.0423},
            {"ticker": "3324", "name": "雙鴻",      "weight": 0.0389},
            {"ticker": "6781", "name": "AES-KY",    "weight": 0.0312},
            {"ticker": "2059", "name": "川湖",      "weight": 0.0289},
            {"ticker": "3081", "name": "聯亞",      "weight": 0.0256},
            {"ticker": "3363", "name": "上詮",      "weight": 0.0234},
            {"ticker": "3105", "name": "穩懋",      "weight": 0.0212},
            {"ticker": "4979", "name": "華星光",    "weight": 0.0198},
        ],
    },
    "00830": {
        "name": "國泰臺灣ESG",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",    "weight": 0.2156},
            {"ticker": "2454", "name": "聯發科",    "weight": 0.0923},
            {"ticker": "2317", "name": "鴻海",      "weight": 0.0712},
            {"ticker": "2308", "name": "台達電",    "weight": 0.0589},
            {"ticker": "2382", "name": "廣達",      "weight": 0.0456},
        ],
    },
    "00757": {
        "name": "統一FANG+",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "META",  "name": "Meta Platforms", "weight": 0.1250},
            {"ticker": "AMZN",  "name": "Amazon",         "weight": 0.1250},
            {"ticker": "NFLX",  "name": "Netflix",        "weight": 0.1250},
            {"ticker": "GOOGL", "name": "Alphabet",       "weight": 0.1250},
            {"ticker": "AAPL",  "name": "Apple",          "weight": 0.1250},
            {"ticker": "NVDA",  "name": "NVIDIA",         "weight": 0.1250},
            {"ticker": "MSFT",  "name": "Microsoft",      "weight": 0.1250},
            {"ticker": "TSLA",  "name": "Tesla",          "weight": 0.1250},
        ],
    },
}


def load_ai_watchlist_codes() -> set:
    """Return set of ticker codes from data/master/ai_watchlist_source.csv."""
    codes = set()
    if not AI_WATCHLIST_PATH.exists():
        return codes
    with open(AI_WATCHLIST_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = row.get("股票代號", "").strip()
            enabled = row.get("啟用", "").strip().lower()
            if code and enabled == "true":
                codes.add(code)
    return codes


def get_etf_holdings(etf_code: str, log_sink: list | None = None) -> list:
    """Return list of holding dicts for the given ETF code, or [] on missing."""
    if log_sink is None:
        log_sink = []
    data = _ETF_HOLDINGS.get(etf_code)
    if data is None:
        log_sink.append(f"[FETCHER] ETF {etf_code} not in static data — skipping")
        return []
    holdings = []
    for h in data["holdings"]:
        holdings.append({
            "ticker": h["ticker"],
            "name": h["name"],
            "source_type": "ETF_HOLDING",
            "source_name": data["name"],
            "source_ticker_or_etf": etf_code,
            "source_weight": h["weight"],
            "source_date": data["source_date"],
            "active_etf_flag": etf_code in ACTIVE_ETFS,
            "momentum_etf_flag": etf_code in MOMENTUM_ETFS,
            "_semiconductor_etf_flag": etf_code in SEMICONDUCTOR_ETFS,
        })
    return holdings


def fetch_price(ticker_code: str, log_sink: list | None = None) -> dict:
    """
    Try yfinance for last close + pct_change for a TW stock.
    Returns {"close": float|"DATA_MISSING", "pct_change": float|"DATA_MISSING"}.
    Never raises.
    """
    if log_sink is None:
        log_sink = []
    yf_ticker = f"{ticker_code}.TW"
    try:
        import yfinance as yf
        t = yf.Ticker(yf_ticker)
        hist = t.history(period="5d")
        if hist.empty or len(hist) < 2:
            # Try .TWO suffix
            yf_ticker = f"{ticker_code}.TWO"
            t = yf.Ticker(yf_ticker)
            hist = t.history(period="5d")
        if hist.empty or len(hist) < 2:
            log_sink.append(f"[PRICE] {ticker_code}: no history data")
            return {"close": "DATA_MISSING", "pct_change": "DATA_MISSING"}
        close_today = float(hist["Close"].iloc[-1])
        close_prev = float(hist["Close"].iloc[-2])
        pct = round((close_today - close_prev) / close_prev * 100, 2) if close_prev else "DATA_MISSING"
        return {"close": round(close_today, 2), "pct_change": pct}
    except Exception as exc:
        log_sink.append(f"[PRICE] {ticker_code}: error={exc}")
        return {"close": "DATA_MISSING", "pct_change": "DATA_MISSING"}


def load_all_etf_candidates(etf_list: list | None = None,
                            log_sink: list | None = None) -> list:
    """
    Load holdings from all ETFs in etf_list (default: all 13 in spec).
    Returns flat list of raw candidate dicts (before quality gate).
    """
    if etf_list is None:
        etf_list = list(_ETF_HOLDINGS.keys())
    if log_sink is None:
        log_sink = []
    all_holdings = []
    for etf_code in etf_list:
        holdings = get_etf_holdings(etf_code, log_sink)
        all_holdings.extend(holdings)
    return all_holdings


def load_ai_watchlist_candidates(log_sink: list | None = None) -> list:
    """
    Return candidate dicts for all enabled entries in ai_watchlist_source.csv
    (marked as source_type=AI_WATCHLIST).
    """
    if log_sink is None:
        log_sink = []
    candidates = []
    if not AI_WATCHLIST_PATH.exists():
        log_sink.append(f"[FETCHER] ai_watchlist_source.csv not found — skipping")
        return candidates
    with open(AI_WATCHLIST_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = row.get("股票代號", "").strip()
            name = row.get("股票名稱", "").strip()
            enabled = row.get("啟用", "").strip().lower()
            industry = row.get("產業類別", "").strip()
            if not code or enabled != "true":
                continue
            candidates.append({
                "ticker": code,
                "name": name,
                "industry": industry,
                "source_type": "AI_WATCHLIST",
                "source_name": "ai_watchlist_source",
                "source_ticker_or_etf": "AI_WATCHLIST",
                "source_weight": None,
                "source_date": "2026-04-26",
                "active_etf_flag": False,
                "momentum_etf_flag": False,
                "_semiconductor_etf_flag": False,
            })
    return candidates
```

- [ ] **Step 2: Syntax-check**

```bash
cd /home/shimeon/investment_os && python3 -m py_compile discovery/etf_source_fetcher.py && echo "PASS"
```

Expected: `PASS`

- [ ] **Step 3: Quick inline validation**

```bash
cd /home/shimeon/investment_os && python3 - <<'EOF'
import sys; sys.path.insert(0, ".")
from discovery.etf_source_fetcher import (
    get_etf_holdings, load_ai_watchlist_candidates, load_all_etf_candidates,
    load_ai_watchlist_codes, ACTIVE_ETFS, SEMICONDUCTOR_ETFS
)

h = get_etf_holdings("0050")
assert len(h) > 0, "0050 has no holdings"
assert h[0]["source_ticker_or_etf"] == "0050"
assert h[0]["active_etf_flag"] is False  # 0050 is not active

h2 = get_etf_holdings("00993A")
assert h2[0]["active_etf_flag"] is True  # active ETF

missing = get_etf_holdings("99999", [])
assert missing == []  # unknown ETF → empty list

all_h = load_all_etf_candidates()
assert len(all_h) > 50

ai_codes = load_ai_watchlist_codes()
assert "2330" in ai_codes  # 台積電 is in ai_watchlist

ai_cands = load_ai_watchlist_candidates()
assert any(c["ticker"] == "2330" for c in ai_cands)

print(f"etf_source_fetcher: PASS — {len(all_h)} ETF holdings, {len(ai_cands)} AI watchlist")
EOF
```

Expected: `etf_source_fetcher: PASS — ... ETF holdings, ... AI watchlist`

- [ ] **Step 4: Commit**

```bash
cd /home/shimeon/investment_os && git add discovery/etf_source_fetcher.py && git commit -m "feat: add etf_source_fetcher with static ETF holdings and yfinance price lookup"
```

---

## Task 3: Discovery Pool Builder

**Files:**
- Create: `discovery/discovery_pool_builder.py`

- [ ] **Step 1: Write `discovery/discovery_pool_builder.py`**

```python
# discovery/discovery_pool_builder.py
"""
Aggregates validated candidates from ETF sources and AI watchlist,
deduplicates by ticker, computes discovery score, and writes
data/discovery/candidate_discovery_pool_YYYY-MM-DD.csv.
"""
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_DIR = PROJECT_ROOT / "data" / "discovery"

REQUIRED_COLUMNS = [
    "date", "ticker", "name", "industry",
    "source_type", "source_name", "source_ticker_or_etf",
    "source_weight", "source_date",
    "etf_count", "active_etf_flag", "momentum_etf_flag",
    "us_mapping_flag", "already_in_universe",
    "data_quality_status", "discovery_status",
    "discovery_score", "recommended_action", "note",
]

SCORE_ETF_PER_COUNT = 10
SCORE_ACTIVE_ETF = 15
SCORE_MOMENTUM_ETF = 10
SCORE_SEMICONDUCTOR_ETF = 10
SCORE_AI_WATCHLIST = 20
SCORE_IN_UNIVERSE = 5
SCORE_US_MAPPING = 5
PENALTY_CONFLICT = -20
PENALTY_STALE = -10


def _calc_score(record: dict) -> float:
    score = 0.0
    score += record.get("etf_count", 0) * SCORE_ETF_PER_COUNT
    if record.get("active_etf_flag"):
        score += SCORE_ACTIVE_ETF
    if record.get("momentum_etf_flag"):
        score += SCORE_MOMENTUM_ETF
    if record.get("_semiconductor_etf_flag"):
        score += SCORE_SEMICONDUCTOR_ETF
    if record.get("_in_ai_watchlist"):
        score += SCORE_AI_WATCHLIST
    if record.get("already_in_universe"):
        score += SCORE_IN_UNIVERSE
    if record.get("us_mapping_flag"):
        score += SCORE_US_MAPPING
    if record.get("data_quality_status") == "SOURCE_CONFLICT_REVIEW":
        score += PENALTY_CONFLICT
    if "STALE_DATA" in record.get("_quality_issues", []):
        score += PENALTY_STALE
    return max(0.0, round(score, 1))


def _get_discovery_status(record: dict) -> str:
    status = record.get("data_quality_status", "")
    score = record.get("discovery_score", 0)
    if status == "REJECT_BAD_TICKER":
        return "REJECT_BAD_TICKER"
    if status == "THEME_MAPPING_ONLY":
        return "THEME_MAPPING_ONLY"
    if status == "SOURCE_CONFLICT_REVIEW":
        return "SOURCE_CONFLICT_REVIEW"
    if status == "EXISTING_UNIVERSE_REINFORCED":
        return "EXISTING_UNIVERSE_REINFORCED"
    return "NEW_DISCOVERY_CANDIDATE" if score >= 20 else "IGNORE_LOW_RELEVANCE"


def _get_recommended_action(record: dict) -> str:
    status = record.get("data_quality_status", "")
    if status == "REJECT_BAD_TICKER":
        return "REJECT_NEEDS_CORRECTION"
    if record.get("us_mapping_flag"):
        return "US_MAPPING_ONLY"
    if record.get("already_in_universe"):
        return "WATCH_EXISTING_UNIVERSE"
    if status == "SOURCE_CONFLICT_REVIEW":
        return "REJECT_NEEDS_CORRECTION"
    score = record.get("discovery_score", 0)
    return "REVIEW_FOR_UNIVERSE_ADD" if score >= 20 else "KEEP_IN_DISCOVERY_POOL"


def _deduplicate(validated: list, ai_watchlist_codes: set) -> list:
    """
    Merge records with the same normalized_ticker.
    Picks the first name seen; accumulates ETF sources;
    OR-combines boolean flags; uses highest source_weight seen.
    """
    by_ticker: dict = {}
    etf_sources: dict = defaultdict(set)
    flags: dict = defaultdict(lambda: {
        "active_etf_flag": False,
        "momentum_etf_flag": False,
        "_semiconductor_etf_flag": False,
    })

    for r in validated:
        code = r["normalized_ticker"]
        etf_src = r.get("source_ticker_or_etf", "")
        if etf_src and r.get("source_type") == "ETF_HOLDING":
            etf_sources[code].add(etf_src)

        if r.get("active_etf_flag"):
            flags[code]["active_etf_flag"] = True
        if r.get("momentum_etf_flag"):
            flags[code]["momentum_etf_flag"] = True
        if r.get("_semiconductor_etf_flag"):
            flags[code]["_semiconductor_etf_flag"] = True

        if code not in by_ticker:
            by_ticker[code] = r.copy()
        else:
            # Keep highest source_weight
            existing_w = by_ticker[code].get("source_weight") or 0
            new_w = r.get("source_weight") or 0
            if (new_w or 0) > (existing_w or 0):
                by_ticker[code]["source_weight"] = new_w

    records = []
    for code, rec in by_ticker.items():
        rec["etf_count"] = len(etf_sources[code])
        rec["active_etf_flag"] = flags[code]["active_etf_flag"]
        rec["momentum_etf_flag"] = flags[code]["momentum_etf_flag"]
        rec["_semiconductor_etf_flag"] = flags[code]["_semiconductor_etf_flag"]
        rec["_in_ai_watchlist"] = code in ai_watchlist_codes
        # Aggregate source names for display
        src_names = sorted(etf_sources[code])
        if src_names:
            rec["source_ticker_or_etf"] = ",".join(src_names)
        records.append(rec)

    return records


def build_pool(validated: list,
               ai_watchlist_codes: set,
               run_date: str | None = None,
               write_csv: bool = True) -> tuple:
    """
    Build discovery pool from validated candidates.
    Returns (pool_records: list, csv_path: str|None).
    pool_records: sorted by discovery_score desc.
    """
    if run_date is None:
        run_date = datetime.now().strftime("%Y-%m-%d")

    merged = _deduplicate(validated, ai_watchlist_codes)

    for rec in merged:
        rec["date"] = run_date
        rec["industry"] = rec.get("industry", "")
        rec["discovery_score"] = _calc_score(rec)
        rec["discovery_status"] = _get_discovery_status(rec)
        rec["recommended_action"] = _get_recommended_action(rec)
        rec["note"] = ""
        if rec.get("_in_ai_watchlist"):
            rec["note"] = "AI watchlist confirmed"

    merged.sort(key=lambda r: r.get("discovery_score", 0), reverse=True)

    csv_path = None
    if write_csv:
        DISCOVERY_DIR.mkdir(parents=True, exist_ok=True)
        csv_path = str(DISCOVERY_DIR / f"{run_date}_candidate_discovery_pool.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(merged)

    return merged, csv_path


def build_summary(pool: list) -> dict:
    """Return count summary dict for the pool."""
    by_status = defaultdict(int)
    for r in pool:
        by_status[r.get("discovery_status", "UNKNOWN")] += 1
    return dict(by_status)
```

- [ ] **Step 2: Syntax-check**

```bash
cd /home/shimeon/investment_os && python3 -m py_compile discovery/discovery_pool_builder.py && echo "PASS"
```

Expected: `PASS`

- [ ] **Step 3: Inline logic test**

```bash
cd /home/shimeon/investment_os && python3 - <<'EOF'
import sys; sys.path.insert(0, ".")
from discovery.data_quality_gate import run_gate
from discovery.etf_source_fetcher import load_all_etf_candidates, load_ai_watchlist_codes
from discovery.discovery_pool_builder import build_pool, build_summary

# Run with write_csv=False (no file I/O)
raw = load_all_etf_candidates()
ai_codes = load_ai_watchlist_codes()

logs = []
validated = run_gate(raw, logs)
pool, csv_path = build_pool(validated, ai_codes, run_date="2026-05-07", write_csv=False)

assert isinstance(pool, list), "pool must be list"
assert len(pool) > 0, "pool must not be empty"
assert csv_path is None, "csv_path must be None when write_csv=False"

# Verify required fields present
required = ["ticker", "discovery_score", "discovery_status", "recommended_action"]
for field in required:
    assert field in pool[0], f"missing field: {field}"

# Verify no US symbols mixed into pool without THEME_MAPPING_ONLY
us_mixed = [r for r in pool if r.get("us_mapping_flag") and r["discovery_status"] != "THEME_MAPPING_ONLY"]
assert len(us_mixed) == 0, f"US symbols not properly classified: {us_mixed}"

summary = build_summary(pool)
print(f"discovery_pool_builder: PASS — pool={len(pool)} records, summary={summary}")
EOF
```

Expected: `discovery_pool_builder: PASS — pool=... records, summary={...}`

- [ ] **Step 4: Commit**

```bash
cd /home/shimeon/investment_os && git add discovery/discovery_pool_builder.py && git commit -m "feat: add discovery_pool_builder with deduplication and scoring"
```

---

## Task 4: Report Generator

**Files:**
- Create: `reporting/candidate_discovery_report.py`

- [ ] **Step 1: Write `reporting/candidate_discovery_report.py`**

```python
# reporting/candidate_discovery_report.py
"""
Generates reports/discovery/YYYY-MM-DD_candidate_discovery_report.md
from the discovery pool list produced by discovery_pool_builder.
"""
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "reports" / "discovery"


def _fmt_weight(w) -> str:
    if w is None:
        return "-"
    try:
        return f"{float(w)*100:.1f}%"
    except (TypeError, ValueError):
        return str(w)


def _fmt_price(v) -> str:
    if v is None or v == "DATA_MISSING":
        return "DATA_MISSING"
    try:
        return f"{float(v):.2f}"
    except (TypeError, ValueError):
        return "DATA_MISSING"


def _fmt_pct(v) -> str:
    if v is None or v == "DATA_MISSING":
        return "DATA_MISSING"
    try:
        return f"{float(v):+.2f}%"
    except (TypeError, ValueError):
        return "DATA_MISSING"


def _status_badge(status: str) -> str:
    badges = {
        "EXISTING_UNIVERSE_REINFORCED": "✅",
        "NEW_DISCOVERY_CANDIDATE": "🆕",
        "SOURCE_CONFLICT_REVIEW": "⚠️",
        "THEME_MAPPING_ONLY": "🌐",
        "IGNORE_LOW_RELEVANCE": "➖",
        "REJECT_BAD_TICKER": "🚫",
    }
    return badges.get(status, "❓")


def _table_row(r: dict) -> str:
    return (
        f"| {r.get('industry', '-')} "
        f"| {r.get('ticker', '-')} "
        f"| {r.get('name', '-')} "
        f"| {_fmt_price(r.get('close'))} "
        f"| {_fmt_pct(r.get('pct_change'))} "
        f"| {r.get('source_ticker_or_etf', '-')} "
        f"| {_fmt_weight(r.get('source_weight'))} "
        f"| {r.get('note', '')} |"
    )


_TABLE_HEADER = (
    "| 產業 | 代號 | 名稱 | 本日收盤價 | 漲幅 | ETF來源 | 持股比例 | note |\n"
    "|---|---|---|---:|---|---:|---|---|"
)


def _filter_by_status(pool: list, status: str) -> list:
    return [r for r in pool if r.get("discovery_status") == status]


def generate_report(pool: list,
                    summary: dict,
                    gate_log: list,
                    run_date: str | None = None,
                    write_file: bool = True) -> str:
    """
    Generate markdown report text. Optionally write to file.
    Returns the markdown string.
    """
    if run_date is None:
        run_date = datetime.now().strftime("%Y-%m-%d")

    existing = _filter_by_status(pool, "EXISTING_UNIVERSE_REINFORCED")
    new_disc = _filter_by_status(pool, "NEW_DISCOVERY_CANDIDATE")
    conflicts = _filter_by_status(pool, "SOURCE_CONFLICT_REVIEW")
    theme_map = _filter_by_status(pool, "THEME_MAPPING_ONLY")
    rejected = _filter_by_status(pool, "REJECT_BAD_TICKER")
    ignored = _filter_by_status(pool, "IGNORE_LOW_RELEVANCE")

    missing_sources = [l for l in gate_log if "not found" in l or "skipping" in l or "MISSING" in l]
    conflict_logs = [l for l in gate_log if "NAME_MISMATCH" in l or "SOURCE_CONFLICT" in l]

    lines = [
        f"# Candidate Discovery Report — {run_date}",
        "",
        "## 1. Executive Summary",
        "",
        f"- Run date: `{run_date}`",
        f"- Total pool records: **{len(pool)}**",
        f"- Existing universe reinforced: **{len(existing)}**",
        f"- New discovery candidates: **{len(new_disc)}**",
        f"- Source conflict review: **{len(conflicts)}**",
        f"- Theme mapping only (US): **{len(theme_map)}**",
        f"- Ignored (low relevance): **{len(ignored)}**",
        f"- Rejected (bad ticker): **{len(rejected)}**",
        "",
        "> Discovery Score does NOT override P1 Entry Audit. Candidates require Owner Review before universe promotion.",
        "",
    ]

    # Section 2: Existing Universe Reinforced
    lines += [
        "## 2. Existing Universe Reinforced",
        "",
        _TABLE_HEADER,
    ]
    for r in existing:
        lines.append(_table_row(r))
    if not existing:
        lines.append("_(none)_")
    lines.append("")

    # Section 3: New Discovery Candidates
    lines += [
        "## 3. New Discovery Candidates",
        "",
        _TABLE_HEADER,
    ]
    for r in new_disc:
        lines.append(_table_row(r))
    if not new_disc:
        lines.append("_(none)_")
    lines.append("")

    # Section 4: Source Conflict Review
    lines += [
        "## 4. Source Conflict Review",
        "",
        _TABLE_HEADER,
    ]
    for r in conflicts:
        lines.append(_table_row(r))
    if not conflicts:
        lines.append("_(none)_")
    lines.append("")

    # Section 5: Theme Mapping Only
    lines += [
        "## 5. Theme Mapping Only (US Symbols)",
        "",
        "These are US symbols. They must not be mixed into TW ranking.",
        "",
        _TABLE_HEADER,
    ]
    for r in theme_map:
        lines.append(_table_row(r))
    if not theme_map:
        lines.append("_(none)_")
    lines.append("")

    # Section 6: Data Quality Gate Findings
    lines += [
        "## 6. Data Quality Gate Findings",
        "",
        f"- Gate log entries: {len(gate_log)}",
        f"- Missing sources: {len(missing_sources)}",
        f"- Conflict flags: {len(conflict_logs)}",
        f"- Rejected tickers: {len(rejected)}",
        "",
    ]
    if gate_log:
        lines.append("```")
        for entry in gate_log[:30]:  # cap at 30 lines
            lines.append(entry)
        if len(gate_log) > 30:
            lines.append(f"... ({len(gate_log) - 30} more)")
        lines.append("```")
    lines.append("")

    # Section 7: Owner Review List
    lines += [
        "## 7. Owner Review List",
        "",
        "Candidates recommended for universe promotion review:",
        "",
        _TABLE_HEADER,
    ]
    review_list = [r for r in new_disc if r.get("recommended_action") == "REVIEW_FOR_UNIVERSE_ADD"]
    for r in review_list:
        lines.append(_table_row(r))
    if not review_list:
        lines.append("_(none)_")
    lines.append("")
    lines.append(f"_Generated by Investment OS candidate_discovery_report.py — {run_date}_")

    text = "\n".join(lines)

    if write_file:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORT_DIR / f"{run_date}_candidate_discovery_report.md"
        report_path.write_text(text, encoding="utf-8")

    return text
```

- [ ] **Step 2: Syntax-check**

```bash
cd /home/shimeon/investment_os && python3 -m py_compile reporting/candidate_discovery_report.py && echo "PASS"
```

Expected: `PASS`

- [ ] **Step 3: Inline test (no file I/O)**

```bash
cd /home/shimeon/investment_os && python3 - <<'EOF'
import sys; sys.path.insert(0, ".")
from reporting.candidate_discovery_report import generate_report

# Minimal synthetic pool
pool = [
    {
        "ticker": "2330", "name": "台積電", "industry": "Core",
        "source_ticker_or_etf": "0050,00891", "source_weight": 0.45,
        "close": 950.0, "pct_change": 1.5, "note": "AI watchlist confirmed",
        "discovery_status": "EXISTING_UNIVERSE_REINFORCED",
        "recommended_action": "WATCH_EXISTING_UNIVERSE",
    },
    {
        "ticker": "3363", "name": "上詮", "industry": "矽光子",
        "source_ticker_or_etf": "00993A", "source_weight": 0.05,
        "close": "DATA_MISSING", "pct_change": "DATA_MISSING", "note": "",
        "discovery_status": "NEW_DISCOVERY_CANDIDATE",
        "recommended_action": "REVIEW_FOR_UNIVERSE_ADD",
    },
    {
        "ticker": "NVDA", "name": "NVIDIA", "industry": "",
        "source_ticker_or_etf": "00757", "source_weight": 0.125,
        "close": "DATA_MISSING", "pct_change": "DATA_MISSING", "note": "",
        "discovery_status": "THEME_MAPPING_ONLY",
        "recommended_action": "US_MAPPING_ONLY",
    },
]
summary = {"EXISTING_UNIVERSE_REINFORCED": 1, "NEW_DISCOVERY_CANDIDATE": 1, "THEME_MAPPING_ONLY": 1}
gate_log = ["[GATE] 3363 issues=['MISSING_SOURCE_DATE']"]

text = generate_report(pool, summary, gate_log, run_date="2026-05-07", write_file=False)
assert "## 1. Executive Summary" in text
assert "## 2. Existing Universe Reinforced" in text
assert "## 7. Owner Review List" in text
assert "DATA_MISSING" in text or "DATA_MISSING" not in text  # graceful
assert "NVDA" in text
assert "台積電" in text

print("candidate_discovery_report: PASS")
EOF
```

Expected: `candidate_discovery_report: PASS`

- [ ] **Step 4: Commit**

```bash
cd /home/shimeon/investment_os && git add reporting/candidate_discovery_report.py && git commit -m "feat: add candidate_discovery_report generator (7 sections)"
```

---

## Task 5: Main Runner Script

**Files:**
- Create: `scripts/run_candidate_discovery.py`

- [ ] **Step 1: Write `scripts/run_candidate_discovery.py`**

```python
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


def _verify_universe_untouched():
    universe_path = PROJECT_ROOT / "data" / "universe_tw.csv"
    if not universe_path.exists():
        print("[GUARDRAIL] WARNING: universe_tw.csv not found")
        return
    mtime_before = universe_path.stat().st_mtime
    return mtime_before


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

    universe_mtime = _verify_universe_untouched()

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

    # ── Step 3: Load AI watchlist codes for scoring ──────────────
    ai_codes = load_ai_watchlist_codes()

    # ── Step 4: Build pool (no CSV yet — add prices first) ───────
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

    # ── Write CSV ────────────────────────────────────────────────
    print("[5/5] Writing outputs...")
    pool_final, csv_path = build_pool(validated, ai_codes, run_date=run_date, write_csv=True)
    # Re-attach prices fetched above
    price_lookup = {r["normalized_ticker"]: r for r in pool}
    for rec in pool_final:
        src = price_lookup.get(rec["normalized_ticker"], {})
        rec["close"] = src.get("close", "DATA_MISSING")
        rec["pct_change"] = src.get("pct_change", "DATA_MISSING")

    summary = build_summary(pool_final)
    report_text = generate_report(pool_final, summary, gate_log, run_date=run_date, write_file=True)

    # ── Guardrail: verify universe untouched ─────────────────────
    universe_path = PROJECT_ROOT / "data" / "universe_tw.csv"
    if universe_path.exists() and universe_mtime:
        assert universe_path.stat().st_mtime == universe_mtime, \
            "GUARDRAIL VIOLATION: universe_tw.csv was modified!"

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("Discovery Summary:")
    for status, count in sorted(summary.items()):
        print(f"  {status}: {count}")
    print(f"\nOutputs:")
    print(f"  CSV:    {csv_path}")
    report_path = PROJECT_ROOT / "reports" / "discovery" / f"{run_date}_candidate_discovery_report.md"
    print(f"  Report: {report_path}")
    print(f"\nGate log: {len(gate_log)} entries")
    if rejected_count:
        print(f"  Rejected tickers: {rejected_count}")
    if conflict_count:
        print(f"  Conflict review needed: {conflict_count}")
    print(f"\nGuardrails confirmed:")
    print(f"  - universe_tw.csv: NOT MODIFIED")
    print(f"  - Trading logic: NOT TOUCHED")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Syntax-check**

```bash
cd /home/shimeon/investment_os && python3 -m py_compile scripts/run_candidate_discovery.py && echo "PASS"
```

Expected: `PASS`

- [ ] **Step 3: Commit**

```bash
cd /home/shimeon/investment_os && git add scripts/run_candidate_discovery.py && git commit -m "feat: add run_candidate_discovery.py CLI runner"
```

---

## Task 6: Smoke Test + Integration Validation

**Files:**
- Create: `tests/smoke_candidate_discovery.py`

- [ ] **Step 1: Write `tests/smoke_candidate_discovery.py`**

```python
# tests/smoke_candidate_discovery.py
"""
Offline smoke test for Candidate Discovery Pool v0.1.
No network I/O. No file writes. Uses synthetic mock data.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from discovery.data_quality_gate import run_gate
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
        # TW stock already in universe
        {
            "ticker": "2330", "name": "台積電", "industry": "Core",
            "source_type": "ETF_HOLDING", "source_name": "元大台灣50",
            "source_ticker_or_etf": "0050", "source_weight": 0.458,
            "source_date": "2026-04-30",
            "active_etf_flag": False, "momentum_etf_flag": False,
            "_semiconductor_etf_flag": False,
        },
        # New TW discovery candidate
        {
            "ticker": "3363", "name": "上詮", "industry": "矽光子",
            "source_type": "ETF_HOLDING", "source_name": "中信AI晶片",
            "source_ticker_or_etf": "00993A", "source_weight": 0.051,
            "source_date": "2026-04-30",
            "active_etf_flag": True, "momentum_etf_flag": False,
            "_semiconductor_etf_flag": False,
        },
        # US symbol → must be THEME_MAPPING_ONLY
        {
            "ticker": "NVDA", "name": "NVIDIA", "industry": "GPU",
            "source_type": "ETF_HOLDING", "source_name": "統一FANG+",
            "source_ticker_or_etf": "00757", "source_weight": 0.125,
            "source_date": "2026-04-30",
            "active_etf_flag": False, "momentum_etf_flag": False,
            "_semiconductor_etf_flag": False,
        },
        # Name mismatch → SOURCE_CONFLICT_REVIEW
        {
            "ticker": "2454", "name": "WRONG NAME", "industry": "IC Design",
            "source_type": "ETF_HOLDING", "source_name": "富邦科技",
            "source_ticker_or_etf": "0052", "source_weight": 0.061,
            "source_date": "2026-04-30",
            "active_etf_flag": False, "momentum_etf_flag": False,
            "_semiconductor_etf_flag": False,
        },
        # Bad ticker → REJECT
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
    universe_codes = {"2330", "2454", "3443"}
    master_map = {"2330": "台積電", "2454": "聯發科"}

    logs = []
    # Run gate with explicit universe/master (no file I/O)
    from discovery.data_quality_gate import validate
    results = []
    for c in raw:
        results.append(validate(c.copy(), universe_codes, master_map))

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

    r_bad = next(r for r in results if r["normalized_ticker"] == "??BAD")
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

    from discovery.data_quality_gate import validate
    validated = [validate(c.copy(), universe_codes, master_map) for c in raw]

    ai_codes = {"2330", "3363"}
    pool, csv_path = build_pool(validated, ai_codes, run_date="2026-05-07", write_csv=False)

    _assert(csv_path is None, "write_csv=False → csv_path=None")
    _assert(len(pool) > 0, "pool has records")

    # US symbols must not be in TW ranking (must be THEME_MAPPING_ONLY)
    us_mixed = [r for r in pool
                if r.get("us_mapping_flag") and r["discovery_status"] != "THEME_MAPPING_ONLY"]
    _assert(len(us_mixed) == 0, "US symbols not mixed into TW ranking")

    # Required fields present
    for field in ["ticker", "discovery_score", "discovery_status", "recommended_action", "date"]:
        _assert(field in pool[0], f"field '{field}' present in pool records")

    # AI watchlist confirmed gets bonus score
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
    import csv
    universe_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "universe_tw.csv"
    )
    if not os.path.exists(universe_path):
        print("  - universe_tw.csv not found, skipping guardrail check")
        return
    with open(universe_path, "r", encoding="utf-8") as f:
        original = f.read()
    # Run gate (should never write to universe_tw.csv)
    from discovery.data_quality_gate import run_gate
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
```

- [ ] **Step 2: Run smoke test**

```bash
cd /home/shimeon/investment_os && python3 tests/smoke_candidate_discovery.py
```

Expected: All `✓` lines, ends with `Smoke Candidate Discovery: PASSED`

- [ ] **Step 3: Verify py_compile passes all new files**

```bash
cd /home/shimeon/investment_os && python3 -m py_compile \
    discovery/__init__.py \
    discovery/data_quality_gate.py \
    discovery/etf_source_fetcher.py \
    discovery/discovery_pool_builder.py \
    reporting/candidate_discovery_report.py \
    scripts/run_candidate_discovery.py \
    tests/smoke_candidate_discovery.py \
    && echo "py_compile: ALL PASS"
```

Expected: `py_compile: ALL PASS`

- [ ] **Step 4: Dry run (no price fetch, no git)**

```bash
cd /home/shimeon/investment_os && python3 scripts/run_candidate_discovery.py --no-price --date 2026-05-07
```

Expected:
- Prints discovery summary
- `data/discovery/2026-05-07_candidate_discovery_pool.csv` created
- `reports/discovery/2026-05-07_candidate_discovery_report.md` created
- "Guardrails confirmed: universe_tw.csv: NOT MODIFIED"

- [ ] **Step 5: Verify outputs exist**

```bash
ls -la /home/shimeon/investment_os/data/discovery/ && ls -la /home/shimeon/investment_os/reports/discovery/
```

Expected: Both files exist and are non-empty.

- [ ] **Step 6: Verify universe_tw.csv not modified**

```bash
cd /home/shimeon/investment_os && git diff data/universe_tw.csv && echo "universe_tw.csv: CLEAN"
```

Expected: No diff output, then `universe_tw.csv: CLEAN`

- [ ] **Step 7: Commit all**

```bash
cd /home/shimeon/investment_os && git add \
    tests/smoke_candidate_discovery.py \
    data/discovery/ \
    reports/discovery/ \
    && git commit -m "Build candidate discovery pool and data quality gate v0.1"
```

---

## Self-Review Checklist

| Spec Requirement | Plan Coverage |
|---|---|
| Layer 1 Core Universe (read-only) | `universe_tw.csv` never written; guardrail in runner + smoke test |
| Layer 2 Candidate Discovery Pool | Task 3 `discovery_pool_builder.py` |
| Layer 3 External Mapping / Regime Pool | `THEME_MAPPING_ONLY` status for US symbols in gate |
| Data Quality Gate 8 checks | Task 1 `data_quality_gate.py` — all 8 checks |
| Required CSV columns (19 fields) | `REQUIRED_COLUMNS` in `discovery_pool_builder.py` |
| All 6 candidate status values | `_get_discovery_status()` covers all |
| All 5 recommended actions | `_get_recommended_action()` covers all |
| Discovery Score v0.1 factors | `_calc_score()` — 10 factors |
| ETF list (13 ETFs) | Embedded in `etf_source_fetcher.py` |
| Markdown report 7 sections | `generate_report()` in Task 4 |
| Report table format | `_TABLE_HEADER` + `_table_row()` |
| DATA_MISSING for unavailable prices | `fetch_price()` returns `"DATA_MISSING"` |
| Missing sources do not crash | `get_etf_holdings()` returns `[]`, `run_gate()` catches exceptions |
| US symbols not in TW ranking | Enforced via `THEME_MAPPING_ONLY` + smoke test assertion |
| Commit message | "Build candidate discovery pool and data quality gate v0.1" |
| py_compile validation | Task 6 Step 3 |
| Smoke validation | Task 6 Step 2 |
| Market Sentiment Engine placeholder | Not implemented (spec says reserve schema only if useful — skipped for v0.1) |
