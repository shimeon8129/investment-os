# Investment OS｜Project Brain

## Purpose

Investment OS is an AI-assisted investment research, scanner, reporting, and decision-support operating system.

It is not an auto-trading system.

## Core Rule

Investment OS must never:
- Login to broker accounts
- Place trades automatically
- Modify broker accounts
- Execute trades without human decision

All trading execution remains manual.

## Sensitive Investment Data Protection Rule

Investment-context data must be protected from automatic deletion or silent mutation.

Sensitive investment data includes: universe files, watchlists, holdings, portfolio files, user-observed tickers, trade logs, and manually curated research targets.

Claude Code, ChatGPT, or any automation must not remove, replace, downgrade, or silently mutate sensitive investment data without explicit user approval.

**A data provider failure is not evidence that a ticker is invalid.**

- `yfinance no price data` does not mean the ticker is delisted.
- Missing OHLCV data, API timeout, stale data, or provider warning must be classified as `data_warning`, not as deletion permission.
- Correct handling: keep the ticker, surface the warning in reports, investigate alternate data sources, and ask the user before any removal.

**Approval requirement:**

For sensitive investment data changes, Claude Code may inspect files and propose a diff, but must not auto-commit or auto-push. The user must explicitly approve the exact diff before commit or push. Validation success does not override the approval requirement.

This rule has higher priority than the Local Claude Code Git Workflow Rule.

## Current Strategic Problem

The project has grown large across many sessions. The main issue is no longer lack of modules, but session memory decay and fragmented integration.

## Memory Principle

GitHub memory/ is the primary persistent AI collaboration memory layer.

Every new AI session should first read:
- memory/00_PROJECT_BRAIN.md
- memory/01_SYSTEM_STATUS.md
- memory/02_SESSION_LOG.md
- memory/03_NEXT_ACTION.md


## Collaboration Rule

For OS, shell, or Claude Code tasks, ChatGPT must give short, clear, single-block commands that are safe to copy and paste. Do not use long heredoc prompts such as `cat EOF`. Do not paste long duplicated context into terminal commands.

Claude Code should read project context directly from repo files, especially:
- memory/00_PROJECT_BRAIN.md
- memory/01_SYSTEM_STATUS.md
- memory/02_SESSION_LOG.md
- memory/03_NEXT_ACTION.md

Preferred style is one short `claude` command telling Claude which files to read and what to do.

## Local Claude Code Git Workflow Rule

For local engineering tasks, Claude Code may commit and push directly only when the task explicitly allows it. Steps:
1. Read repo memory and relevant files before making any change.
2. Make the minimal requested change.
3. Run the requested validation (compile, smoke tests, etc.).
4. Commit and push only if validation passes; do not commit or push if validation fails.

After push, ChatGPT will verify by reading GitHub remote.

## Claude Code Token Discipline Rule

Claude Code credit is limited. ChatGPT must avoid giving Claude Code broad exploratory tasks unless explicitly needed.

Default workflow:
- ChatGPT performs architecture reasoning and decides exact patch scope.
- Claude Code receives only precise patch tasks.
- Read only necessary files.
- Modify only explicitly named files.
- Avoid broad review commands unless the task is specifically a review.
- Avoid re-reading long context already known.
- One task should change one small scope.
- Validation must be specified exactly.

Preferred instruction style:
- Edit only `<file>`.
- Do exactly these changes.
- Do not edit any other file.
- Run exactly this validation.
- Commit/push only if validation passes.

## Current System Direction

Current priority:
- Mainline consolidation
- Runtime integration
- Prevent further uncontrolled module growth
