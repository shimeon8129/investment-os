# signal_engine/entry.py

def generate_entry_signal(close, volume, features, candidate_info=None):
    """
    Entry Signal v3（整合 Scanner READY）

    Signals:
    - BUY_BREAKOUT
    - BUY_LATE
    - TREND_CONTINUE
    - READY_PULLBACK
    - BUY（🔥 由 READY 觸發）
    """

    ma5 = features["ma5"]
    vol_ratio = features["vol_ratio"]

    signals = {}

    for col in close.columns:

        # === 防呆 ===
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
        # 1. BREAKOUT
        # =====================================
        if latest_close > prev_high and latest_vol > 1.2:
            signals[col] = "BUY_BREAKOUT"

        # =====================================
        # 2. LATE ENTRY
        # =====================================
        elif (
            latest_close > latest_ma5 and
            latest_vol > 1.2 and
            latest_close > prev_close
        ):
            signals[col] = "BUY_LATE"

        # =====================================
        # 3. TREND
        # =====================================
        elif latest_close > latest_ma5 and latest_vol > 1.0:
            signals[col] = "TREND_CONTINUE"

        # =====================================
        # 4. PULLBACK
        # =====================================
        elif latest_close < prev_high and latest_close > latest_ma5:
            signals[col] = "READY_PULLBACK"

        else:
            signals[col] = ""

        # =====================================
        # 🔥 5. READY 升級（核心）
        # =====================================
        if candidate_info and col in candidate_info:

            level = candidate_info[col].get("level")

            if level == "READY":
                signals[col] = "BUY"   # 🔥 覆蓋所有其他 signal

    return signals
