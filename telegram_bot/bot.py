from __future__ import annotations
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from telegram_bot.config import BOT_TOKEN, get_allowed_chat_ids
from telegram_bot.handlers.ask import cmd_ask
from telegram_bot.handlers.commands import (
    cmd_daily,
    cmd_help,
    cmd_intraday,
    cmd_start,
    cmd_status,
    cmd_watchlist,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger(__name__)


def _auth(handler):
    """Decorator: reject any update not from an allowed chat ID."""
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_chat.id not in get_allowed_chat_ids():
            log.warning("Unauthorized access from chat_id=%s", update.effective_chat.id)
            await update.message.reply_text("Unauthorized.")
            return
        await handler(update, ctx)
    return wrapper


def main() -> None:
    if not BOT_TOKEN:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN is not set")
    if not get_allowed_chat_ids():
        raise EnvironmentError("ALLOWED_CHAT_IDS is not set")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    for name, handler in [
        ("start", cmd_start),
        ("help", cmd_help),
        ("status", cmd_status),
        ("watchlist", cmd_watchlist),
        ("daily", cmd_daily),
        ("intraday", cmd_intraday),
        ("ask", cmd_ask),
    ]:
        app.add_handler(CommandHandler(name, _auth(handler)))

    log.info("Investment OS Telegram Bot started, polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
