from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TW_TICKER_MASTER_PATH = PROJECT_ROOT / "data" / "master" / "tw_ticker_master.json"


def normalize_ticker(ticker: str) -> str:
    """
    Normalize ticker for comparison and canonical mapping.

    Examples:
    - 2330.TW  -> 2330
    - 6187.TWO -> 6187
    - 00992A   -> 00992A
    """
    ticker = str(ticker).strip()
    if "." in ticker:
        return ticker.split(".")[0]
    return ticker


def load_ticker_master(path=DEFAULT_TW_TICKER_MASTER_PATH) -> dict:
    path = Path(path)

    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = data.get("tickers", [])
    master = {}

    for row in rows:
        ticker = row.get("ticker")
        if not ticker:
            continue

        base_ticker = normalize_ticker(ticker)
        master[base_ticker] = {
            **row,
            "ticker": base_ticker,
            "canonical_name": row.get("canonical_name", row.get("name", base_ticker)),
        }

    return master


def resolve_canonical_name(
    ticker: str,
    fallback_name=None,
    master=None,
) -> str:
    base_ticker = normalize_ticker(ticker)
    master = master if master is not None else load_ticker_master()

    if base_ticker in master:
        return master[base_ticker].get("canonical_name", fallback_name or base_ticker)

    if fallback_name:
        return fallback_name

    return base_ticker


def resolve_asset_type(
    ticker: str,
    fallback_asset_type=None,
    master=None,
) -> str:
    base_ticker = normalize_ticker(ticker)
    master = master if master is not None else load_ticker_master()

    if base_ticker in master:
        return master[base_ticker].get("asset_type", fallback_asset_type or "-")

    return fallback_asset_type or "-"
