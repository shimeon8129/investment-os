# Diagnosis Report — ROLLING_FIVE_DAY_TOP1_ATR_DIAGNOSIS_v0_1

Generated: 2026-05-26
Valuation date: 2026-05-26
Rolling baskets: 11

---

## Cross-Basket Summary

- strategy_id: ROLLING_FIVE_DAY_TOP1_ATR_DIAGNOSIS_v0_1
- n_baskets: 11
- n_immature: 5
- n_mature: 6
- total_lots: 55
- total_false_exit_count: 17
- total_entry_failure_count: 0
- total_open_winner_count: 20
- total_open_risk_count: 0
- total_market_reversal_count: 0
- total_data_quality_issue_count: 18
- total_gross_pnl: 243496.5
- avg_gross_return_pct_per_basket: 4.4272

---

## Per-Basket Results (ATR_BASE — primary)

| Basket ID | Immature | GrossPnL | Return% | FalseExit | EntryFail | OpenWinner | OpenRisk |
|-----------|----------|----------|---------|-----------|-----------|------------|----------|
| 2026-05-01_5D | NO | -19,748 | -3.95% | 3 | 0 | 0 | 0 |
| 2026-05-02_5D | NO | +24,817 | 4.96% | 3 | 0 | 1 | 0 |
| 2026-05-05_5D | NO | +9,877 | 1.98% | 4 | 0 | 1 | 0 |
| 2026-05-07_5D | NO | +37,644 | 7.53% | 3 | 0 | 2 | 0 |
| 2026-05-08_5D | NO | +57,999 | 11.60% | 2 | 0 | 3 | 0 |
| 2026-05-11_5D | NO | +62,245 | 12.45% | 1 | 0 | 4 | 0 |
| 2026-05-12_5D | YES | +17,680 | 3.54% | 1 | 0 | 3 | 0 |
| 2026-05-13_5D | YES | +32,620 | 6.52% | 0 | 0 | 3 | 0 |
| 2026-05-14_5D | YES | +14,068 | 2.81% | 0 | 0 | 2 | 0 |
| 2026-05-15_5D | YES | +6,294 | 1.26% | 0 | 0 | 1 | 0 |
| 2026-05-17_5D | YES | +0 | 0.00% | 0 | 0 | 0 | 0 |

---

## Lot-Level Diagnosis (ATR_BASE)

| Basket | Date | Ticker | Entry | GrossPnL | Label | PostExitRet | Next1D |
|--------|------|--------|-------|----------|-------|-------------|--------|
| 2026-05-01_5D | 2026-05-01 | 3711.TW | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-01_5D | 2026-05-02 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-01_5D | 2026-05-05 | 3711.TW | 520.0 | -9,216 | ATR_TOO_TIGHT | 30.7% | 0.8% |
| 2026-05-01_5D | 2026-05-07 | 3711.TW | 540.0 | -12,580 | ATR_TOO_TIGHT | 30.7% | -4.4% |
| 2026-05-01_5D | 2026-05-08 | 2464.TW | 122.0 | +2,048 | ATR_TOO_TIGHT | 39.4% | -1.6% |
| 2026-05-02_5D | 2026-05-02 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-02_5D | 2026-05-05 | 3711.TW | 520.0 | -9,216 | ATR_TOO_TIGHT | 30.7% | 0.8% |
| 2026-05-02_5D | 2026-05-07 | 3711.TW | 540.0 | -12,580 | ATR_TOO_TIGHT | 30.7% | -4.4% |
| 2026-05-02_5D | 2026-05-08 | 2464.TW | 122.0 | +2,048 | ATR_TOO_TIGHT | 39.4% | -1.6% |
| 2026-05-02_5D | 2026-05-11 | 2464.TW | 120.0 | +44,566 | OPEN_WINNER | — | -1.7% |
| 2026-05-05_5D | 2026-05-05 | 3711.TW | 520.0 | -9,216 | ATR_TOO_TIGHT | 30.7% | 0.8% |
| 2026-05-05_5D | 2026-05-07 | 3711.TW | 540.0 | -12,580 | ATR_TOO_TIGHT | 30.7% | -4.4% |
| 2026-05-05_5D | 2026-05-08 | 2464.TW | 122.0 | +2,048 | ATR_TOO_TIGHT | 39.4% | -1.6% |
| 2026-05-05_5D | 2026-05-11 | 2464.TW | 120.0 | +44,566 | OPEN_WINNER | — | -1.7% |
| 2026-05-05_5D | 2026-05-12 | 3711.TW | 555.0 | -14,940 | ATR_TOO_TIGHT | 30.7% | -1.3% |
| 2026-05-07_5D | 2026-05-07 | 3711.TW | 540.0 | -12,580 | ATR_TOO_TIGHT | 30.7% | -4.4% |
| 2026-05-07_5D | 2026-05-08 | 2464.TW | 122.0 | +2,048 | ATR_TOO_TIGHT | 39.4% | -1.6% |
| 2026-05-07_5D | 2026-05-11 | 2464.TW | 120.0 | +44,566 | OPEN_WINNER | — | -1.7% |
| 2026-05-07_5D | 2026-05-12 | 3711.TW | 555.0 | -14,940 | ATR_TOO_TIGHT | 30.7% | -1.3% |
| 2026-05-07_5D | 2026-05-13 | 2356.TW | 52.8 | +18,551 | OPEN_WINNER | — | 0.8% |
| 2026-05-08_5D | 2026-05-08 | 2464.TW | 122.0 | +2,048 | ATR_TOO_TIGHT | 39.4% | -1.6% |
| 2026-05-08_5D | 2026-05-11 | 2464.TW | 120.0 | +44,566 | OPEN_WINNER | — | -1.7% |
| 2026-05-08_5D | 2026-05-12 | 3711.TW | 555.0 | -14,940 | ATR_TOO_TIGHT | 30.7% | -1.3% |
| 2026-05-08_5D | 2026-05-13 | 2356.TW | 52.8 | +18,551 | OPEN_WINNER | — | 0.8% |
| 2026-05-08_5D | 2026-05-14 | 3413.TW | 321.0 | +7,775 | OPEN_WINNER | — | 1.4% |
| 2026-05-11_5D | 2026-05-11 | 2464.TW | 120.0 | +44,566 | OPEN_WINNER | — | -1.7% |
| 2026-05-11_5D | 2026-05-12 | 3711.TW | 555.0 | -14,940 | ATR_TOO_TIGHT | 30.7% | -1.3% |
| 2026-05-11_5D | 2026-05-13 | 2356.TW | 52.8 | +18,551 | OPEN_WINNER | — | 0.8% |
| 2026-05-11_5D | 2026-05-14 | 3413.TW | 321.0 | +7,775 | OPEN_WINNER | — | 1.4% |
| 2026-05-11_5D | 2026-05-15 | 3413.TW | 325.5 | +6,294 | OPEN_WINNER | — | -0.9% |
| 2026-05-12_5D | 2026-05-12 | 3711.TW | 555.0 | -14,940 | ATR_TOO_TIGHT | 30.7% | -1.3% |
| 2026-05-12_5D | 2026-05-13 | 2356.TW | 52.8 | +18,551 | OPEN_WINNER | — | 0.8% |
| 2026-05-12_5D | 2026-05-14 | 3413.TW | 321.0 | +7,775 | OPEN_WINNER | — | 1.4% |
| 2026-05-12_5D | 2026-05-15 | 3413.TW | 325.5 | +6,294 | OPEN_WINNER | — | -0.9% |
| 2026-05-12_5D | 2026-05-17 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-13_5D | 2026-05-13 | 2356.TW | 52.8 | +18,551 | OPEN_WINNER | — | 0.8% |
| 2026-05-13_5D | 2026-05-14 | 3413.TW | 321.0 | +7,775 | OPEN_WINNER | — | 1.4% |
| 2026-05-13_5D | 2026-05-15 | 3413.TW | 325.5 | +6,294 | OPEN_WINNER | — | -0.9% |
| 2026-05-13_5D | 2026-05-17 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-13_5D | 2026-05-21 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-14_5D | 2026-05-14 | 3413.TW | 321.0 | +7,775 | OPEN_WINNER | — | 1.4% |
| 2026-05-14_5D | 2026-05-15 | 3413.TW | 325.5 | +6,294 | OPEN_WINNER | — | -0.9% |
| 2026-05-14_5D | 2026-05-17 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-14_5D | 2026-05-21 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-14_5D | 2026-05-22 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-15_5D | 2026-05-15 | 3413.TW | 325.5 | +6,294 | OPEN_WINNER | — | -0.9% |
| 2026-05-15_5D | 2026-05-17 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-15_5D | 2026-05-21 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-15_5D | 2026-05-22 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-15_5D | 2026-05-25 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-17_5D | 2026-05-17 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-17_5D | 2026-05-21 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-17_5D | 2026-05-22 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-17_5D | 2026-05-25 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |
| 2026-05-17_5D | 2026-05-26 | None | None | +0 | DATA_QUALITY_ISSUE | — | — |

---

## Model Comparison (Summed Across All Baskets)

| Model | TotalGrossPnL | AvgReturn%/Basket |
|-------|---------------|------------------|
| ATR_TIGHT | 123,620 | 2.25% |
| ATR_BASE | 243,496 | 4.43% |
| ATR_WIDE | 444,152 | 8.08% |
| FIXED_10D | 291,488 | 5.30% |
| MA5 | -168,108 | -3.06% |

---

*Advisory only. No trades placed. All outputs for human review.*
