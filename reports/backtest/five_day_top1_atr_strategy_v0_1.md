# Backtest Report — FIVE_DAY_TOP1_ATR_STRATEGY_v0_1

Generated: 2026-05-26
Valuation date: 2026-05-25

---

## Strategy Parameters

- Strategy ID: `FIVE_DAY_TOP1_ATR_STRATEGY_v0_1`
- Basket ID: `2026-05-07_TOP1_5D`
- Planned capital: 500,000 TWD
- Entry capital / lot: 100,000 TWD
- Lots: 5
- Primary exit model: **ATR_BASE** (initial 1.5×ATR, trailing 2.0×ATR)
- Entry price: signal-day close (v0.1)

---

## Lot-Level Results (ATR_BASE — primary)

| # | Date | Ticker | Entry | Shares | Cost | ATR20 | InitStop | TrailStop | Exit | Reason | GrossPnL | Grade |
|---|------|--------|-------|--------|------|-------|----------|-----------|------|--------|----------|-------|
| 1 | 2026-05-07 | 3711.TW | 540.0 | 185 | 99,900 | 27.025 | 499.46 | 500.95 | 472.0 | ATR_TRAILING_STOP | -12,580 | B |
| 2 | 2026-05-08 | 2464.TW | 122.0 | 819 | 99,918 | 7.24 | 111.14 | 124.52 | 124.5 | ATR_TRAILING_STOP | +2,048 | B |
| 3 | 2026-05-11 | 2464.TW | 120.0 | 833 | 99,960 | 7.825 | 108.26 | 142.35 | — | OPEN_POSITION | +31,654 | B |
| 4 | 2026-05-12 | 3711.TW | 555.0 | 180 | 99,900 | 28.875 | 511.69 | 497.25 | 472.0 | ATR_TRAILING_STOP | -14,940 | A |
| 5 | 2026-05-13 | 2356.TW | 52.8 | 1893 | 99,950 | 1.7125 | 50.23 | 61.98 | — | OPEN_POSITION | +23,852 | B |

---

## Basket Summary (ATR_BASE)

| Field | Value |
|-------|-------|
| strategy_id | FIVE_DAY_TOP1_ATR_STRATEGY_v0_1 |
| basket_id | 2026-05-07_TOP1_5D |
| start_date | 2026-05-07 |
| entry_count | 5 |
| planned_capital | 500000.0 |
| deployed_capital | 499628.4 |
| cash_remainder | 371.6 |
| current_stock_value | 255416.2 |
| realized_value | 274245.5 |
| total_equity | 530033.3 |
| gross_pnl | 30033.3 |
| net_pnl_estimated | 26977.57 |
| gross_return_pct | 6.0067 |
| net_return_pct_estimated | 5.3955 |
| open_positions | 2 |
| exited_positions | 3 |
| best_lot | 2464.TW |
| worst_lot | 3711.TW |

---

## ATR Stop Status per Lot (ATR_BASE)

| Ticker | Entry | ATR20 | Initial Stop | Trailing Stop | Highest Close | Status |
|--------|-------|-------|-------------|--------------|--------------|--------|
| 3711.TW | 540.0 | 27.025 | 499.46 | 500.95 | 555.0 | ATR_TRAILING_STOP |
| 2464.TW | 122.0 | 7.24 | 111.14 | 124.52 | 139.0 | ATR_TRAILING_STOP |
| 2464.TW | 120.0 | 7.825 | 108.26 | 142.35 | 158.0 | OPEN_POSITION |
| 3711.TW | 555.0 | 28.875 | 511.69 | 497.25 | 555.0 | ATR_TRAILING_STOP |
| 2356.TW | 52.8 | 1.7125 | 50.23 | 61.98 | 65.4 | OPEN_POSITION |

---

## Multi-Model Comparison

| Model | GrossPnL | NetPnL(est) | Gross% | Net%(est) | Open | Exited |
|-------|----------|------------|--------|----------|------|--------|
| ATR_TIGHT | 15,998 | 13,004 | 3.20% | 2.60% | 1 | 4 |
| ATR_BASE | 30,033 | 26,978 | 6.01% | 5.40% | 2 | 3 |
| ATR_WIDE | 57,470 | 54,293 | 11.49% | 10.86% | 3 | 2 |
| FIXED_10D | 44,122 | 42,173 | 8.82% | 8.43% | 0 | 3 |
| MA5 | -28,650 | -31,446 | -5.73% | -6.29% | 0 | 5 |

---

## ATR Variant Comparison

| Variant | Init Mult | Trail Mult | GrossPnL | NetPnL(est) | Return% |
|---------|-----------|------------|----------|------------|---------|
| ATR_TIGHT | 1.0× | 1.5× | 15,998 | 13,004 | 3.20% |
| ATR_BASE | 1.5× | 2.0× | 30,033 | 26,978 | 6.01% |
| ATR_WIDE | 2.0× | 2.5× | 57,470 | 54,293 | 11.49% |


*Advisory only. No trades placed. All outputs for human review.*
