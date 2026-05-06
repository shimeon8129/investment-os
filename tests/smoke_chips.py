import sys
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.ranking_engine import rank_stocks
from steps.fetch_chips import score_chip_flow


def main():
    strong = {
        "foreign_net_buy": 1_200_000,
        "trust_net_buy": 300_000,
        "dealer_net_buy": 50_000,
        "institutional_net_buy": 1_550_000,
    }
    weak = {
        "foreign_net_buy": -1_200_000,
        "trust_net_buy": -300_000,
        "dealer_net_buy": 50_000,
        "institutional_net_buy": -1_450_000,
    }

    assert score_chip_flow(strong) > score_chip_flow(weak)

    ranked = rank_stocks(
        signal_results=[
            {"ticker": "CHIP.TW", "signal": "BUY", "level": "READY"},
            {"ticker": "NOCHIP.TW", "signal": "BUY", "level": "READY"},
        ],
        scanner_results={"CHIP.TW": 2, "NOCHIP.TW": 2},
        sector_map={"CHIP.TW": "Equipment", "NOCHIP.TW": "Equipment"},
        name_map={"CHIP.TW": "Institutional Buy", "NOCHIP.TW": "No Chip"},
        chip_results={
            "CHIP.TW": {
                **strong,
                "chip_score": 95,
                "institutional_bias": "BUY",
            }
        },
    )

    assert ranked[0]["ticker"] == "CHIP.TW"
    assert ranked[0]["chip_bonus"] == 19
    assert ranked[0]["institutional_bias"] == "BUY"

    print("Chips smoke test passed")
    print("Strong chip score:", score_chip_flow(strong))


if __name__ == "__main__":
    main()
