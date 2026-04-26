from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOLDINGS_PATH = PROJECT_ROOT / "data" / "portfolio" / "current_holdings.json"


def load_current_holdings(path: str | Path = DEFAULT_HOLDINGS_PATH) -> dict:
    """
    Load current portfolio holdings from JSON.

    This module is intentionally simple.
    Do not add valuation, signal, risk, or execution logic here.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Holdings file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "holdings" not in data:
        raise ValueError("Invalid holdings file: missing 'holdings' field")

    if not isinstance(data["holdings"], list):
        raise ValueError("Invalid holdings file: 'holdings' must be a list")

    for item in data["holdings"]:
        if "ticker" not in item:
            raise ValueError(f"Invalid holding item, missing ticker: {item}")

        if "shares" not in item:
            raise ValueError(f"Invalid holding item, missing shares: {item}")

        item["ticker"] = str(item["ticker"]).strip()
        item["shares"] = int(item["shares"])

    return data


def get_holding_shares(ticker: str, path: str | Path = DEFAULT_HOLDINGS_PATH) -> int:
    """
    Return current shares for a specific ticker.
    If ticker does not exist, return 0.
    """

    ticker = str(ticker).strip()
    data = load_current_holdings(path)

    for item in data["holdings"]:
        if item["ticker"] == ticker:
            return int(item["shares"])

    return 0


def list_current_positions(path: str | Path = DEFAULT_HOLDINGS_PATH) -> list[dict]:
    """
    Return holdings list only.
    """

    data = load_current_holdings(path)
    return data["holdings"]
