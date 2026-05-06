from metadata.ticker_master import (
    normalize_ticker,
    load_ticker_master,
    resolve_canonical_name,
    resolve_asset_type,
)


def main():
    master = load_ticker_master()

    assert normalize_ticker("2330.TW") == "2330"
    assert normalize_ticker("6187.TWO") == "6187"
    assert normalize_ticker("00992A") == "00992A"

    assert resolve_canonical_name("6830", master=master) == "汎銓"
    assert resolve_canonical_name("6830.TWO", master=master) == "汎銓"
    assert resolve_canonical_name("2330.TW", master=master) == "台積電"
    assert resolve_canonical_name("6187.TWO", master=master) == "萬潤"
    assert resolve_canonical_name("5443.TWO", master=master) == "均豪"
    assert resolve_canonical_name("3680.TWO", master=master) == "家登"

    assert resolve_asset_type("009816", master=master) == "ETF"
    assert resolve_asset_type("2330.TW", master=master) == "stock"

    print("Ticker master smoke test passed.")


if __name__ == "__main__":
    main()
