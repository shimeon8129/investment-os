from pathlib import Path
import json

import yfinance as yf

from portfolio.broker_valuation import summarize_positions, value_position
from portfolio.holdings_loader import DEFAULT_HOLDINGS_PATH, load_current_holdings


def yahoo_ticker_candidates(ticker: str) -> list[str]:
    if "." in ticker:
        return [ticker]
    return [f"{ticker}.TW", f"{ticker}.TWO"]


def fetch_latest_price(ticker: str) -> tuple[float | None, str | None]:
    for yahoo_ticker in yahoo_ticker_candidates(ticker):
        hist = yf.download(
            yahoo_ticker,
            period="5d",
            interval="1d",
            auto_adjust=True,
            progress=False,
        )

        if hist.empty or "Close" not in hist:
            continue

        close = hist["Close"].dropna()
        if close.empty:
            continue

        value = close.iloc[-1]
        if hasattr(value, "iloc"):
            value = value.iloc[0]

        return float(value), yahoo_ticker

    return None, None


def build_valuation_report(path: str | Path = DEFAULT_HOLDINGS_PATH) -> dict:
    data = load_current_holdings(path)
    rows = []
    missing_prices = []
    missing_cost_basis = []

    for holding in data["holdings"]:
        yahoo_ticker = None

        if holding.get("broker_market_value") is not None:
            price = float(holding["broker_market_value"]) / int(holding["shares"])
            yahoo_ticker = "broker_snapshot"
        else:
            price, yahoo_ticker = fetch_latest_price(holding["ticker"])
            if price is None:
                missing_prices.append(holding["ticker"])
                continue

        try:
            row = value_position(holding, price)
        except ValueError:
            missing_cost_basis.append(holding["ticker"])
            continue

        row["yahoo_ticker"] = yahoo_ticker
        rows.append(row)

    return {
        "as_of": data.get("as_of"),
        "currency": data.get("currency"),
        "rows": rows,
        "summary": summarize_positions(rows),
        "missing_prices": missing_prices,
        "missing_cost_basis": missing_cost_basis,
    }


def main():
    report = build_valuation_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
