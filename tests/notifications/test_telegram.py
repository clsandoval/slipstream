"""Tests for Telegram notification sending."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import httpx


class TestTelegramConfig:
    """Test Telegram configuration."""

    def test_config_from_dict(self):
        """Create config from dict with all fields."""
        from src.notifications.telegram import TelegramConfig

        data = {
            "bot_token": "123456:ABC-DEF",
            "chat_id": "987654321",
            "enabled": True,
        }

        config = TelegramConfig.from_dict(data)

        assert config.bot_token == "123456:ABC-DEF"
        assert config.chat_id == "987654321"
        assert config.enabled is True

    def test_config_default_enabled(self):
        """Config defaults enabled to True when not specified."""
        from src.notifications.telegram import TelegramConfig

        data = {"bot_token": "123456:ABC", "chat_id": "987654"}

        config = TelegramConfig.from_dict(data)

        assert config.enabled is True

    def test_config_to_dict(self):
        """Config converts to serializable dict."""
        from src.notifications.telegram import TelegramConfig

        config = TelegramConfig(
            bot_token="123456:ABC",
            chat_id="987654",
            enabled=False,
        )

        result = config.to_dict()

        assert result == {
            "bot_token": "123456:ABC",
            "chat_id": "987654",
            "enabled": False,
        }

    def test_config_validates_missing_bot_token(self):
        """Config raises ValueError when bot_token missing."""
        from src.notifications.telegram import TelegramConfig

        data = {"chat_id": "987654"}

        with pytest.raises(ValueError, match="bot_token is required"):
            TelegramConfig.from_dict(data)

    def test_config_validates_missing_chat_id(self):
        """Config raises ValueError when chat_id missing."""
        from src.notifications.telegram import TelegramConfig

        data = {"bot_token": "123456:ABC"}

        with pytest.raises(ValueError, match="chat_id is required"):
            TelegramConfig.from_dict(data)


class TestTelegramNotifier:
    """Test Telegram message sending."""

    @pytest.fixture
    def config(self):
        from src.notifications.telegram import TelegramConfig

        return TelegramConfig(
            bot_token="123456:ABC-DEF",
            chat_id="987654321",
            enabled=True,
        )

    @pytest.fixture
    def disabled_config(self):
        from src.notifications.telegram import TelegramConfig

        return TelegramConfig(
            bot_token="123456:ABC-DEF",
            chat_id="987654321",
            enabled=False,
        )

    @pytest.mark.asyncio
    async def test_send_success(self, config):
        """Send message returns True on success."""
        from src.notifications.telegram import TelegramNotifier

        notifier = TelegramNotifier(config)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await notifier.send("Hello")

            assert result is True
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_api_error(self, config):
        """Send message returns False on API error."""
        from src.notifications.telegram import TelegramNotifier

        notifier = TelegramNotifier(config)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await notifier.send("Hello")

            assert result is False

    @pytest.mark.asyncio
    async def test_send_network_error(self, config):
        """Send message returns False on network error."""
        from src.notifications.telegram import TelegramNotifier

        notifier = TelegramNotifier(config)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.RequestError("Connection failed")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await notifier.send("Hello")

            assert result is False

    @pytest.mark.asyncio
    async def test_send_disabled(self, disabled_config):
        """Send skips when disabled, returns True."""
        from src.notifications.telegram import TelegramNotifier

        notifier = TelegramNotifier(disabled_config)

        with patch("httpx.AsyncClient") as mock_client_class:
            result = await notifier.send("Hello")

            assert result is True
            mock_client_class.assert_not_called()

    def test_api_url(self, config):
        """API URL formed correctly from bot token."""
        from src.notifications.telegram import TelegramNotifier

        notifier = TelegramNotifier(config)

        assert (
            notifier.api_url
            == "https://api.telegram.org/bot123456:ABC-DEF/sendMessage"
        )

    @pytest.mark.asyncio
    async def test_payload_format(self, config):
        """Payload includes chat_id and text."""
        from src.notifications.telegram import TelegramNotifier

        notifier = TelegramNotifier(config)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await notifier.send("Test message")

            call_kwargs = mock_client.post.call_args
            assert call_kwargs[1]["json"] == {
                "chat_id": "987654321",
                "text": "Test message",
            }

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, config):
        """Rate limit (429) returns False."""
        from src.notifications.telegram import TelegramNotifier

        notifier = TelegramNotifier(config)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await notifier.send("Hello")

            assert result is False
