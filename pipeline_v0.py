import yfinance as yf
import pandas as pd
import requests
import json
import os

# ======================
# 🔧 Telegram 設定（填你的）
# ======================
TOKEN = "8315568434:AAE4uY5t-rvqJHb9UIuuUS-73lpj305aoNw"
CHAT_ID = "7934011157"

STATE_FILE = "alert_state.json"


# ======================
# 🔄 防重複通知
# ======================
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ======================
# Data
# ======================
def get_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.rename(columns={"Close": "price", "Volume": "volume"})

    df["ma20"] = df["price"].rolling(20).mean()
    df["avg_volume20"] = df["volume"].rolling(20).mean()
    df["high20"] = df["price"].rolling(20).max()

    latest = df.iloc[-1]

    return {
        "ticker": ticker,
        "price": float(latest["price"]),
        "volume": float(latest["volume"]),
        "ma20": float(latest["ma20"]),
        "avg_volume20": float(latest["avg_volume20"]),
        "high20": float(latest["high20"])
    }


# ======================
# Signal
# ======================
def generate_signal(data):
    volume_ratio = data["volume"] / data["avg_volume20"]
    trend_ratio = data["price"] / data["ma20"]
    breakout_gap = data["price"] - data["high20"]

    trend_score = min(trend_ratio, 1.2)
    volume_score = min(volume_ratio, 1.5)
    breakout_score = max(0, 1 + breakout_gap / 10)

    composite = round(trend_score + volume_score + breakout_score, 2)

    return {
        "ticker": data["ticker"],
        "price": round(data["price"], 2),
        "volume_ratio": round(volume_ratio, 2),
        "trend_ratio": round(trend_ratio, 2),
        "breakout_gap": round(breakout_gap, 2),
        "composite": composite
    }


# ======================
# Logic
# ======================
def get_alert(gap):
    if gap > 0:
        return "🚀 BREAKOUT"
    elif gap > -1:
        return "🔥 READY"
    elif gap > -2:
        return "👀 WATCH"
    return ""


def check_entry(s):
    if s["breakout_gap"] >= 0 and s["volume_ratio"] > 1.2 and s["trend_ratio"] > 1:
        return "✅ ENTRY"
    elif s["breakout_gap"] > -1 and s["trend_ratio"] > 1:
        return "⚠️ PREPARE"
    return ""


def check_exit(s, entry_price=None):
    if entry_price is None:
        return ""

    price = s["price"]
    ma20 = price / s["trend_ratio"]

    if price < ma20:
        return "❌ STOP LOSS"
    if price > entry_price * 1.1:
        return "💰 TAKE PROFIT"
    return ""


# ======================
# Position
# ======================
def calculate_position(s, capital=1000000, risk_pct=0.01, max_pct=0.2):

    # 只對 ENTRY 給倉位
    if check_entry(s) != "✅ ENTRY":
        return 0

    price = s["price"]
    ma20 = price / s["trend_ratio"]

    risk_per_share = price - ma20

    if risk_per_share <= 0:
        return 0

    if risk_per_share < price * 0.01:
        return 0

    risk_amount = capital * risk_pct
    risk_position = int(risk_amount / risk_per_share)

    cap_position = int((capital * max_pct) / price)

    return min(risk_position, cap_position)


# ======================
# Telegram（含 debug）
# ======================
def send_telegram(msg):
    print("📤 SEND:", msg)

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}

    try:
        r = requests.post(url, data=data)
        print("📡 RESPONSE:", r.text)
    except Exception as e:
        print("❌ ERROR:", e)


# ======================
# 🚀 MAIN
# ======================
if __name__ == "__main__":

    tickers = [
        "NVDA", "AMD", "AVGO", "MU", "INTC",
        "TSM", "ASML", "AMAT", "LRCX", "KLAC",
        "SMH", "SOXX",
        "QCOM", "MRVL", "TXN",
        "ANET", "DELL", "HPQ"
    ]

    state = load_state()
    results = []

    # 1️⃣ 抓資料
    for t in tickers:
        try:
            data = get_data(t)
            signal = generate_signal(data)
            results.append(signal)
        except:
            continue

    # 2️⃣ 排序
    ranked = sorted(results, key=lambda x: x["composite"], reverse=True)

    # 3️⃣ 假設持倉
    portfolio = {"DELL": 160}

    print("\n=== RANKING ===")

    # 4️⃣ 主邏輯
    for r in ranked:

        ticker = r["ticker"]
        alert = get_alert(r["breakout_gap"])
        entry = check_entry(r)
        exit_signal = check_exit(r, portfolio.get(ticker))
        size = calculate_position(r)

        print(f'{ticker} | score:{r["composite"]} | gap:{r["breakout_gap"]} {alert} {entry} {exit_signal} | size:{size}')

        # 🔥 防重複通知
        prev_signal = state.get(ticker, "")
        current_signal = entry if entry == "✅ ENTRY" else alert

        if current_signal != "" and current_signal != prev_signal:

            msg = f'{ticker} | {current_signal} | price:{r["price"]}'
            send_telegram(msg)

            state[ticker] = current_signal

    # 5️⃣ 存 state
    save_state(state)

    # 6️⃣ 機會清單
    print("\n=== OPPORTUNITIES ===")
    for r in ranked:
        if r["breakout_gap"] > -5:
            print(f'{r["ticker"]} | gap:{r["breakout_gap"]}')
