# Claude Hotfix Report — 6830 Name Mapping

## Goal

Fix incorrect 6830 name mapping.

## Correction

- Wrong: 6830 泰鼎 (incorrectly used in previous commits)
- Correct: 6830 汎銓 (confirmed from data/universe_tw.csv and data/watchlist.json)

## Scope

Allowed:
- Fix current_holdings name
- Fix ticker master canonical name
- Fix smoke tests
- Regenerate reports
- Replace incorrect generated docs content
- Python syntax check

Not allowed:
- Change scanner scoring logic
- Change decision lock logic
- Change risk logic
- Change Telegram notification
- Change main pipeline behavior
- Change holdings share count
- Add AI Agent

## Result

- [x] data/portfolio/current_holdings.json fixed (泰鼎 → 汎銓)
- [x] data/master/tw_ticker_master.json fixed (泰鼎 → 汎銓)
- [x] tests/smoke_ticker_master.py fixed (assertions updated)
- [x] tests/smoke_portfolio_candidate_review.py fixed (assert 汎銓 in content, assert 泰鼎 not in content)
- [x] All smoke tests passed
- [x] candidate review regenerated
- [x] portfolio candidate review regenerated
- [x] No "泰鼎" remains under data/metadata/reporting/docs/tests (except negative assertion)
- [x] Python compile check passed
- [x] Git commit created

## Validation

```
grep -R "泰鼎" -n data metadata reporting docs tests
-> Only found: tests/smoke_portfolio_candidate_review.py:35: assert "泰鼎" not in content
-> This is an intentional negative assertion, not a data error
```

## 6830 shares check

- shares: 20 (unchanged) ✓

## Modified Files

- `data/portfolio/current_holdings.json` — 6830 name: 泰鼎 → 汎銓
- `data/master/tw_ticker_master.json` — 6830 canonical_name: 泰鼎 → 汎銓
- `tests/smoke_ticker_master.py` — assertions updated to 汎銓
- `tests/smoke_portfolio_candidate_review.py` — updated to assert 汎銓 in / 泰鼎 not in content
- `docs/*.md` (7 files) — all 泰鼎 occurrences replaced with 汎銓
- `docs/CANDIDATE_REVIEW_20260426.md` — regenerated
- `docs/PORTFOLIO_CANDIDATE_REVIEW_20260426.md` — regenerated

## Errors

None.

## Notes

- pipeline/main.py was NOT modified
- The error originated from the previous portfolio holdings creation step
  where mojibake in the MD instruction was decoded as 泰鼎 instead of 汎銓
- Source of truth: data/universe_tw.csv shows `6830.TW,汎銓,Equipment,CORE`
