# scanner/basic_scanner.py


def scan_candidates(close, volume, features):

    ma20 = features["ma20"]
    vol_ratio = features["vol_ratio"]
    ret_1d = features["return_1d"]

    equipment_list = [
        "2467.TW", "3131.TWO", "3583.TW",
        "5443.TWO", "6139.TW", "2464.TW", "3413.TW"
    ]

    candidates = []

    for col in close.columns:

        try:
            latest_close = close[col].iloc[-1]

            ma10 = close[col].rolling(10).mean().iloc[-1]
            ma20_val = ma20[col].iloc[-1]

            recent_low = close[col].rolling(20).min().iloc[-1]
            recent_high = close[col].rolling(20).max().iloc[-1]

            latest_vol = vol_ratio[col].iloc[-1]
            latest_ret = ret_1d[col].iloc[-1]

            # =========================
            # 🎯 新邏輯（關鍵🔥）
            # =========================

            # 1️⃣ 底部反彈（最重要🔥）
            rebound = latest_close > recent_low * 1.05

            # 2️⃣ 剛站上 MA10（轉強）
            ma10_break = latest_close > ma10

            # 3️⃣ 接近區間上緣（但還沒突破）
            range_high_test = latest_close > recent_high * 0.9

            # 4️⃣ 動能轉正
            momentum_ok = latest_ret > 0

            # 5️⃣ 量能稍微放大（放寬🔥）
            vol_ok = latest_vol > 1.0

            # 6️⃣ 趨勢（不再硬限制）
            trend_soft = latest_close > ma20_val * 0.98

            # 7️⃣ 族群
            sector_boost = 1 if col in equipment_list else 0

            # =========================
            # 🧠 Score（重寫🔥）
            # =========================

            score = (
                rebound * 2 +          # 🔥核心
                ma10_break * 2 +       # 🔥核心
                range_high_test * 1 +
                momentum_ok * 1 +
                vol_ok * 1 +
                trend_soft * 1 +
                sector_boost * 1
            )

            # =========================
            # 🎯 分級
            # =========================

            if score >= 6:
                level = "ATTACK"      # 🔥可以準備進場
            elif score >= 4:
                level = "READY"       # 🔥觀察名單
            else:
                level = "EARLY"

            if score >= 3:
                candidates.append({
                    "ticker": col,
                    "score": score,
                    "level": level,
                    "price": latest_close
                })

        except Exception:
            continue

    candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

    return candidates
