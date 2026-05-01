# Investment OS｜AI Session Protocol

## Purpose

This file defines the universal AI collaboration protocol for Investment OS.

The goal is to prevent session memory loss, fragmented architecture, duplicated modules, and uncontrolled system growth.

This protocol should be used by ChatGPT, Claude, Gemini, Codex, or any external AI tool working on Investment OS.

---

## Session Start Protocol

At the beginning of every new AI working session, the user should issue:

請先讀 GitHub repo shimeon8129/investment-os 的:
- memory/00_PROJECT_BRAIN.md
- memory/01_SYSTEM_STATUS.md
- memory/02_SESSION_LOG.md
- memory/03_NEXT_ACTION.md
- memory/99_AI_SESSION_PROTOCOL.md

再恢復 Investment OS 工作狀態。

AI must:
1. Read memory files
2. Summarize current state
3. Respect guardrails
4. Inspect repo before proposing changes
5. Avoid uncontrolled module expansion

---

## Session Close Protocol

At session end, the user should issue:

請更新本次 session 至 GitHub memory：
- SYSTEM_STATUS
- SESSION_LOG
- NEXT_ACTION
- AI_SESSION_PROTOCOL 如有變更

並輸出完整 git commit / push 指令。

AI must:
1. Record major work
2. Update memory docs
3. Preserve decisions
4. Define next steps
5. Output safe commit workflow

---

## Core Rules

### Always
- Inspect current repo structure first
- Prefer integration over expansion
- Preserve working runtime
- Work on branches
- Keep memory updated

### Never
- Assume missing modules
- Expand architecture blindly
- Auto trade
- Broker login
- Modify broker execution systems
- Create redundant pipelines without inspection

---

## Safety

Investment OS is advisory only.

Never:
- Login broker
- Auto trade
- Execute trades automatically

All trading remains manual.

---

## Current Strategic Focus

Main issue:
Mainline fragmentation

Known mainlines:
1. pipeline/main.py
2. decision/decision_engine.py
3. jobs/daily_run.py

Priority:
Mainline consolidation before expansion

---

## Standard Commands

### Session Start
請先讀 GitHub memory 並恢復工作狀態。

### Session Close
請更新 GitHub memory 並輸出 commit / push 指令。

---

## Principle

Do not rely on AI memory.
Rely on protocol-backed external memory.
