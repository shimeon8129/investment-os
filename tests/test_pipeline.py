# tests/test_pipeline.py

import sys
import os

# ✅ 修正 path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data_node.loader import load_price_data
from processing.features import compute_features
from signal_engine.entry import generate_entry_signal
from execution.trade import execute_trade
from execution.exit import check_exit

# ==============================
# 🏷️ 股票名稱對照
# ==============================

name_map = {
    "2467.TW": "志聖",
    "3131.TWO": "弘塑",
    "3583.TW": "辛耘",
}

# ==============================
# 🔧 格式化工具
# ==============================

def fmt_pct(x):
    if isinstance(x, float):
        return f"{x*100:.1f}%"
    return x

# ==============================
# 📊 Data
# ==============================

tickers = ["2467.TW", "3131.TWO", "3583.TW"]

close, volume = load_price_data(tickers)

features = compute_features(close, volume)

# ==============================
# 🧠 Signal
# ==============================

signals = generate_entry_signal(close, volume, features)

print("=== SIGNAL ===")

for ticker, sig in signals.items():
    name = name_map.get(ticker, "")
    print(f"{ticker} {name} → {sig}")

# ==============================
# 🟩 Decision
# ==============================

decisions = execute_trade(signals)

print("\n=== DECISION ===")

for ticker, d in decisions.items():
    name = name_map.get(ticker, "")
    action = d.get("action")

    if action == "BUY":
        size = fmt_pct(d.get("position_size"))
        sl = fmt_pct(d.get("stop_loss"))

        print(f"{ticker} {name} → BUY | 倉位: {size} | 停損: {sl}")

    else:
        print(f"{ticker} {name} → {action}")

# ==============================
# 🟥 Exit
# ==============================

print("\n=== EXIT CHECK ===")

# 模擬持倉（3583）
position = {
    "entry_price": close["3583.TW"].iloc[-3],
    "size": 0.15
}

current_price = close["3583.TW"].iloc[-1]
ma5 = features["ma5"]["3583.TW"].iloc[-1]
highest_price = close["3583.TW"].max()

exit_signal = check_exit(
    position,
    current_price,
    ma5,
    highest_price
)

print(f"3583.TW 辛耘 → {exit_signal}")
