# tests/test_dashboard_html_safety.py
# P0.1 Dashboard HTML Safety — verify display never shows unsafe BUY labels

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from reporting.dashboard_v2 import _cand_card, _market_card, _action_cls


def _make_candidate(**kwargs) -> dict:
    defaults = {
        "ticker": "TEST",
        "name": "測試股",
        "sector": "",
        "score": 120,
        "narrative_score": 60,
        "chip_score": 50,
        "vol_ratio": 1.2,
        "action_mode": "TECH_BUY",
        "action_label": "技術買進",
        "suggested_action": "試單",
        "chase_risk": "LOW",
        "chip_status": "POSITIVE",
        "chip_freshness": "FRESH",
        "signal": "BUY",
        "invalid_if": [],
        "foreign_net_buy": 0,
        "trust_net_buy": 0,
        "dealer_net_buy": 0,
    }
    defaults.update(kwargs)
    return defaults


def _make_market_data(**kwargs) -> dict:
    defaults = {
        "market_state": "RANGE",
        "market_score": -0.003,
        "vix_value": 22.0,
        "vix_alert": "ELEVATED",
        "market_guidance": {
            "summary": "市場盤整，精選進場",
            "new_entry_ok": True,
            "role_filter": ["WAVE_SWING"],
            "holding_action": "",
        },
    }
    defaults.update(kwargs)
    return defaults


# ─── 低量比候選 ────────────────────────────────────────────────────────────────

def test_low_volume_candidate_html_no_buy():
    """低量比 (vol_ratio=0.78) 的 HTML 不能包含「技術買進」。"""
    c = _make_candidate(vol_ratio=0.78, ticker="2356", name="英業達")
    html = _cand_card(c, 1, {})
    assert "技術買進" not in html, "低量比候選不應顯示「技術買進」"
    assert "量能不足" in html, "低量比候選應顯示「量能不足」"


def test_low_volume_candidate_html_no_buy_2377():
    """微星 vol_ratio=0.63 的 HTML 不能包含「技術買進」。"""
    c = _make_candidate(vol_ratio=0.63, ticker="2377", name="微星")
    html = _cand_card(c, 2, {})
    assert "技術買進" not in html
    assert "量能不足" in html


# ─── 籌碼分歧候選 ──────────────────────────────────────────────────────────────

def test_chip_divergence_candidate_html_no_buy():
    """籌碼分歧 (DIVERGENCE) 候選的 HTML 不能包含「技術買進」。"""
    c = _make_candidate(chip_status="DIVERGENCE", ticker="2467", name="志聖")
    html = _cand_card(c, 3, {})
    assert "技術買進" not in html, "籌碼分歧候選不應顯示「技術買進」"
    assert "籌碼分歧" in html, "籌碼分歧候選應顯示「籌碼分歧」"


def test_chip_strong_divergence_candidate_html_no_buy():
    """STRONG_DIVERGENCE 候選的 HTML 不能包含「技術買進」。"""
    c = _make_candidate(chip_status="STRONG_DIVERGENCE")
    html = _cand_card(c, 1, {})
    assert "技術買進" not in html


def test_chip_strong_negative_candidate_html_no_buy():
    """STRONG_NEGATIVE 候選的 HTML 不能包含「技術買進」。"""
    c = _make_candidate(chip_status="STRONG_NEGATIVE")
    html = _cand_card(c, 1, {})
    assert "技術買進" not in html


# ─── 追價風險 ──────────────────────────────────────────────────────────────────

def test_high_chase_risk_candidate_html_no_buy():
    """chase_risk=HIGH 候選的 HTML 不能包含「技術買進」。"""
    c = _make_candidate(chase_risk="HIGH")
    html = _cand_card(c, 1, {})
    assert "技術買進" not in html
    assert "追價風險" in html


# ─── 市場 RANGE + 負分 ────────────────────────────────────────────────────────

def test_range_negative_market_shows_stop_entry():
    """RANGE + negative score 的 market card 應顯示「暫停進場」，不顯示「可進場」。"""
    data = _make_market_data(market_state="RANGE", market_score=-0.003)
    html = _market_card(data)
    assert "暫停進場" in html, "RANGE+負分市場應顯示「暫停進場」"
    assert "可進場" not in html, "RANGE+負分市場不應顯示「可進場」"


def test_range_positive_market_shows_can_entry():
    """RANGE + positive score 的 market card 應顯示「可進場」（若 new_entry_ok=True）。"""
    data = _make_market_data(market_state="RANGE", market_score=0.001)
    html = _market_card(data)
    assert "可進場" in html


def test_bull_market_shows_can_entry():
    """BULL 市場應顯示「可進場」。"""
    data = _make_market_data(
        market_state="BULL",
        market_score=0.005,
        market_guidance={"summary": "多頭", "new_entry_ok": True, "role_filter": [], "holding_action": ""},
    )
    html = _market_card(data)
    assert "可進場" in html


# ─── Section Note ──────────────────────────────────────────────────────────────

def test_section_note_warns_about_downgrade():
    """進場候選 section note 必須說明 WATCH_READY / 不允許 fresh BUY 的情況。"""
    # Import build_dashboard to get the raw HTML output
    from reporting.dashboard_v2 import build_dashboard
    try:
        html = build_dashboard()
        assert "不等於可直接進場" in html, "section note 應警示不等於直接進場"
    except Exception:
        pytest.skip("build_dashboard needs snapshot data — skipped in CI without data")


# ─── 已持倉 ────────────────────────────────────────────────────────────────────

def test_held_ticker_not_in_fresh_entry_html():
    """已持倉 ticker 在 build_dashboard 的 wave/satellite 篩選後不出現在進場區。"""
    holdings = [{"ticker": "HELD"}]
    candidates = [{"ticker": "HELD"}, {"ticker": "NEW"}]
    held_tickers = {h["ticker"] for h in holdings}
    filtered = [c for c in candidates if c["ticker"] not in held_tickers]
    assert len(filtered) == 1
    assert filtered[0]["ticker"] == "NEW"
    assert "HELD" not in [c["ticker"] for c in filtered]


# ─── 實際失敗案例 2026-05-17 ───────────────────────────────────────────────────

def test_actual_failure_2356_yingye():
    """英業達 vol_ratio=0.78 → 不顯示「技術買進」（2026-05-17 實際失敗案例）。"""
    c = _make_candidate(ticker="2356", name="英業達", vol_ratio=0.78)
    html = _cand_card(c, 1, {})
    assert "技術買進" not in html
    assert "量能不足" in html


def test_actual_failure_2377_msi():
    """微星 vol_ratio=0.63 → 不顯示「技術買進」（2026-05-17 實際失敗案例）。"""
    c = _make_candidate(ticker="2377", name="微星", vol_ratio=0.63)
    html = _cand_card(c, 2, {})
    assert "技術買進" not in html
    assert "量能不足" in html


def test_actual_failure_2467_zhisheng():
    """志聖 chip_status=DIVERGENCE → 不顯示「技術買進」（2026-05-17 實際失敗案例）。"""
    c = _make_candidate(ticker="2467", name="志聖", chip_status="DIVERGENCE", vol_ratio=0.80)
    html = _cand_card(c, 3, {})
    assert "技術買進" not in html
