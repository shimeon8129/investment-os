# =========================================================
# decision/ready_predictor.py
# READY → BUY 預測模型 v1
# =========================================================

def predict_ready_breakout(close, volume, entry_signals):

    results = []

    for e in entry_signals:

        ticker = e["ticker"]
        signal = e["signal"]

        if signal != "READY":
            continue

        try:
            price = close[ticker].iloc[-1]

            ma5 = close[ticker].rolling(5).mean().iloc[-1]
            ma10 = close[ticker].rolling(10).mean().iloc[-1]
            ma20 = close[ticker].rolling(20).mean().iloc[-1]

            vol = volume[ticker].iloc[-1]
            vol_avg10 = volume[ticker].rolling(10).mean().iloc[-1]

            # =========================
            # 1️⃣ 趨勢結構（一定要多頭）
            # =========================
            trend_ok = price > ma20

            # =========================
            # 2️⃣ 貼近5MA（壓縮）
            # =========================
            near_ma5 = abs(price - ma5) / ma5 < 0.02

            # =========================
            # 3️⃣ 不過度延伸
            # =========================
            not_extended = price < ma10 * 1.05

            # =========================
            # 4️⃣ 量縮（關鍵🔥）
            # =========================
            vol_contract = vol < vol_avg10

            # =========================
            # 🔥 評分系統
            # =========================
            score = 0

            if trend_ok:
                score += 1

            if near_ma5:
                score += 1

            if not_extended:
                score += 1

            if vol_contract:
                score += 1

            # =========================
            # 🔥 分級
            # =========================
            if score >= 4:
                level = "READY_A"   # 🔥 高機率爆發
            elif score == 3:
                level = "READY_B"
            else:
                level = "WEAK"

            results.append({
                "ticker": ticker,
                "level": level,
                "score": score,
                "price": float(price)
            })

        except:
            continue

    return results
