# Validation Report — FIVE_DAY_TOP1_ATR_STRATEGY_v0_1

Generated: 2026-05-26

## Assumptions

1. Entry price = signal-day adjusted close (yfinance auto_adjust=True, v0.1)
2. ATR20 = arithmetic mean of True Range over 20 trading days strictly before entry date
3. Trailing stop = highest_close_since_entry − trailing_mult × ATR20 (close-based exit)
4. On day-1 of hold: effective_stop = max(trailing_stop, initial_stop)
5. Duplicate tickers allowed across entry days (signal persistence)
6. Transaction costs: buy 0.1425%, sell 0.1425% + STT 0.3% on sell value
7. No slippage model in v0.1

## Data Quality Summary

| Entry | Ticker | DQ Flag | Note |
|-------|--------|---------|------|
| 1 | 3711.TW | PASS | — |
| 2 | 2464.TW | PASS | — |
| 3 | 2464.TW | PASS | — |
| 4 | 3711.TW | PASS | — |
| 5 | 2356.TW | PASS | — |

## Known Limitations

- Score field not normalized across all dates (see spec §9)
- Position grade is diagnostic only — derived from signal/market_state/role_confidence; chips and chase_risk not available in historical reports
- Entry price uses adjusted close; may differ from actual signal-day raw close due to splits/dividends
- ATR20 uses calendar-day windows from yfinance, not exact TW trading-day count
- v0.1 does not compare next-day open vs VWAP entry prices

## Ticker Exposure Concentration

| Ticker | Market Value | % of Total |
|--------|-------------|------------|
| 2464.TW | 233,580 | 44.1% |
| 3711.TW | 172,280 | 32.5% |
| 2356.TW | 123,802 | 23.4% |

---

*Owner should review before any capital allocation decisions.*
