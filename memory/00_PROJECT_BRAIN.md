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

When providing commands or tasks for Investment OS, Claude Code, shell, or any local OS execution environment, the assistant must provide one complete copy-paste-ready block.

Do not split OS/Claude Code instructions across multiple separate fragments unless the user explicitly asks for step-by-step separation.

The preferred format is a single fenced command block or a single generated task file, such as:

```bash
cat > /tmp/investment_os_task.md <<'EOF'
# Task content here
EOF

claude < /tmp/investment_os_task.md
```

This rule exists to reduce copy/paste errors and preserve execution context across AI collaboration sessions.

## Current System Direction

Current priority:
- Mainline consolidation
- Runtime integration
- Prevent further uncontrolled module growth
