from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot.adapters.claude_client import ask_claude


async def cmd_ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    question = " ".join(ctx.args) if ctx.args else ""
    if not question:
        await update.message.reply_text("用法：/ask \\[你的問題\\]\n例如：/ask 今天 2382 值得進嗎", parse_mode="Markdown")
        return
    await update.message.reply_text("思考中...")
    reply = ask_claude(question)
    await update.message.reply_text(reply)
