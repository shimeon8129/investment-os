# tests/test_entry_safety_gate.py
# P0.1: Entry Safety Gate — 完整驗收測試

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from decision.entry_safety_gate import apply_entry_safety_gate


def _base(**kwargs) -> dict:
    """Safe-passing base candidate（所有必要欄位齊全）。"""
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


# ─── Block 0: is_held（最高優先）─────────────────────────────────────────────

def test_held_ticker_position_manage_only():
    """is_held=True → POSITION_MANAGE_ONLY，action_label 同步更新。"""
    result = apply_entry_safety_gate(_base(is_held=True))
    assert result["action_mode"] == "POSITION_MANAGE_ONLY"
    assert result["action_label"] == "持倉管理"
    assert "ticker_already_held" in result["downgrade_reasons"]


def test_held_ticker_overrides_all_other_blockers():
    """is_held=True 時，即使其他 block 條件同時存在，仍回傳 POSITION_MANAGE_ONLY。"""
    result = apply_entry_safety_gate(_base(
        is_held=True,
        vol_ratio=0.5,
        chip_status="DIVERGENCE",
        chase_risk="EXTREME",
    ))
    assert result["action_mode"] == "POSITION_MANAGE_ONLY"
    # 只應有 ticker_already_held，不應疊加其他 reason
    assert result["downgrade_reasons"] == ["ticker_already_held"]


# ─── Block 1: Missing Fields ───────────────────────────────────────────────────

def test_missing_vol_ratio_downgrades():
    """缺少 vol_ratio → DATA_INCOMPLETE_REVIEW，不是 gate_pass。"""
    c = {"ticker": "X", "action_mode": "TECH_BUY",
         "chip_status": "POSITIVE", "chase_risk": "LOW", "is_held": False}
    result = apply_entry_safety_gate(c)
    assert result["action_mode"] == "DATA_INCOMPLETE_REVIEW"
    assert result.get("gate_passed") is not True
    assert "vol_ratio" in result["downgrade_reasons"][0]


def test_missing_chip_status_downgrades():
    """缺少 chip_status → DATA_INCOMPLETE_REVIEW。"""
    c = {"ticker": "X", "action_mode": "TECH_BUY",
         "vol_ratio": 1.2, "chase_risk": "LOW", "is_held": False}
    result = apply_entry_safety_gate(c)
    assert result["action_mode"] == "DATA_INCOMPLETE_REVIEW"


def test_missing_chase_risk_downgrades():
    """缺少 chase_risk → DATA_INCOMPLETE_REVIEW。"""
    c = {"ticker": "X", "action_mode": "TECH_BUY",
         "vol_ratio": 1.2, "chip_status": "POSITIVE", "is_held": False}
    result = apply_entry_safety_gate(c)
    assert result["action_mode"] == "DATA_INCOMPLETE_REVIEW"


def test_missing_all_critical_fields_downgrades():
    """三個關鍵欄位都缺 → DATA_INCOMPLETE_REVIEW，reason 包含全部欄位名。"""
    result = apply_entry_safety_gate({"ticker": "BARE", "is_held": False})
    assert result["action_mode"] == "DATA_INCOMPLETE_REVIEW"
    assert result.get("gate_passed") is not True
    reason = result["downgrade_reasons"][0]
    assert "vol_ratio" in reason
    assert "chip_status" in reason
    assert "chase_risk" in reason


# ─── Block 2: Market State ─────────────────────────────────────────────────────

def test_range_negative_score_blocks_full_buy():
    """RANGE + market_score < 0 → WATCH_MARKET，不允許 TECH_BUY / TECH_ATTACK。"""
    result = apply_entry_safety_gate(_base(), market_state="RANGE", market_score=-0.002)
    assert result["action_mode"] == "WATCH_MARKET"
    assert result["action_label"] == "市場觀望"
    assert result.get("gate_passed") is not True
    assert "market_state=RANGE" in result["downgrade_reasons"][0]


def test_range_positive_score_allows_buy():
    """RANGE + market_score >= 0 → 不觸發市場 block。"""
    result = apply_entry_safety_gate(_base(), market_state="RANGE", market_score=0.001)
    assert result["action_mode"] != "WATCH_MARKET"


def test_bull_with_negative_score_allows_buy():
    """BULL + negative score → 不觸發 RANGE block（只有 RANGE 才受限）。"""
    result = apply_entry_safety_gate(_base(), market_state="BULL", market_score=-0.005)
    assert result["action_mode"] != "WATCH_MARKET"


def test_range_score_exactly_zero_allows_buy():
    """RANGE + market_score == 0.0 → 不觸發 block（< 0 才封鎖）。"""
    result = apply_entry_safety_gate(_base(), market_state="RANGE", market_score=0.0)
    assert result["action_mode"] != "WATCH_MARKET"


# ─── Block 3: Volume ───────────────────────────────────────────────────────────

def test_low_volume_blocks_buy():
    """vol_ratio < 1.0 → WATCH_READY，action_label 同步更新。"""
    result = apply_entry_safety_gate(_base(vol_ratio=0.8))
    assert result["action_mode"] == "WATCH_READY"
    assert result["action_label"] == "量能不足觀察"
    assert "vol_ratio=0.80<1.0" in result["downgrade_reasons"]


# ─── Block 4: Chip Status ──────────────────────────────────────────────────────

def test_chip_divergence_blocks_buy():
    """chip_status=DIVERGENCE → WATCH_READY，action_label 同步更新。"""
    result = apply_entry_safety_gate(_base(chip_status="DIVERGENCE"))
    assert result["action_mode"] == "WATCH_READY"
    assert result["action_label"] == "籌碼分歧觀察"
    assert any("chip_status" in r for r in result["downgrade_reasons"])


def test_chip_strong_divergence_blocks_buy():
    """chip_status=STRONG_DIVERGENCE → WATCH_READY。"""
    result = apply_entry_safety_gate(_base(chip_status="STRONG_DIVERGENCE"))
    assert result["action_mode"] == "WATCH_READY"


def test_chip_strong_negative_blocks_buy():
    """chip_status=STRONG_NEGATIVE → WATCH_READY。"""
    result = apply_entry_safety_gate(_base(chip_status="STRONG_NEGATIVE"))
    assert result["action_mode"] == "WATCH_READY"


# ─── Block 5: Chase Risk ───────────────────────────────────────────────────────

def test_high_chase_risk_blocks_buy():
    """chase_risk=HIGH → NO_FRESH_ENTRY_EXTENDED，action_label 同步更新。"""
    result = apply_entry_safety_gate(_base(chase_risk="HIGH"))
    assert result["action_mode"] == "NO_FRESH_ENTRY_EXTENDED"
    assert result["action_label"] == "追價風險過高"
    assert any("chase_risk" in r for r in result["downgrade_reasons"])


def test_extreme_chase_risk_blocks_buy():
    """chase_risk=EXTREME → NO_FRESH_ENTRY_EXTENDED。"""
    result = apply_entry_safety_gate(_base(chase_risk="EXTREME"))
    assert result["action_mode"] == "NO_FRESH_ENTRY_EXTENDED"


# ─── Pass Case ─────────────────────────────────────────────────────────────────

def test_all_conditions_pass():
    """全部 checks 通過 → gate_passed=True，action_mode / action_label 不變。"""
    candidate = _base()
    result = apply_entry_safety_gate(candidate)
    assert result.get("gate_passed") is True
    assert result["action_mode"] == "TECH_BUY"
    assert result["action_label"] == "技術買進"
    assert result["downgrade_reasons"] == []


# ─── Priority Order ────────────────────────────────────────────────────────────

def test_held_fires_before_missing_fields():
    """is_held 應在 missing fields 之前執行。"""
    c = {"ticker": "X", "is_held": True}  # 完全沒有 vol_ratio/chip_status/chase_risk
    result = apply_entry_safety_gate(c)
    assert result["action_mode"] == "POSITION_MANAGE_ONLY"


def test_missing_fires_before_market_state():
    """missing fields 應在 market_state 之前執行。"""
    c = {"ticker": "X", "is_held": False}  # 缺欄位
    result = apply_entry_safety_gate(c, market_state="RANGE", market_score=-0.01)
    assert result["action_mode"] == "DATA_INCOMPLETE_REVIEW"


def test_market_fires_before_volume():
    """market_state block 應在 volume block 之前執行。"""
    result = apply_entry_safety_gate(
        _base(vol_ratio=0.5),
        market_state="RANGE",
        market_score=-0.01,
    )
    assert result["action_mode"] == "WATCH_MARKET"
    assert not any("vol_ratio" in r for r in result["downgrade_reasons"])
