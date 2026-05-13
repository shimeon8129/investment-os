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
    "/marketstatus — 今日快照（候選、決策）\n"
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


async def cmd_marketstatus(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    snap = ios.load_mainline_snapshot()
    ranked = snap.get("ranked", [])[:5]
    decisions = snap.get("decisions", {})
    if not ranked and not decisions:
        await update.message.reply_text("暫無資料，請先執行 /daily")
        return
    name_map = {r.get("ticker", ""): r.get("name", "") for r in snap.get("ranked", [])}
    market_state = snap.get("market_state", "—")
    vix = snap.get("vix_value", 0)
    lines = [f"*今日快照*  市場: {market_state} | VIX: {vix:.2f}\n", "*候選 Top 5:*"]
    for i, r in enumerate(ranked, 1):
        ticker = r.get("ticker", "")
        name = r.get("name", "")
        score = r.get("score", 0)
        signal = r.get("signal", "")
        lines.append(f"  {i}\\. {ticker} {name}  score={score:.1f} | {signal}")
    if decisions:
        lines.append("\n*決策:*")
        for ticker, d in decisions.items():
            name = name_map.get(ticker, "")
            action = d.get("action", "")
            reason = d.get("reason", "")
            size = d.get("position_size", 0)
            lines.append(f"  {ticker} {name} → {action}（{reason}，倉位 {size*100:.0f}%）")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_watchlist(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    snap = ios.load_mainline_snapshot()
    ranked = snap.get("ranked", [])
    if not ranked:
        await update.message.reply_text("暫無資料，請先執行 /daily")
        return
    market_state = snap.get("market_state", "—")
    vix = snap.get("vix_value", 0)
    lines = [f"*明日 Watchlist*  市場: {market_state} | VIX: {vix:.2f}\n"]
    for i, r in enumerate(ranked[:10], 1):
        ticker = r.get("ticker", "")
        name = r.get("name", "")
        score = r.get("score", 0)
        signal = r.get("signal", "")
        lines.append(f"  {i}\\. {ticker} {name}  {score:.1f} | {signal}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def _run_job(update: Update, script_name: str, timeout: int) -> None:
    script = ROOT / "jobs" / script_name
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=timeout,
        )
        status = "✅ 完成" if result.returncode == 0 else f"❌ 失敗（exit {result.returncode}）"
        tail = (result.stdout or result.stderr or "")[-500:]
        await update.message.reply_text(
            f"{script_name} {status}\n\n```\n{tail}\n```", parse_mode="Markdown"
        )
    except subprocess.TimeoutExpired:
        await update.message.reply_text(
            f"❌ {script_name} 超時（>{timeout}s），已中止", parse_mode="Markdown"
        )


async def cmd_daily(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("正在啟動 daily\\_run，完成後推送摘要...", parse_mode="Markdown")
    script = ROOT / "jobs" / "daily_run.py"
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            tail = (result.stdout or result.stderr or "")[-400:]
            await update.message.reply_text(f"❌ daily\\_run 失敗\n\n```\n{tail}\n```", parse_mode="Markdown")
            return
        snap = ios.load_mainline_snapshot()
        ranked = snap.get("ranked", [])[:5]
        decisions = snap.get("decisions", {})
        name_map = {r.get("ticker", ""): r.get("name", "") for r in snap.get("ranked", [])}
        market_state = snap.get("market_state", "—")
        vix = snap.get("vix_value", 0)
        lines = [f"✅ *daily\\_run 完成*  市場: {market_state} | VIX: {vix:.2f}\n", "*Top 5 候選:*"]
        for i, r in enumerate(ranked, 1):
            ticker = r.get("ticker", "")
            name = r.get("name", "")
            score = r.get("score", 0)
            signal = r.get("signal", "")
            lines.append(f"  {i}\\. {ticker} {name}  {score:.1f} | {signal}")
        if decisions:
            lines.append("\n*決策:*")
            for ticker, d in decisions.items():
                name = name_map.get(ticker, "")
                action = d.get("action", "")
                reason = d.get("reason", "")
                size = d.get("position_size", 0)
                lines.append(f"  {ticker} {name} → {action}（{reason}，倉位 {size*100:.0f}%）")
        lines.append("\n⚠️ Advisory only，不自動下單。")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except subprocess.TimeoutExpired:
        await update.message.reply_text("❌ daily\\_run 超時（>300s），已中止", parse_mode="Markdown")


async def cmd_intraday(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("正在啟動盤中觀察...", parse_mode="Markdown")
    await _run_job(update, "intraday_observation.py", timeout=180)
