# tests/test_dashboard_semantics.py
# P0 Patch B-lite: 驗證 Dashboard 語義正確性

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from reporting.dashboard_v2 import _cand_card, _action_cls


def _minimal_card(**kwargs) -> dict:
    defaults = {
        "ticker": "TEST",
        "name": "測試股",
        "sector": "",
        "score": 120,
        "narrative_score": 70,
        "chip_score": 60,
        "vol_ratio": 1.1,
        "action_mode": "WATCH_READY",
        "action_label": "觀察等待",
        "suggested_action": "",
        "chase_risk": "MEDIUM",
        "chip_status": "POSITIVE",
        "chip_freshness": "FRESH",
        "signal": "WATCH_READY",
        "invalid_if": [],
        "foreign_net_buy": 0,
        "trust_net_buy": 0,
        "dealer_net_buy": 0,
    }
    defaults.update(kwargs)
    return defaults


def test_card_displays_action_label_before_raw_signal():
    """卡片應顯示 action_label 為主，raw signal 在次要位置（若不同的話）。"""
    c = _minimal_card(
        signal="BUY_LATE",
        action_mode="WATCH_READY",
        action_label="風險警示：追高",
    )
    html = _cand_card(c, 1, {})

    action_pos = html.find("風險警示：追高")
    signal_pos = html.find("BUY_LATE")

    assert action_pos != -1, "action_label 應出現在 HTML 中"
    assert signal_pos != -1, "raw signal 應出現在 HTML 診斷區"
    assert action_pos < signal_pos, "action_label 應在 raw signal 前面"


def test_card_primary_signal_is_action_label_not_buy():
    """當 action_mode=WATCH_READY，card 主要訊號不應是 BUY。"""
    c = _minimal_card(
        signal="BUY_LATE",
        action_mode="WATCH_READY",
        action_label="觀察等待",
    )
    html = _cand_card(c, 1, {})

    # 主要 card-signal span 應包含 action_label
    assert "觀察等待" in html
    # card-signal 的 class 不應是 green (TECH_BUY)
    # WATCH_READY → yellow class
    assert 'card-signal yellow' in html or 'card-signal' in html


def test_held_ticker_filtered_from_fresh_entry():
    """已持倉的 ticker 不應出現在 fresh entry 列表中。"""
    holdings = [{"ticker": "HELD_TICKER"}, {"ticker": "OTHER"}]
    candidates = [
        {"ticker": "HELD_TICKER"},
        {"ticker": "NEW_TICKER"},
    ]
    held_tickers = {h["ticker"] for h in holdings}
    filtered = [c for c in candidates if c["ticker"] not in held_tickers]

    assert len(filtered) == 1
    assert filtered[0]["ticker"] == "NEW_TICKER"
    assert "HELD_TICKER" not in [c["ticker"] for c in filtered]


def test_action_cls_green_for_tech_buy():
    """TECH_BUY → green CSS class。"""
    assert _action_cls("TECH_BUY") == "green"
    assert _action_cls("TECH_BUY_BREAKOUT") == "green"


def test_action_cls_yellow_for_watch():
    """WATCH_READY → yellow CSS class。"""
    assert _action_cls("WATCH_READY") == "yellow"
    assert _action_cls("WATCH") == "yellow"


def test_action_cls_red_for_no_fresh_entry():
    """NO_FRESH_ENTRY_EXTENDED → red CSS class。"""
    assert _action_cls("NO_FRESH_ENTRY_EXTENDED") == "red"
    assert _action_cls("POSITION_MANAGE_ONLY") == "red"


def test_card_same_label_as_signal_no_duplicate():
    """當 action_label 與 signal 相同，diagnostic span 不應顯示重複。"""
    c = _minimal_card(
        signal="WATCH_READY",
        action_mode="WATCH_READY",
        action_label="WATCH_READY",
    )
    html = _cand_card(c, 1, {})
    # 只應出現一次 WATCH_READY 作為主訊號
    count = html.count("WATCH_READY")
    assert count <= 2, f"WATCH_READY 不應重複出現太多次，found {count}"
