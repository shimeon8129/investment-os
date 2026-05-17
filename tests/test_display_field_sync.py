# tests/test_display_field_sync.py
# P0.1 Display Field Sync — verify safety gate updates action_label + suggested_action

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from decision.entry_safety_gate import apply_entry_safety_gate


def _base(**kwargs) -> dict:
    defaults = {
        "ticker": "TEST",
        "action_mode": "TECH_BUY",
        "action_label": "技術買進",
        "suggested_action": "試單",
        "vol_ratio": 1.2,
        "chip_status": "POSITIVE",
        "chase_risk": "LOW",
        "is_held": False,
    }
    defaults.update(kwargs)
    return defaults


def test_low_volume_downgrades_action_label():
    """vol_ratio<1.0 時，action_label 必須同步 downgrade，不能仍顯示「技術買進」。"""
    result = apply_entry_safety_gate(_base(vol_ratio=0.8))
    assert result["action_mode"] == "WATCH_READY"
    assert result["action_label"] != "技術買進"
    assert result["action_label"]  # must be non-empty


def test_chip_divergence_downgrades_action_label():
    """chip_status=DIVERGENCE 時，action_label 必須同步 downgrade。"""
    result = apply_entry_safety_gate(_base(chip_status="DIVERGENCE"))
    assert result["action_mode"] == "WATCH_READY"
    assert result["action_label"] != "技術買進"
    assert result["action_label"]


def test_chip_strong_divergence_downgrades_action_label():
    """chip_status=STRONG_DIVERGENCE 時，action_label 也必須 downgrade。"""
    result = apply_entry_safety_gate(_base(chip_status="STRONG_DIVERGENCE"))
    assert result["action_mode"] == "WATCH_READY"
    assert result["action_label"] != "技術買進"


def test_chase_high_downgrades_action_label():
    """chase_risk=HIGH 時，action_label 必須同步 downgrade。"""
    result = apply_entry_safety_gate(_base(chase_risk="HIGH"))
    assert result["action_mode"] == "NO_FRESH_ENTRY_EXTENDED"
    assert result["action_label"] != "技術買進"
    assert result["action_label"]


def test_held_ticker_uses_position_manage_label():
    """已持倉 ticker 的 action_label 應為「持倉管理」類字樣。"""
    result = apply_entry_safety_gate(_base(is_held=True))
    assert result["action_mode"] == "POSITION_MANAGE_ONLY"
    assert "持倉" in result["action_label"]


def test_action_label_updated_with_suggested_action():
    """downgrade 時 suggested_action 也必須同步更新（不留舊文案）。"""
    result = apply_entry_safety_gate(_base(vol_ratio=0.5))
    assert result["suggested_action"] != "試單"  # 舊 suggested 不應保留


def test_no_null_action_label_in_passing_candidate():
    """通過所有 checks 的 candidate action_label 不應為 null / 空字串。"""
    result = apply_entry_safety_gate(_base())
    assert result.get("action_label")  # truthy


def test_market_range_negative_score_label_not_buy():
    """RANGE + negative score downgrade 時，action_label 也不應是「技術買進」。"""
    result = apply_entry_safety_gate(_base(), market_state="RANGE", market_score=-0.003)
    assert result["action_mode"] == "WATCH_MARKET"
    assert result["action_label"] != "技術買進"
    assert result["action_label"]
