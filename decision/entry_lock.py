# =========================================================
# decision/entry_lock.py
# =========================================================

def apply_entry_lock(close, volume, entry_signals):

    results = []

    for e in entry_signals:

        ticker = e["ticker"]
        signal = e["signal"]

        if signal != "BUY":
            continue

        try:
            price = close[ticker].iloc[-1]

            ma5 = close[ticker].rolling(5).mean().iloc[-1]
            ma10 = close[ticker].rolling(10).mean().iloc[-1]

            vol = volume[ticker].iloc[-1]
            vol_avg = volume[ticker].rolling(10).mean().iloc[-1]

            # =========================
            # L2 Setup Lock
            # =========================
            near_ma5 = price < ma5 * 1.03
            not_too_extended = price < ma10 * 1.10

            setup_ok = near_ma5 and not_too_extended

            # =========================
            # L3 Validation Lock
            # =========================
            vol_confirm = vol > vol_avg
            not_fake = price > ma5

            validation_ok = vol_confirm and not_fake

            # =========================
            # L4 Risk Lock
            # =========================
            risk_ok = price > ma10

            # =========================
            # Final Decision
            # =========================
            if setup_ok and validation_ok and risk_ok:
                decision = "BUY"
            elif setup_ok:
                decision = "BUY_PARTIAL"
            else:
                decision = "BLOCK"

            results.append({
                "ticker": ticker,
                "decision": decision,
                "price": float(price)
            })

        except:
            continue

    return results
