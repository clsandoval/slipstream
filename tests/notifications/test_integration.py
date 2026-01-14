"""Tests for MCP server notification integration."""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestMCPNotificationIntegration:
    """Test notification integration with MCP server."""

    @pytest.fixture
    def sample_session(self):
        return {
            "session_id": "2024-01-15_1430",
            "stroke_count": 842,
            "stroke_rate_avg": 53.2,
            "duration_seconds": 1934,
            "estimated_distance_m": 1515.6,
        }

    @pytest.mark.asyncio
    async def test_end_session_triggers_notification(self, sample_session):
        """end_session triggers notification when manager configured."""
        from src.notifications.manager import NotificationManager

        mock_notifier = AsyncMock()
        mock_notifier.send.return_value = True
        manager = NotificationManager(notifier=mock_notifier)

        result = await manager.on_session_end(sample_session)

        assert result is True
        mock_notifier.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_notification_failure_doesnt_block(self, sample_session):
        """Notification failure returns False but doesn't raise."""
        from src.notifications.manager import NotificationManager

        mock_notifier = AsyncMock()
        mock_notifier.send.return_value = False
        manager = NotificationManager(notifier=mock_notifier)

        result = await manager.on_session_end(sample_session)

        # Returns False but no exception
        assert result is False

    @pytest.mark.asyncio
    async def test_session_data_passed(self, sample_session):
        """Session data passed correctly to notification."""
        from src.notifications.manager import NotificationManager

        mock_notifier = AsyncMock()
        mock_notifier.send.return_value = True
        manager = NotificationManager(notifier=mock_notifier)

        await manager.on_session_end(sample_session)

        sent_message = mock_notifier.send.call_args[0][0]
        # Verify session data appears in formatted message
        assert "842" in sent_message  # Stroke count
        assert "32:14" in sent_message  # Duration

    @pytest.mark.asyncio
    async def test_no_notification_without_manager(self, sample_session):
        """No notification attempt when manager has no notifier."""
        from src.notifications.manager import NotificationManager

        manager = NotificationManager(notifier=None)

        result = await manager.on_session_end(sample_session)

        # Returns True (no-op success)
        assert result is True


class TestConfigIntegration:
    """Test config loading for notifications."""

    def test_config_has_telegram_section(self, temp_slipstream_dir):
        """Config with telegram section creates TelegramNotifier."""
        from src.notifications.manager import NotificationManager
        from src.notifications.telegram import TelegramNotifier

        config_path = temp_slipstream_dir / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "dps_ratio": 1.8,
                    "telegram": {
                        "bot_token": "123456:ABC-DEF",
                        "chat_id": "987654321",
                        "enabled": True,
                    },
                }
            )
        )

        manager = NotificationManager.from_config(config_path)

        assert manager.notifier is not None
        assert isinstance(manager.notifier, TelegramNotifier)

    def test_config_telegram_optional(self, temp_slipstream_dir):
        """Config without telegram section creates manager with no notifier."""
        from src.notifications.manager import NotificationManager

        config_path = temp_slipstream_dir / "config.json"
        config_path.write_text(json.dumps({"dps_ratio": 1.8}))

        manager = NotificationManager.from_config(config_path)

        assert manager.notifier is None
