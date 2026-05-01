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

## Current System Direction

Current priority:
- Mainline consolidation
- Runtime integration
- Prevent further uncontrolled module growth
