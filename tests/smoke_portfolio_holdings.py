from portfolio.holdings_loader import (
    load_current_holdings,
    get_holding_shares,
    list_current_positions,
)


def main():
    data = load_current_holdings()
    positions = list_current_positions()

    print(f"As of: {data.get('as_of')}")
    print(f"Currency: {data.get('currency')}")
    print(f"Market: {data.get('market')}")
    print(f"Position count: {len(positions)}")

    for item in positions:
        print(
            item.get("ticker"),
            item.get("name"),
            item.get("shares"),
            item.get("asset_type"),
        )

    assert get_holding_shares("009816") == 5000
    assert get_holding_shares("00992A") == 5000
    assert get_holding_shares("2330") == 50
    assert get_holding_shares("2345") == 55
    assert get_holding_shares("3017") == 20
    assert get_holding_shares("3711") == 50
    assert get_holding_shares("6830") == 20
    assert get_holding_shares("9999") == 0

    print("Portfolio holdings smoke test passed.")


if __name__ == "__main__":
    main()
