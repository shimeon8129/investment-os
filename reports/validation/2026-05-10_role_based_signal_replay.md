# Role-Based Signal Replay — 2026-05-10

**Verdict: WARN**

> PIT snapshot 僅 3/20 天，17 天為 HISTORICAL_RECONSTRUCTED。角色分組有助解讀（4/4 角色顯示訊號），但資料來源可信度有限，需累積更多 PIT snapshot 後才能確認 PASS。

---

## 資料覆蓋

- 請求交易日數：20
- PIT_SNAPSHOT 日數：3
- HISTORICAL_RECONSTRUCTED 日數：17

### 逐日 Replay Quality

| 日期 | Replay 品質 |
| --- | --- |
| 2026-05-08 | PIT_SNAPSHOT |
| 2026-05-07 | PIT_SNAPSHOT |
| 2026-05-06 | HISTORICAL_RECONSTRUCTED |
| 2026-05-05 | PIT_SNAPSHOT |
| 2026-05-04 | HISTORICAL_RECONSTRUCTED |
| 2026-04-30 | HISTORICAL_RECONSTRUCTED |
| 2026-04-29 | HISTORICAL_RECONSTRUCTED |
| 2026-04-28 | HISTORICAL_RECONSTRUCTED |
| 2026-04-27 | HISTORICAL_RECONSTRUCTED |
| 2026-04-24 | HISTORICAL_RECONSTRUCTED |
| 2026-04-23 | HISTORICAL_RECONSTRUCTED |
| 2026-04-22 | HISTORICAL_RECONSTRUCTED |
| 2026-04-21 | HISTORICAL_RECONSTRUCTED |
| 2026-04-20 | HISTORICAL_RECONSTRUCTED |
| 2026-04-17 | HISTORICAL_RECONSTRUCTED |
| 2026-04-16 | HISTORICAL_RECONSTRUCTED |
| 2026-04-15 | HISTORICAL_RECONSTRUCTED |
| 2026-04-14 | HISTORICAL_RECONSTRUCTED |
| 2026-04-13 | HISTORICAL_RECONSTRUCTED |
| 2026-04-10 | HISTORICAL_RECONSTRUCTED |

---

## 角色分組統計

### CORE （6 個 ticker）

**Tickers：** 2330.TW, 2454.TW, 3661.TWO, 3711.TW, 6187.TWO, 7769.TWO

| 窗口 | 樣本數 | 平均報酬 | 中位數 | Hit Rate |
| --- | --- | --- | --- | --- |
| 10D | 40 | +19.67% | +11.59% | 90% |
| 20D | 0 | N/A | N/A | N/A |

- **最大漲幅（20D 窗口）：** N/A
- **最大跌幅（20D 窗口）：** N/A
- **False Positives：** 0

### CORE_ETF （2 個 ticker）

**Tickers：** 009816.TW, 00992A.TW

| 窗口 | 樣本數 | 平均報酬 | 中位數 | Hit Rate |
| --- | --- | --- | --- | --- |
| 10D | 20 | +11.34% | +12.67% | 100% |
| 20D | 0 | N/A | N/A | N/A |

- **最大漲幅（20D 窗口）：** N/A
- **最大跌幅（20D 窗口）：** N/A
- **False Positives：** 0

### SATELLITE （11 個 ticker）

**Tickers：** 2059.TW, 2308.TW, 2345.TW, 2408.TW, 3017.TW, 3081.TWO, 3105.TWO, 3324.TW, 3363.TWO, 4979.TWO, 6781.TW

| 窗口 | 樣本數 | 平均報酬 | 中位數 | Hit Rate |
| --- | --- | --- | --- | --- |
| 5D | 150 | +7.33% | +7.36% | 76% |
| 10D | 100 | +9.97% | +11.70% | 78% |
| 20D | 0 | N/A | N/A | N/A |

- **最大漲幅（20D 窗口）：** N/A
- **最大跌幅（20D 窗口）：** N/A
- **False Positives：** 18

### WAVE_SWING （17 個 ticker）

**Tickers：** 2317.TW, 2337.TW, 2356.TW, 2376.TW, 2382.TW, 2449.TW, 2464.TW, 3231.TW, 3260.TW, 3680.TWO, 3706.TW, 6147.TWO, 6257.TW, 6515.TWO, 6669.TWO, 6830.TW, 8299.TWO

| 窗口 | 樣本數 | 平均報酬 | 中位數 | Hit Rate |
| --- | --- | --- | --- | --- |
| 3D | 238 | +4.03% | +2.62% | 66% |
| 5D | 210 | +6.98% | +5.20% | 72% |
| 10D | 140 | +12.54% | +6.93% | 80% |

- **最大漲幅（10D 窗口）：** +60.76%
- **最大跌幅（10D 窗口）：** -31.69%
- **False Positives：** 26

---

## 角色 vs 全宇宙比較

| 角色 | 3D 平均 | 5D 平均 | 10D 平均 | 20D 平均 |
| --- | --- | --- | --- | --- |
| Universe | +4.42% | +7.59% | +12.64% | N/A |
| CORE | N/A | N/A | +19.67% | N/A |
| CORE_ETF | N/A | N/A | +11.34% | N/A |
| SATELLITE | N/A | +7.33% | +9.97% | N/A |
| WAVE_SWING | +4.03% | +6.98% | +12.54% | N/A |

---

## 任務問題回答

**Q1. CORE 標的是否表現如核心持倉？**
- CORE 10D 均報酬：+19.67%，20D：N/A → 正常
- 注意：CORE 不應以 1D/3D 短期波動論斷，應以 10D/20D 趨勢評估

**Q2. SATELLITE 標的是否適合 5D–20D 波段擴張？**
- SATELLITE 5D：+7.33%，10D：+9.97%，20D：N/A → 有潛力

**Q3. WAVE_SWING 標的是否適合 3D–10D 波動操作？**
- WAVE_SWING 3D：+4.03%，5D：+6.98%，10D：+12.54% → 有訊號

**Q4. 前次 Top3 弱勢是否因角色混合所致？**
- 前次 all-in-one Top3 1D均 -3.17%，WAVE_SWING 3D均 +4.03% → 分組後表現有差異，混合評估確實掩蓋角色差異

**Q5. 目前雷達按角色是否可用？**
- 3/3 個主要角色有足夠資料（n≥3）→ 初步可用，建議持續累積

---

## 最終結果

```
WARN
```

**理由：** PIT snapshot 僅 3/20 天，17 天為 HISTORICAL_RECONSTRUCTED。角色分組有助解讀（4/4 角色顯示訊號），但資料來源可信度有限，需累積更多 PIT snapshot 後才能確認 PASS。

---

*報告產生時間：2026-05-10 17:05:35*
*分析腳本：`analysis/role_based_signal_replay.py`*
*無任何持倉或交易資料被修改。*