from __future__ import annotations
from unittest.mock import MagicMock, patch


def test_ask_claude_returns_text_response(monkeypatch):
    """ask_claude() returns the text content from Claude's response."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    fake_response = MagicMock()
    fake_response.content = [MagicMock(text="廣達今日訊號強，可考慮進場。")]
    with patch("anthropic.Anthropic") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.messages.create.return_value = fake_response
        with patch("telegram_bot.adapters.investment_os.build_context_summary", return_value="ctx"):
            from telegram_bot.adapters.claude_client import ask_claude
            result = ask_claude("今天廣達值得進嗎？")
    assert "廣達" in result


def test_ask_claude_returns_error_message_on_api_failure(monkeypatch):
    """ask_claude() returns a user-friendly error string when APIError is raised."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    import anthropic
    with patch("anthropic.Anthropic") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.messages.create.side_effect = anthropic.APIStatusError(
            "server error", response=MagicMock(status_code=500), body={}
        )
        with patch("telegram_bot.adapters.investment_os.build_context_summary", return_value="ctx"):
            from telegram_bot.adapters import claude_client
            import importlib
            importlib.reload(claude_client)
            result = claude_client.ask_claude("test")
    assert "暫時無法回覆" in result
