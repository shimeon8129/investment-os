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
