import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
from analysis.technical_action_mode import classify_action_mode
from analysis.chase_risk import compute_chase_risk


def make_close(prices: list) -> pd.DataFrame:
    return pd.DataFrame({"TEST": prices})


def make_features(close_df: pd.DataFrame) -> dict:
    prices = close_df["TEST"]
    return {
        "ma5": pd.DataFrame({"TEST": prices.rolling(5).mean()}),
        "ma20": pd.DataFrame({"TEST": prices.rolling(20).mean()}),
        "vol_ratio": pd.DataFrame({"TEST": pd.Series([1.0] * len(prices))}),
    }


def test_tech_attack():
    result = classify_action_mode(
        signal="BUY", level="READY", vol_ratio=2.5,
        chase_risk="LOW", chip_status="POSITIVE",
        market_state="BULL",
    )
    assert result["action_mode"] == "TECH_ATTACK", f"got {result['action_mode']}"


def test_chase_gate_high_suppresses_buy():
    # Phase 1A: HIGH chase risk must suppress BUY → TECH_WATCH regardless of vol_ratio
    result = classify_action_mode(
        signal="BUY", level="READY", vol_ratio=2.5,
        chase_risk="HIGH", chip_status="POSITIVE",
        market_state="RANGE",
    )
    assert result["action_mode"] == "TECH_WATCH", f"got {result['action_mode']}"
    assert "chase_risk_gate=BUY_SUPPRESSED" in result["technical_reasons"]


def test_chase_gate_extreme_suppresses_buy():
    # Phase 1A: EXTREME chase risk must also suppress BUY
    result = classify_action_mode(
        signal="BUY", level="ATTACK", vol_ratio=3.0,
        chase_risk="EXTREME", chip_status="STRONG_POSITIVE",
        market_state="BULL",
    )
    assert result["action_mode"] == "TECH_WATCH", f"got {result['action_mode']}"
    assert "chase_risk_gate=BUY_SUPPRESSED" in result["technical_reasons"]


def test_tech_buy():
    result = classify_action_mode(
        signal="BUY", level="READY", vol_ratio=1.2,
        chase_risk="LOW", chip_status="POSITIVE",
        market_state="RANGE",
    )
    assert result["action_mode"] == "TECH_BUY", f"got {result['action_mode']}"


def test_tech_buy_caution_divergence():
    result = classify_action_mode(
        signal="BUY", level="READY", vol_ratio=1.2,
        chase_risk="LOW", chip_status="DIVERGENCE",
        market_state="RANGE",
    )
    assert result["action_mode"] == "TECH_BUY_CAUTION", f"got {result['action_mode']}"


def test_tech_buy_caution_medium_chase():
    result = classify_action_mode(
        signal="BUY", level="READY", vol_ratio=1.5,
        chase_risk="MEDIUM", chip_status="POSITIVE",
        market_state="RANGE",
    )
    assert result["action_mode"] == "TECH_BUY_CAUTION", f"got {result['action_mode']}"


def test_tech_watch():
    result = classify_action_mode(
        signal="", level="READY", vol_ratio=0.9,
        chase_risk="LOW", chip_status="MISSING",
        market_state="RANGE",
    )
    assert result["action_mode"] == "TECH_WATCH", f"got {result['action_mode']}"


def test_tech_reduce():
    result = classify_action_mode(
        signal="BUY", level="READY", vol_ratio=1.0,
        chase_risk="LOW", chip_status="MISSING",
        market_state="RANGE",
        exit_signal="REDUCE",
    )
    assert result["action_mode"] == "TECH_REDUCE", f"got {result['action_mode']}"


def test_tech_exit():
    result = classify_action_mode(
        signal="BUY", level="READY", vol_ratio=1.0,
        chase_risk="LOW", chip_status="MISSING",
        market_state="RANGE",
        exit_signal="EXIT_ALL",
    )
    assert result["action_mode"] == "TECH_EXIT", f"got {result['action_mode']}"


def test_chase_risk_low():
    prices = [100.0] * 25
    close = make_close(prices)
    features = make_features(close)
    result = compute_chase_risk(close, features, "TEST")
    assert result["chase_risk"] == "LOW", f"got {result}"


def test_chase_risk_extreme():
    # Simulate a big up day after a steady base
    prices = [100.0] * 24 + [110.0]
    close = make_close(prices)
    features = make_features(close)
    # vol_ratio high
    features["vol_ratio"] = pd.DataFrame({"TEST": [1.0] * 24 + [3.5]})
    result = compute_chase_risk(close, features, "TEST")
    assert result["chase_risk"] in ("HIGH", "EXTREME"), f"got {result}"


def test_output_fields():
    result = classify_action_mode(
        signal="BUY", level="READY", vol_ratio=2.0,
        chase_risk="HIGH", chip_status="POSITIVE",
        market_state="RANGE",
    )
    for field in ("action_mode", "action_label", "suggested_action", "technical_reasons", "invalid_if"):
        assert field in result, f"missing field: {field}"
    assert len(result["technical_reasons"]) >= 4
    assert len(result["action_label"]) > 0
    assert len(result["suggested_action"]) > 0


def main():
    test_tech_attack()
    test_chase_gate_high_suppresses_buy()
    test_chase_gate_extreme_suppresses_buy()
    test_tech_buy()
    test_tech_buy_caution_divergence()
    test_tech_buy_caution_medium_chase()
    test_tech_watch()
    test_tech_reduce()
    test_tech_exit()
    test_chase_risk_low()
    test_chase_risk_extreme()
    test_output_fields()
    print("smoke_technical_action_mode: all tests passed.")


if __name__ == "__main__":
    main()
