# Signal Quality Replay — 2026-05-10

**Verdict: WARN**

> 樣本不足：僅 3 個交易日有 point-in-time 資料（目標 10 個，最低門檻 5 個）。 請先建立更完整的歷史 snapshot，再下最終判定。 初步觀察：Top3 1D均 -3.17% vs Universe -2.19%。

## 資料覆蓋

- 請求交易日數：10
- 有資料日數：3
- 無資料日數（缺少 point-in-time snapshot）：7
- 候選標的總數（跨日累計）：30
- 1D 報酬資料覆蓋：20/30
- 3D 報酬資料覆蓋：10/30
- 5D 報酬資料覆蓋：0/30

### 限制聲明

- No point-in-time data available for this date. Exact replay not supported.
- L0-L4 partial or missing; scores from daily report only (top 5 authoritative)

## 逐日資料來源

| 日期 | 資料來源 | 市場狀態 | VIX | 候選數 | Universe 1D均 | Top3 1D均 |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-05-08 | p1_audit_report.json + mainline_snapshot.json | RANGE | 17.200000762939453 | 10 | N/A | N/A |
| 2026-05-07 | daily_report + P1_ENTRY_AUDIT_md + DAILY_DECISION_DASHBOARD | RANGE | 17.51 | 10 | -2.07% | -0.88% |
| 2026-05-06 | NONE | N/A | None | 0 | N/A | N/A |
| 2026-05-05 | daily_report + DAILY_DECISION_DASHBOARD | BULL | 18.29 | 10 | -2.31% | -5.46% |
| 2026-05-04 | NONE | N/A | None | 0 | N/A | N/A |
| 2026-04-30 | NONE | N/A | None | 0 | N/A | N/A |
| 2026-04-29 | NONE | N/A | None | 0 | N/A | N/A |
| 2026-04-28 | NONE | N/A | None | 0 | N/A | N/A |
| 2026-04-27 | NONE | N/A | None | 0 | N/A | N/A |
| 2026-04-24 | NONE | N/A | None | 0 | N/A | N/A |

## 排名分組 vs 全宇宙比較

| 分組 | 1D 均報酬 | 3D 均報酬 |
| --- | --- | --- |
| 全宇宙 (Universe) | -2.19% | -3.38% |
| Top 3 | -3.17% | -10.73% |
| Top 5 | -3.52% | -11.01% |
| Top 10 | -2.19% | -3.38% |

## EntryLock 分組報酬

| P1 結果 | 1D 均報酬 | 3D 均報酬 |
| --- | --- | --- |
| ENTRY / ENTRY_REDUCED | +0.34% | N/A |
| WAIT | -2.33% | N/A |

## Lock Layer 封鎖分組

| 封鎖層 | 1D 均報酬（被封鎖者） |
| --- | --- |
| L2 BLOCK | -1.38% |
| L3 BLOCK | -6.03% |

## 候選標的明細（有資料日）

| 日期 | Rank | Ticker | 名稱 | 分數 | P1 | L0 | L2 | L3 | 1D | 3D | 5D |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-08 | 1 | 2464.TW | 盟立 | 151.4 | WAIT | WARN | BLOCK | PASS | N/A | N/A | N/A |
| 2026-05-08 | 2 | 2356.TW | 英業達 | 145.534 | ENTRY_REDUCED | WARN | PASS | PASS | N/A | N/A | N/A |
| 2026-05-08 | 3 | 2449.TW | 京元電子 | 145.2 | WAIT | WARN | PASS | BLOCK | N/A | N/A | N/A |
| 2026-05-08 | 4 | 3231.TW | 緯創 | 144.534 | ENTRY_REDUCED | WARN | PASS | PASS | N/A | N/A | N/A |
| 2026-05-08 | 5 | 3680.TWO | 家登 | 124.0 | WAIT | WARN | PASS | BLOCK | N/A | N/A | N/A |
| 2026-05-08 | 6 | 6147.TWO | 頎邦 | 108.2 | WAIT | WARN | BLOCK | PASS | N/A | N/A | N/A |
| 2026-05-08 | 7 | 6257.TW | 矽格 | 108.2 | WAIT | WARN | BLOCK | PASS | N/A | N/A | N/A |
| 2026-05-08 | 8 | 2317.TW | 鴻海 | 108.2 | WAIT | WARN | PASS | BLOCK | N/A | N/A | N/A |
| 2026-05-08 | 9 | 6669.TW | 緯穎 | 108.2 | WAIT | WARN | BLOCK | PASS | N/A | N/A | N/A |
| 2026-05-08 | 10 | 3706.TW | 神達 | 108.2 | ENTRY_REDUCED | WARN | PASS | PASS | N/A | N/A | N/A |
| 2026-05-07 | 1 | 3711.TW | 日月光投控 | 173.46599999999998 | WAIT | WARN | BLOCK | BLOCK | -4.44% | N/A | N/A |
| 2026-05-07 | 2 | 2356.TW | 英業達 | 145.534 | WAIT | WARN | BLOCK | PASS | -0.80% | N/A | N/A |
| 2026-05-07 | 3 | 2376.TW | 技嘉 | 145.2 | WAIT | WARN | BLOCK | PASS | +2.59% | N/A | N/A |
| 2026-05-07 | 4 | 3231.TW | 緯創 | 144.534 | ENTRY_REDUCED | WARN | PASS | PASS | +0.34% | N/A | N/A |
| 2026-05-07 | 5 | 6830.TW | 汎銓 | 118.2 | WAIT | WARN | PASS | BLOCK | -9.95% | N/A | N/A |
| 2026-05-07 | 6 | 6239.TW | 6239.TW | 230.5 | WAIT | WARN | BLOCK | BLOCK | -3.69% | N/A | N/A |
| 2026-05-07 | 7 | 6257.TW | 6257.TW | 213.0 | WAIT | WARN | BLOCK | PASS | -0.94% | N/A | N/A |
| 2026-05-07 | 8 | 2382.TW | 2382.TW | 344.0 | WAIT | WARN | BLOCK | PASS | -1.02% | N/A | N/A |
| 2026-05-07 | 9 | 2317.TW | 2317.TW | 253.5 | WAIT | WARN | BLOCK | PASS | -1.38% | N/A | N/A |
| 2026-05-07 | 10 | 3706.TW | 3706.TW | 87.4 | WAIT | WARN | BLOCK | PASS | -1.37% | N/A | N/A |
| 2026-05-05 | 1 | 3711.TW | 日月光投控 | 173.46599999999998 | None | None | None | None | +0.77% | -0.77% | N/A |
| 2026-05-05 | 2 | 2449.TW | 京元電子 | 145.2 | None | None | None | None | -7.20% | -12.15% | N/A |
| 2026-05-05 | 3 | 6830.TW | 汎銓 | 118.2 | None | None | None | None | -9.95% | -19.28% | N/A |
| 2026-05-05 | 4 | 6187.TWO | 萬潤 | 118.2 | None | None | None | None | -9.67% | -20.45% | N/A |
| 2026-05-05 | 5 | 6239.TW | 力成 | 108.2 | None | None | None | None | +3.08% | -2.42% | N/A |
| 2026-05-05 | 6 | 6147.TWO | 頎邦 | 108.2 | None | None | None | None | -1.41% | +11.55% | N/A |
| 2026-05-05 | 7 | 6257.TW | 矽格 | 108.2 | None | None | None | None | +3.30% | +7.11% | N/A |
| 2026-05-05 | 8 | 3706.TW | 神達 | 108.2 | None | None | None | None | +4.40% | +2.50% | N/A |
| 2026-05-05 | 9 | 2313.TW | 華通 | 108.2 | None | None | None | None | -8.93% | -7.65% | N/A |
| 2026-05-05 | 10 | 3443.TW | 創意 | 108.2 | None | None | None | None | +2.48% | +7.76% | N/A |

## False Negatives（WAIT/BLOCK 但後來大漲）

（無）— 所有明確 WAIT 的標的均未超過 +3% (3D) / +5% (5D) 閾值

### 備注：無 P1 資料但 3D/5D 表現 ≥+5% 的候選（僅供參考）

| 日期 | Ticker | 名稱 | Rank | 3D | 5D |
| --- | --- | --- | --- | --- | --- |
| 2026-05-05 | 6147.TWO | 頎邦 | 6 | +11.55% | N/A |
| 2026-05-05 | 6257.TW | 矽格 | 7 | +7.11% | N/A |
| 2026-05-05 | 3443.TW | 創意 | 10 | +7.76% | N/A |

## False Positives（ENTRY 但後來下跌）

（無）— 所有 ENTRY/ENTRY_REDUCED 標的均未跌超 -3% (3D) / -5% (5D) 閾值

## 任務問題回答

**Q1. Top 3/5/10 是否跑贏候選宇宙？**
- Top 3 1D 均: -3.17% vs Universe -2.19% → 未優於
- Top 5 1D 均: -3.52% | Top 10 1D 均: -2.19%

**Q2. WAIT/BLOCK 標籤是否過於保守？**
- ENTRY/ENTRY_REDUCED 1D 均: +0.34%
- WAIT 1D 均: -2.33%
- False Negatives 數量: 0

**Q3. 哪個封鎖層造成最多錯失機會？**
- L2 封鎖後 1D 均: -1.38%
- L3 封鎖後 1D 均: -6.03%

**Q4. 目前雷達是否能及早捕捉主升段？**
- Top 3 5D 最大漲幅均值: -2.17%

**Q5. 是否應擴展至 20 交易日？**
→ **暫緩擴展，先釐清根因**（WARN → review root cause before expansion）

---

## 最終結果

```
WARN
```

**理由：** 樣本不足：僅 3 個交易日有 point-in-time 資料（目標 10 個，最低門檻 5 個）。 請先建立更完整的歷史 snapshot，再下最終判定。 初步觀察：Top3 1D均 -3.17% vs Universe -2.19%。
