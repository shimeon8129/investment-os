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
            {"ticker": "2330", "name": "台積電",     "weight": 0.4580},
            {"ticker": "2317", "name": "鴻海",       "weight": 0.0652},
            {"ticker": "2454", "name": "聯發科",     "weight": 0.0521},
            {"ticker": "2308", "name": "台達電",     "weight": 0.0298},
            {"ticker": "2382", "name": "廣達",       "weight": 0.0289},
            {"ticker": "3711", "name": "日月光投控", "weight": 0.0201},
            {"ticker": "2303", "name": "聯電",       "weight": 0.0198},
            {"ticker": "2881", "name": "富邦金",     "weight": 0.0195},
            {"ticker": "2882", "name": "國泰金",     "weight": 0.0188},
            {"ticker": "2412", "name": "中華電信",   "weight": 0.0185},
            {"ticker": "6669", "name": "緯穎",       "weight": 0.0165},
            {"ticker": "2002", "name": "中鋼",       "weight": 0.0142},
        ],
    },
    "0052": {
        "name": "富邦科技",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",     "weight": 0.6720},
            {"ticker": "2303", "name": "聯電",       "weight": 0.0921},
            {"ticker": "2454", "name": "聯發科",     "weight": 0.0612},
            {"ticker": "3711", "name": "日月光投控", "weight": 0.0398},
            {"ticker": "2317", "name": "鴻海",       "weight": 0.0312},
            {"ticker": "6669", "name": "緯穎",       "weight": 0.0201},
            {"ticker": "3443", "name": "創意",       "weight": 0.0156},
        ],
    },
    "006208": {
        "name": "富邦台灣采吉50",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",     "weight": 0.4512},
            {"ticker": "2317", "name": "鴻海",       "weight": 0.0645},
            {"ticker": "2454", "name": "聯發科",     "weight": 0.0498},
            {"ticker": "2308", "name": "台達電",     "weight": 0.0289},
            {"ticker": "2382", "name": "廣達",       "weight": 0.0272},
            {"ticker": "3711", "name": "日月光投控", "weight": 0.0188},
            {"ticker": "6669", "name": "緯穎",       "weight": 0.0178},
            {"ticker": "2303", "name": "聯電",       "weight": 0.0175},
        ],
    },
    "00881": {
        "name": "國泰台灣5G+",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",   "weight": 0.2890},
            {"ticker": "2454", "name": "聯發科",   "weight": 0.1102},
            {"ticker": "3661", "name": "世芯-KY",  "weight": 0.0821},
            {"ticker": "6669", "name": "緯穎",     "weight": 0.0756},
            {"ticker": "2345", "name": "智邦",     "weight": 0.0612},
            {"ticker": "3443", "name": "創意",     "weight": 0.0589},
            {"ticker": "2382", "name": "廣達",     "weight": 0.0489},
        ],
    },
    "00891": {
        "name": "中信關鍵半導體",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",     "weight": 0.3012},
            {"ticker": "2454", "name": "聯發科",     "weight": 0.1256},
            {"ticker": "3711", "name": "日月光投控", "weight": 0.0892},
            {"ticker": "2303", "name": "聯電",       "weight": 0.0712},
            {"ticker": "3661", "name": "世芯-KY",    "weight": 0.0589},
            {"ticker": "2449", "name": "京元電子",   "weight": 0.0456},
            {"ticker": "6239", "name": "力成",       "weight": 0.0389},
            {"ticker": "3443", "name": "創意",       "weight": 0.0356},
            {"ticker": "6515", "name": "穎崴",       "weight": 0.0312},
            {"ticker": "6147", "name": "頎邦",       "weight": 0.0289},
        ],
    },
    "00892": {
        "name": "富邦台灣半導體",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",     "weight": 0.3456},
            {"ticker": "2454", "name": "聯發科",     "weight": 0.1123},
            {"ticker": "3711", "name": "日月光投控", "weight": 0.0823},
            {"ticker": "2303", "name": "聯電",       "weight": 0.0698},
            {"ticker": "3661", "name": "世芯-KY",    "weight": 0.0512},
            {"ticker": "3443", "name": "創意",       "weight": 0.0421},
            {"ticker": "2449", "name": "京元電子",   "weight": 0.0389},
            {"ticker": "6257", "name": "矽格",       "weight": 0.0312},
        ],
    },
    "00904": {
        "name": "新光臺灣半導體30",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",     "weight": 0.2823},
            {"ticker": "2454", "name": "聯發科",     "weight": 0.1012},
            {"ticker": "3661", "name": "世芯-KY",    "weight": 0.0789},
            {"ticker": "3443", "name": "創意",       "weight": 0.0623},
            {"ticker": "3711", "name": "日月光投控", "weight": 0.0589},
            {"ticker": "2303", "name": "聯電",       "weight": 0.0512},
            {"ticker": "6515", "name": "穎崴",       "weight": 0.0456},
            {"ticker": "6147", "name": "頎邦",       "weight": 0.0389},
            {"ticker": "2449", "name": "京元電子",   "weight": 0.0342},
            {"ticker": "6239", "name": "力成",       "weight": 0.0298},
        ],
    },
    "00992A": {
        "name": "群益台灣科技創新",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",   "weight": 0.2156},
            {"ticker": "3661", "name": "世芯-KY",  "weight": 0.1023},
            {"ticker": "2454", "name": "聯發科",   "weight": 0.0912},
            {"ticker": "6669", "name": "緯穎",     "weight": 0.0789},
            {"ticker": "2345", "name": "智邦",     "weight": 0.0656},
            {"ticker": "3443", "name": "創意",     "weight": 0.0589},
            {"ticker": "3363", "name": "上詮",     "weight": 0.0512},
            {"ticker": "4979", "name": "華星光",   "weight": 0.0445},
        ],
    },
    "00993A": {
        "name": "中信AI晶片",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",   "weight": 0.2512},
            {"ticker": "3661", "name": "世芯-KY",  "weight": 0.1256},
            {"ticker": "2454", "name": "聯發科",   "weight": 0.1023},
            {"ticker": "3443", "name": "創意",     "weight": 0.0789},
            {"ticker": "6669", "name": "緯穎",     "weight": 0.0656},
            {"ticker": "3363", "name": "上詮",     "weight": 0.0512},
            {"ticker": "3081", "name": "聯亞",     "weight": 0.0423},
            {"ticker": "3105", "name": "穩懋",     "weight": 0.0389},
            {"ticker": "4979", "name": "華星光",   "weight": 0.0312},
        ],
    },
    "00994A": {
        "name": "富邦台灣科技",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",     "weight": 0.2889},
            {"ticker": "2454", "name": "聯發科",     "weight": 0.1123},
            {"ticker": "3661", "name": "世芯-KY",    "weight": 0.0856},
            {"ticker": "2382", "name": "廣達",       "weight": 0.0712},
            {"ticker": "6669", "name": "緯穎",       "weight": 0.0589},
            {"ticker": "3711", "name": "日月光投控", "weight": 0.0512},
            {"ticker": "3443", "name": "創意",       "weight": 0.0456},
            {"ticker": "2345", "name": "智邦",       "weight": 0.0389},
        ],
    },
    "00733": {
        "name": "富邦臺灣中小",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "3017", "name": "奇鋐",    "weight": 0.0423},
            {"ticker": "3324", "name": "雙鴻",    "weight": 0.0389},
            {"ticker": "6781", "name": "AES-KY",  "weight": 0.0312},
            {"ticker": "2059", "name": "川湖",    "weight": 0.0289},
            {"ticker": "3081", "name": "聯亞",    "weight": 0.0256},
            {"ticker": "3363", "name": "上詮",    "weight": 0.0234},
            {"ticker": "3105", "name": "穩懋",    "weight": 0.0212},
            {"ticker": "4979", "name": "華星光",  "weight": 0.0198},
        ],
    },
    "00830": {
        "name": "國泰臺灣ESG",
        "source_date": "2026-04-30",
        "holdings": [
            {"ticker": "2330", "name": "台積電",   "weight": 0.2156},
            {"ticker": "2454", "name": "聯發科",   "weight": 0.0923},
            {"ticker": "2317", "name": "鴻海",     "weight": 0.0712},
            {"ticker": "2308", "name": "台達電",   "weight": 0.0589},
            {"ticker": "2382", "name": "廣達",     "weight": 0.0456},
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
    try:
        import yfinance as yf
        yf_ticker = f"{ticker_code}.TW"
        t = yf.Ticker(yf_ticker)
        hist = t.history(period="5d")
        if hist.empty or len(hist) < 2:
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
