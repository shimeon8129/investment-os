# signal_engine/entry.py

def generate_entry_signal(close, volume, features):
    """
    根據價格 / 均線 / 成交量 產生交易訊號

    Signals:
    - BUY_BREAKOUT     → 突破（最強）
    - BUY_LATE         → 強勢追擊（次強）
    - TREND_CONTINUE   → 持續上升（不追）
    - READY_PULLBACK   → 回檔準備
    - ""               → 無訊號
    """

    ma5 = features["ma5"]
    vol_ratio = features["vol_ratio"]

    signals = {}

    for col in close.columns:

        # === 防呆（避免資料不足）===
        if len(close[col]) < 20:
            signals[col] = ""
            continue

        try:
            latest_close = close[col].iloc[-1]
            prev_close = close[col].iloc[-2]
            prev_high = close[col].rolling(20).max().iloc[-2]

            latest_ma5 = ma5[col].iloc[-1]
            latest_vol = vol_ratio[col].iloc[-1]

        except Exception:
            signals[col] = ""
            continue

        # =====================================
        # 🔥 1. BREAKOUT（最強訊號）
        # =====================================
        if latest_close > prev_high and latest_vol > 1.2:
            signals[col] = "BUY_BREAKOUT"
            continue

        # =====================================
        # 🔥 2. LATE ENTRY（追擊）
        # =====================================
        if (
            latest_close > latest_ma5 and
            latest_vol > 1.2 and
            latest_close > prev_close
        ):
            signals[col] = "BUY_LATE"
            continue

        # =====================================
        # 🟡 3. TREND（已在上升）
        # =====================================
        if latest_close > latest_ma5 and latest_vol > 1.0:
            signals[col] = "TREND_CONTINUE"
            continue

        # =====================================
        # 🟠 4. PULLBACK（準備區）
        # =====================================
        pullback = latest_close < prev_high
        hold_ma5 = latest_close > latest_ma5

        if pullback and hold_ma5:
            signals[col] = "READY_PULLBACK"
            continue

        # =====================================
        # ❌ 5. NO SIGNAL
        # =====================================
        signals[col] = ""

    return signals
