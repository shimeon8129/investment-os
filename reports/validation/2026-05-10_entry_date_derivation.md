# Holdings Entry Date Derivation — 2026-05-10

**分析目的：** 為 `current_holdings.json` 中的每筆持倉推導 `entry_date`，供 Role-Based Position Model 使用。
**限制：** 此為分析報告，不修改任何持倉檔案。所有結果待 owner/GPT 審閱後方可套用。

---

## 摘要表

| Ticker | 名稱 | 提議進場日 | 信心度 | 資料來源 | 建議動作 |
| --- | --- | --- | --- | --- | --- |
| 009816 | 凱基台灣TOP50 | 2026-04-13 | LOW | yfinance price match ±2% before 2026-04-30 (best: ... | ⚠️ 需 owner 確認 |
| 00992A | 主動群益科技創新 | 2026-04-29 | LOW | yfinance price match ±2% before 2026-04-30 (best: ... | ⚠️ 需 owner 確認 |
| 2330 | 台積電 | 2026-03-31 | LOW | yfinance price match ±2% before 2026-04-30 (best: ... | ⚠️ 需 owner 確認 |
| 2345 | 智邦 | 2026-04-13 | LOW | yfinance price match ±2% before 2026-04-30 (best: ... | ⚠️ 需 owner 確認 |
| 2408 | 南亞科 | 2026-04-29 | LOW | yfinance price match ±2% before 2026-04-30 (best: ... | ⚠️ 需 owner 確認 |
| 3711 | 日月光投控 | 2026-04-13 | LOW | yfinance price match ±2% before 2026-04-30 (best: ... | ⚠️ 需 owner 確認 |
| 6830 | 汎銓 | 2026-04-28 | LOW | yfinance price match ±2% before 2026-04-30 (best: ... | ⚠️ 需 owner 確認 |

---

## 信心度分佈

| 信心度 | 筆數 |
| --- | --- |
| LOW | 7 |

---

## 各持倉推導明細

### 009816 凱基台灣TOP50

- **數量：** 5000
- **進場價：** 11.4
- **成本：** 57000
- **提議進場日：** `2026-04-13`
- **信心度：** LOW
- **資料來源：** yfinance price match ±2% before 2026-04-30 (best: 2026-04-13 @ 11.38)
- **推導理由：** No repo evidence of exact entry date. Most recent date (before 2026-04-30) with close ≈ entry_price 11.4: 2026-04-13 (close=11.38, diff=-0.2%). Price match is not conclusive — 8 candidate date(s) found.
- **價格比對候選日（前5筆，最近優先）：**
  - 2026-04-13 close=11.38 (-0.2%)
  - 2026-04-10 close=11.4 (-0.0%)
  - 2026-04-09 close=11.19 (-1.8%)
  - 2026-04-08 close=11.23 (-1.5%)
  - 2026-03-02 close=11.32 (-0.7%)
- **建議動作：** ⚠️ 需 owner 確認

### 00992A 主動群益科技創新

- **數量：** 2000
- **進場價：** 16.85
- **成本：** 33700
- **提議進場日：** `2026-04-29`
- **信心度：** LOW
- **資料來源：** yfinance price match ±2% before 2026-04-30 (best: 2026-04-29 @ 17.08)
- **推導理由：** No repo evidence of exact entry date. Most recent date (before 2026-04-30) with close ≈ entry_price 16.85: 2026-04-29 (close=17.08, diff=+1.4%). Price match is not conclusive — 8 candidate date(s) found.
- **價格比對候選日（前5筆，最近優先）：**
  - 2026-04-29 close=17.08 (+1.4%)
  - 2026-04-28 close=17.04 (+1.1%)
  - 2026-04-27 close=16.83 (-0.1%)
  - 2026-04-24 close=16.93 (+0.5%)
  - 2026-04-23 close=16.66 (-1.1%)
- **建議動作：** ⚠️ 需 owner 確認

### 2330 台積電

- **數量：** 50
- **進場價：** 1765.0
- **成本：** 88250
- **提議進場日：** `2026-03-31`
- **信心度：** LOW
- **資料來源：** yfinance price match ±2% before 2026-04-30 (best: 2026-03-31 @ 1760.0)
- **推導理由：** No repo evidence of exact entry date. Most recent date (before 2026-04-30) with close ≈ entry_price 1765.0: 2026-03-31 (close=1760.0, diff=-0.3%). Price match is not conclusive — 17 candidate date(s) found.
- **價格比對候選日（前5筆，最近優先）：**
  - 2026-03-31 close=1760.0 (-0.3%)
  - 2026-03-30 close=1780.0 (+0.8%)
  - 2026-02-06 close=1774.21 (+0.5%)
  - 2026-02-05 close=1759.26 (-0.3%)
  - 2026-02-04 close=1779.2 (+0.8%)
- **建議動作：** ⚠️ 需 owner 確認

### 2345 智邦

- **數量：** 55
- **進場價：** 1828.18
- **成本：** 100550
- **提議進場日：** `2026-04-13`
- **信心度：** LOW
- **資料來源：** yfinance price match ±2% before 2026-04-30 (best: 2026-04-13 @ 1820.0)
- **推導理由：** No repo evidence of exact entry date. Most recent date (before 2026-04-30) with close ≈ entry_price 1828.18: 2026-04-13 (close=1820.0, diff=-0.5%). Price match is not conclusive — 2 candidate date(s) found.
- **價格比對候選日（前5筆，最近優先）：**
  - 2026-04-13 close=1820.0 (-0.5%)
  - 2026-04-10 close=1835.0 (+0.4%)
- **建議動作：** ⚠️ 需 owner 確認

### 2408 南亞科

- **數量：** 120
- **進場價：** 236
- **成本：** 28320
- **提議進場日：** `2026-04-29`
- **信心度：** LOW
- **資料來源：** yfinance price match ±2% before 2026-04-30 (best: 2026-04-29 @ 235.0)
- **推導理由：** No repo evidence of exact entry date. Most recent date (before 2026-04-30) with close ≈ entry_price 236: 2026-04-29 (close=235.0, diff=-0.4%). Price match is not conclusive — 10 candidate date(s) found.
- **價格比對候選日（前5筆，最近優先）：**
  - 2026-04-29 close=235.0 (-0.4%)
  - 2026-04-28 close=237.5 (+0.6%)
  - 2026-03-20 close=234.0 (-0.8%)
  - 2026-03-13 close=238.0 (+0.8%)
  - 2026-03-12 close=239.5 (+1.5%)
- **建議動作：** ⚠️ 需 owner 確認

### 3711 日月光投控

- **數量：** 50
- **進場價：** 412.0
- **成本：** 20600
- **提議進場日：** `2026-04-13`
- **信心度：** LOW
- **資料來源：** yfinance price match ±2% before 2026-04-30 (best: 2026-04-13 @ 417.5)
- **推導理由：** No repo evidence of exact entry date. Most recent date (before 2026-04-30) with close ≈ entry_price 412.0: 2026-04-13 (close=417.5, diff=+1.3%). Price match is not conclusive — 1 candidate date(s) found.
- **備注：** ALREADY_IN_POSITION in pipeline since 2026-05-01 (pipeline position lock uses trade_log, not current_holdings)
- **佐證資料：**
  - trade_log: BUY 2026-04-29 @ 495.5 — ADVISORY MISMATCH (holdings entry_price=412.0, diff=20.3%) — not used
  - daily_report: first seen 2026-05-01 (HOLD/ALREADY_IN_POSITION), last seen 2026-05-07
- **價格比對候選日（前5筆，最近優先）：**
  - 2026-04-13 close=417.5 (+1.3%)
- **建議動作：** ⚠️ 需 owner 確認

### 6830 汎銓

- **數量：** 50
- **進場價：** 712.8
- **成本：** 35640
- **提議進場日：** `2026-04-28`
- **信心度：** LOW
- **資料來源：** yfinance price match ±2% before 2026-04-30 (best: 2026-04-28 @ 716.0)
- **推導理由：** No repo evidence of exact entry date. Most recent date (before 2026-04-30) with close ≈ entry_price 712.8: 2026-04-28 (close=716.0, diff=+0.5%). Price match is not conclusive — 3 candidate date(s) found.
- **佐證資料：**
  - daily_report: first seen 2026-05-05 (BUY/NORMAL), last seen 2026-05-05
- **價格比對候選日（前5筆，最近優先）：**
  - 2026-04-28 close=716.0 (+0.5%)
  - 2026-04-24 close=723.0 (+1.4%)
  - 2026-04-10 close=700.0 (-1.8%)
- **建議動作：** ⚠️ 需 owner 確認

---

## 需 Owner 確認 / 未知項目

以下 7 筆持倉信心度為 LOW 或 UNKNOWN，須 owner 人工確認：

| Ticker | 名稱 | 提議日 | 信心度 | 主要限制 |
| --- | --- | --- | --- | --- |
| 009816 | 凱基台灣TOP50 | 2026-04-13 | LOW | 僅有間接佐證，非確認成交日 |
| 00992A | 主動群益科技創新 | 2026-04-29 | LOW | 僅有間接佐證，非確認成交日 |
| 2330 | 台積電 | 2026-03-31 | LOW | 僅有間接佐證，非確認成交日 |
| 2345 | 智邦 | 2026-04-13 | LOW | 僅有間接佐證，非確認成交日 |
| 2408 | 南亞科 | 2026-04-29 | LOW | 僅有間接佐證，非確認成交日 |
| 3711 | 日月光投控 | 2026-04-13 | LOW | 僅有間接佐證，非確認成交日 |
| 6830 | 汎銓 | 2026-04-28 | LOW | 僅有間接佐證，非確認成交日 |

---

## 建議後續行動

- **可直接套用：** 0 筆（HIGH/MEDIUM 信心度）
- **需 owner 確認：** 7 筆（LOW 信心度）
- **未知，需人工輸入：** 0 筆

**建議任務：** `Manual Owner Review Required for Low-Confidence Entry Dates`

> 建議 owner 從券商後台查詢以下持倉的實際成交日期，確認後補入 `current_holdings.json` 的 `entry_date` 欄位：
> - **009816 凱基台灣TOP50** — 系統推估日期：2026-04-13（LOW），進場價參考：11.4
> - **00992A 主動群益科技創新** — 系統推估日期：2026-04-29（LOW），進場價參考：16.85
> - **2330 台積電** — 系統推估日期：2026-03-31（LOW），進場價參考：1765.0
> - **2345 智邦** — 系統推估日期：2026-04-13（LOW），進場價參考：1828.18
> - **2408 南亞科** — 系統推估日期：2026-04-29（LOW），進場價參考：236
> - **3711 日月光投控** — 系統推估日期：2026-04-13（LOW），進場價參考：412.0
> - **6830 汎銓** — 系統推估日期：2026-04-28（LOW），進場價參考：712.8

---

*報告產生時間：2026-05-10 16:46:32*
*分析腳本：`analysis/derive_entry_dates.py`*
*無任何持倉或交易資料被修改。*