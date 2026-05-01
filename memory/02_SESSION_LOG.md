# Investment OS｜Session Log

## 2026-05-01 (continued — mainline MVP integration)

Major outcomes:
- Created pipeline/main_v1.py: clean extraction of Block B from pipeline/main.py.
  Applied surgical cleanups per docs/MAINLINE_REVIEW_20260501.md:
  removed debug prints, duplicate write_trade_log call, unused imports.
- Converted pipeline/main_v1.py to advisory-only snapshot producer:
  writes data/processed/mainline_snapshot.json with market state, candidates,
  signals, ranked, decisions, exit signals, and safety flags.
- Validated pipeline/main_v1.py standalone (python3 -m pipeline.main_v1): PASS.
- Integrated pipeline_main_v1 into jobs/daily_run.py as a new check block.
- Added Mainline Snapshot section to daily report:
  market state, market score, VIX, top 5 ranked table, decisions table.
- Full daily runner validation (python3 jobs/daily_run.py): PASS.
- Known non-blocking warning: 8046.TWO and 3189.TWO have no price data (delisted).

Added memory rules:
- Local Claude Code Git Workflow Rule
- Claude Code Token Discipline Rule

## 2026-05-01 (earlier)

Major outcomes:
- Confirmed Hermes daily runner works.
- Fixed human_summary.md Markdown formatting.
- Confirmed GitHub branch is pushed and clean.
- Confirmed Google Drive connector can read/list files but Google Docs write test failed with 403.
- Decided GitHub memory/ should be primary AI collaboration memory layer.
- Identified the real system issue: not missing modules, but fragmented mainlines.

Important correction:
- Do not assume missing modules.
- The repo already contains many components.
- Always inspect existing structure before proposing new files.

Current conclusion:
- Use GitHub memory/ as persistent collaboration memory.
- Use Google Drive only as secondary human-readable / NotebookLM layer.
