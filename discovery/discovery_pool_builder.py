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
_AI_WATCHLIST_PATH = PROJECT_ROOT / "data" / "master" / "ai_watchlist_source.csv"
_UNIVERSE_PATH = PROJECT_ROOT / "data" / "universe_tw.csv"


def _build_industry_lookup() -> dict:
    """
    Build {ticker_code: industry_str} from two sources:
    1. universe_tw.csv sector (broad fallback)
    2. ai_watchlist_source.csv 產業類別 (overrides, more specific)
    """
    lookup = {}
    if _UNIVERSE_PATH.exists():
        with open(_UNIVERSE_PATH, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                code = row.get("ticker", "").split(".")[0].strip()
                sector = row.get("sector", "").strip()
                if code and sector:
                    lookup[code] = sector
    if _AI_WATCHLIST_PATH.exists():
        with open(_AI_WATCHLIST_PATH, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                code = row.get("股票代號", "").strip()
                industry = row.get("產業類別", "").strip()
                enabled = row.get("啟用", "").strip().lower()
                if code and industry and enabled == "true":
                    lookup[code] = industry
    return lookup

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
    OR-combines boolean flags; keeps highest source_weight seen.
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
    industry_lookup = _build_industry_lookup()

    for rec in merged:
        rec["date"] = run_date
        if not rec.get("industry"):
            rec["industry"] = industry_lookup.get(rec["normalized_ticker"], "")
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
