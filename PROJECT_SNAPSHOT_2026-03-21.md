# 📸 Investment OS Snapshot — 2026-03-21

## 🧠 System Status
- pipeline_v0.py restored and stable
- End-to-end pipeline operational
- Telegram notification working
- State system working (anti-duplicate alerts)
- Git baseline committed

---

## 🔧 Core Modules (Current - Monolithic)
- Data: yfinance (US stocks)
- Signal: volume + trend + breakout
- Decision: ENTRY / READY
- Notification: Telegram bot
- State: JSON file (alert_state.json)

---

## 🌏 Taiwan Market Status
- Taiwan tickers verified via yfinance (.TW)
- Data format matches US (Close / Volume)
- Not yet integrated into pipeline (intentional isolation)
- Separate test file: test_tw_data.py

---

## ⚠️ Known Issues (Resolved)
- Broken venv → rebuilt
- JSON state corruption → handled manually
- Telegram inconsistency → fixed send function
- Syntax errors → cleaned

---

## 🧠 Key Lessons
- Only change ONE thing at a time
- Never mix state / signal / notification changes
- Always keep a stable Git checkpoint
- Avoid debugging inside production code

---

## 🏗 Architecture Insight
Current:
- Single file (pipeline_v0.py)

Problem:
- Data / Signal / Execution / Infra tightly coupled

Future:
- Modular architecture:
  - data/
  - signal/
  - execution/
  - infra/
  - pipeline.py

---

## 🚀 Next Steps
1. Create TW universe module
2. Integrate TW tickers safely (non-breaking)
3. Build US → TW signal mapping
4. Improve ENTRY quality (reduce noise)
5. Gradual modularization (NOT immediate)

---

## 🧘 Status Summary
System restored from chaos → stable baseline achieved.

Next phase: controlled expansion (no more large refactors).
