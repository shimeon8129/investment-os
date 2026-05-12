from __future__ import annotations
import anthropic
from telegram_bot.config import ANTHROPIC_API_KEY
from telegram_bot.adapters.investment_os import build_context_summary

_client: anthropic.Anthropic | None = None

_SYSTEM = (
    "你是 Investment OS 分析助手。Investment OS 是一套台股量化投資自動化系統。"
    "以下是今日最新市場資料，請根據這些資料回答問題。"
    "回答請保持簡潔，使用繁體中文，必要時用條列式呈現。"
)


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def ask_claude(question: str) -> str:
    context = build_context_summary()
    try:
        response = _get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=f"{_SYSTEM}\n\n---\n{context}\n---",
            messages=[{"role": "user", "content": question}],
        )
        return response.content[0].text
    except anthropic.APIError as exc:
        return f"Claude 暫時無法回覆，請稍後再試。（{exc}）"
