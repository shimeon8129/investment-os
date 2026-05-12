from __future__ import annotations
from unittest.mock import patch, MagicMock


def test_send_notification_silent_when_token_missing(monkeypatch):
    """send_notification() does nothing when TELEGRAM_BOT_TOKEN is unset."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    from utils.telegram_notify import send_notification
    send_notification("hello")  # Must not raise


def test_send_notification_silent_when_chat_id_missing(monkeypatch):
    """send_notification() does nothing when TELEGRAM_CHAT_ID is unset."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    from utils.telegram_notify import send_notification
    send_notification("hello")  # Must not raise


def test_send_notification_posts_to_telegram_api(monkeypatch):
    """send_notification() calls the Telegram sendMessage endpoint."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_ctx = MagicMock()
        mock_urlopen.return_value.__enter__ = lambda s: mock_ctx
        mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)
        from utils.telegram_notify import send_notification
        send_notification("test message")
    assert mock_urlopen.called
    req = mock_urlopen.call_args[0][0]
    assert "fake-token" in req.full_url
    assert b"test message" in req.data


def test_send_notification_handles_network_error(monkeypatch):
    """send_notification() swallows exceptions and does not re-raise."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    with patch("urllib.request.urlopen", side_effect=OSError("network error")):
        from utils.telegram_notify import send_notification
        send_notification("test")  # Must not raise
