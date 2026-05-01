# Investment OS｜Next Action

## Immediate Next Step

Create and maintain GitHub-based memory layer.

## Next Engineering Task

Mainline consolidation.

Priority:
1. Review pipeline/main.py
2. Extract clean mainline plan
3. Decide whether to create pipeline/main_v1.py or refactor existing main.py
4. Connect mainline into jobs/daily_run.py only after standalone validation

## Guardrails

Do not:
- Add new decision modules
- Add new market engine modules
- Expand external AI agents
- Modify broker/execution automation

Do:
- Read current repo structure
- Preserve existing working daily runner
- Work on a branch
- Commit memory updates separately
