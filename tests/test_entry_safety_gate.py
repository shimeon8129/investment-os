# tests/test_entry_safety_gate.py
# P0 Patch C-lite: 驗證 Entry Safety Gate 的 4 個 hard block 條件

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from decision.entry_safety_gate import apply_entry_safety_gate


def _base(**kwargs) -> dict:
    """Safe-passing base candidate."""
    defaults = {
        "ticker": "TEST",
        "action_mode": "TECH_BUY",
        "vol_ratio": 1.2,
        "chip_status": "POSITIVE",
        "chase_risk": "LOW",
        "is_held": False,
    }
    defaults.update(kwargs)
    return defaults


def test_low_volume_blocks_buy():
    """vol_ratio < 1.0 → WATCH_READY，不是 TECH_BUY。"""
    result = apply_entry_safety_gate(_base(vol_ratio=0.8))
    assert result["action_mode"] == "WATCH_READY"
    assert "vol_ratio=0.80<1.0" in result["downgrade_reasons"]


def test_chip_divergence_blocks_buy():
    """chip_status=DIVERGENCE → WATCH_READY。"""
    result = apply_entry_safety_gate(_base(chip_status="DIVERGENCE"))
    assert result["action_mode"] == "WATCH_READY"
    assert any("chip_status" in r for r in result["downgrade_reasons"])


def test_chip_strong_divergence_blocks_buy():
    """chip_status=STRONG_DIVERGENCE → WATCH_READY。"""
    result = apply_entry_safety_gate(_base(chip_status="STRONG_DIVERGENCE"))
    assert result["action_mode"] == "WATCH_READY"


def test_chip_strong_negative_blocks_buy():
    """chip_status=STRONG_NEGATIVE → WATCH_READY。"""
    result = apply_entry_safety_gate(_base(chip_status="STRONG_NEGATIVE"))
    assert result["action_mode"] == "WATCH_READY"


def test_high_chase_risk_blocks_buy():
    """chase_risk=HIGH → NO_FRESH_ENTRY_EXTENDED。"""
    result = apply_entry_safety_gate(_base(chase_risk="HIGH"))
    assert result["action_mode"] == "NO_FRESH_ENTRY_EXTENDED"
    assert any("chase_risk" in r for r in result["downgrade_reasons"])


def test_extreme_chase_risk_blocks_buy():
    """chase_risk=EXTREME → NO_FRESH_ENTRY_EXTENDED。"""
    result = apply_entry_safety_gate(_base(chase_risk="EXTREME"))
    assert result["action_mode"] == "NO_FRESH_ENTRY_EXTENDED"


def test_held_ticker_position_manage_only():
    """is_held=True → POSITION_MANAGE_ONLY。"""
    result = apply_entry_safety_gate(_base(is_held=True))
    assert result["action_mode"] == "POSITION_MANAGE_ONLY"
    assert "ticker_already_held" in result["downgrade_reasons"]


def test_all_conditions_pass():
    """全部 checks 通過時，gate_passed=True，action_mode 不變。"""
    candidate = _base()
    result = apply_entry_safety_gate(candidate)
    assert result.get("gate_passed") is True
    assert result["action_mode"] == "TECH_BUY"
    assert result["downgrade_reasons"] == []


def test_volume_check_takes_priority_over_chip():
    """vol_ratio block 先執行，chip block 不影響 downgrade_reason。"""
    result = apply_entry_safety_gate(_base(vol_ratio=0.5, chip_status="DIVERGENCE"))
    assert result["action_mode"] == "WATCH_READY"
    assert any("vol_ratio" in r for r in result["downgrade_reasons"])
    # chip reason should not appear (vol fired first)
    assert not any("chip_status" in r for r in result["downgrade_reasons"])


def test_missing_fields_use_safe_defaults():
    """缺少欄位時使用安全預設值，不應 block。"""
    result = apply_entry_safety_gate({"ticker": "BARE"})
    assert result.get("gate_passed") is True
