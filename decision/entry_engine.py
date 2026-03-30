# =========================================================
# decision/entry_engine.py
# =========================================================

def generate_entry_signal(close, volume):

    results = []

    for col in close.columns:

        try:
            price = close[col].iloc[-1]

            ma5 = close[col].rolling(5).mean().iloc[-1]
            ma10 = close[col].rolling(10).mean().iloc[-1]

            vol = volume[col].iloc[-1]
            vol_avg = volume[col].rolling(10).mean().iloc[-1]

            prev_high = close[col].rolling(10).max().iloc[-2]

            # =========================
            # READY
            # =========================
            pullback = price < ma5 * 1.02
            support = price > ma5 * 0.98
            vol_contract = vol < vol_avg

            ready = pullback and support and vol_contract

            # =========================
            # BUY
            # =========================
            breakout = price > prev_high

            signal = ""
            if ready:
                signal = "READY"

            if ready and breakout:
                signal = "BUY"

            results.append({
                "ticker": col,
                "signal": signal,
                "price": float(price)
            })

        except:
            continue

    return results
