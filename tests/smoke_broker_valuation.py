import sys
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parents[1]))

from portfolio.broker_valuation import value_position


def main():
    holding = {
        "ticker": "009816",
        "name": "富邦台灣TOP50",
        "shares": 5000,
        "entry_price": 11.42,
        "cost_basis": 57080,
        "asset_type": "ETF",
    }

    result = value_position(holding, last_price=13.15)

    assert result["market_value"] == 65750
    assert result["gross_pnl"] == 8670
    assert result["estimated_sell_fee"] == 93
    assert result["estimated_sell_tax"] == 65
    assert result["estimated_sell_cost"] == 158
    assert result["broker_trial_pnl"] == 8512
    assert round(result["broker_trial_return_pct"], 2) == 14.91

    print("Broker valuation smoke test passed")
    print("009816 broker trial pnl:", result["broker_trial_pnl"])
    print("009816 broker trial return:", round(result["broker_trial_return_pct"], 2))


if __name__ == "__main__":
    main()
