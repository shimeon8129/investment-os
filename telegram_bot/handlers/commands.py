from __future__ import annotations
import subprocess
import sys
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.adapters import investment_os as ios

ROOT = Path(__file__).resolve().parents[2]

HELP_TEXT = (
    "*Investment OS Bot*\n\n"
    "/status — 今日快照（候選、決策）\n"
    "/watchlist — 明日 watchlist\n"
    "/daily — 觸發 daily\\_run\n"
    "/intraday — 觸發盤中觀察\n"
    "/ask \\[問題\\] — 問 Claude\n"
    "/help — 顯示說明"
)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Investment OS Bot 啟動。\n\n{HELP_TEXT}", parse_mode="Markdown")


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    snap = ios.load_snapshot()
    ranked = snap.get("ranked", [])[:5]
    decisions = snap.get("decisions", [])
    if not ranked and not decisions:
        await update.message.reply_text("暫無資料，請先執行 /daily")
        return
    lines = ["*今日快照*\n", "*候選 Top 5:*"]
    for r in ranked:
        lines.append(f"  {r.get('rank','?')}\\. {r.get('ticker','')} {r.get('name','')} score={r.get('score','?')}")
    if decisions:
        lines.append("\n*決策:*")
        for d in decisions:
            lines.append(f"  {d.get('ticker','')} {d.get('action','')} — {d.get('reason','')}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_watchlist(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    snap = ios.load_snapshot()
    watchlist = snap.get("watchlist", [])
    if not watchlist:
        await update.message.reply_text("暫無明日 watchlist 資料")
        return
    lines = ["*明日 Watchlist*\n"]
    for w in watchlist:
        ticker = w.get("ticker", "")
        name = w.get("name") or "—"
        rank = w.get("last_rank", "—")
        lines.append(f"  {ticker} {name} 最後排名={rank}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def _run_job(update: Update, script_name: str, timeout: int) -> None:
    script = ROOT / "jobs" / script_name
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, timeout=timeout,
    )
    status = "✅ 完成" if result.returncode == 0 else f"❌ 失敗（exit {result.returncode}）"
    tail = (result.stdout or result.stderr or "")[-500:]
    await update.message.reply_text(
        f"{script_name} {status}\n\n```\n{tail}\n```", parse_mode="Markdown"
    )


async def cmd_daily(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("正在啟動 daily\\_run，完成後推送摘要...", parse_mode="Markdown")
    await _run_job(update, "daily_run.py", timeout=300)


async def cmd_intraday(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("正在啟動盤中觀察...", parse_mode="Markdown")
    await _run_job(update, "intraday_observation.py", timeout=180)
