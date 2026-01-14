"""Tests for notification orchestration."""

import json
import pytest
from unittest.mock import AsyncMock, patch


class TestNotificationManager:
    """Test notification orchestration."""

    @pytest.fixture
    def mock_notifier(self):
        notifier = AsyncMock()
        notifier.send.return_value = True
        return notifier

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
    async def test_on_session_end_sends_message(self, mock_notifier, sample_session):
        """on_session_end sends formatted message via notifier."""
        from src.notifications.manager import NotificationManager

        manager = NotificationManager(notifier=mock_notifier)

        await manager.on_session_end(sample_session)

        mock_notifier.send.assert_called_once()
        sent_message = mock_notifier.send.call_args[0][0]
        assert isinstance(sent_message, str)
        assert len(sent_message) > 0

    @pytest.mark.asyncio
    async def test_uses_formatter(self, mock_notifier, sample_session):
        """Message contains session data from formatter."""
        from src.notifications.manager import NotificationManager

        manager = NotificationManager(notifier=mock_notifier)

        await manager.on_session_end(sample_session)

        sent_message = mock_notifier.send.call_args[0][0]
        # Check that session data appears in message
        assert "32:14" in sent_message  # Duration
        assert "842" in sent_message  # Stroke count

    @pytest.mark.asyncio
    async def test_returns_success(self, mock_notifier, sample_session):
        """Returns True when notifier succeeds."""
        from src.notifications.manager import NotificationManager

        mock_notifier.send.return_value = True
        manager = NotificationManager(notifier=mock_notifier)

        result = await manager.on_session_end(sample_session)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_failure(self, mock_notifier, sample_session):
        """Returns False when notifier fails."""
        from src.notifications.manager import NotificationManager

        mock_notifier.send.return_value = False
        manager = NotificationManager(notifier=mock_notifier)

        result = await manager.on_session_end(sample_session)

        assert result is False

    @pytest.mark.asyncio
    async def test_handles_exception(self, mock_notifier, sample_session):
        """Returns False when notifier raises exception."""
        from src.notifications.manager import NotificationManager

        mock_notifier.send.side_effect = Exception("Network error")
        manager = NotificationManager(notifier=mock_notifier)

        result = await manager.on_session_end(sample_session)

        assert result is False

    @pytest.mark.asyncio
    async def test_no_notifier_configured(self, sample_session):
        """Returns True when no notifier configured (no-op)."""
        from src.notifications.manager import NotificationManager

        manager = NotificationManager(notifier=None)

        result = await manager.on_session_end(sample_session)

        assert result is True

    @pytest.mark.asyncio
    async def test_logs_result(self, mock_notifier, sample_session, caplog):
        """Logs success/failure message."""
        from src.notifications.manager import NotificationManager
        import logging

        manager = NotificationManager(notifier=mock_notifier)

        with caplog.at_level(logging.INFO):
            await manager.on_session_end(sample_session)

        assert "notification sent" in caplog.text.lower()


class TestNotificationManagerFactory:
    """Test manager creation from config."""

    def test_create_with_telegram(self, temp_slipstream_dir):
        """Create manager with TelegramNotifier from config."""
        from src.notifications.manager import NotificationManager

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

    def test_create_without_telegram(self, temp_slipstream_dir):
        """Create manager without notifier when telegram not in config."""
        from src.notifications.manager import NotificationManager

        config_path = temp_slipstream_dir / "config.json"
        config_path.write_text(json.dumps({"dps_ratio": 1.8}))

        manager = NotificationManager.from_config(config_path)

        assert manager.notifier is None

    def test_create_telegram_disabled(self, temp_slipstream_dir):
        """Create manager with disabled TelegramNotifier."""
        from src.notifications.manager import NotificationManager
        from src.notifications.telegram import TelegramNotifier

        config_path = temp_slipstream_dir / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "telegram": {
                        "bot_token": "123456:ABC",
                        "chat_id": "987654",
                        "enabled": False,
                    }
                }
            )
        )

        manager = NotificationManager.from_config(config_path)

        assert manager.notifier is not None
        assert isinstance(manager.notifier, TelegramNotifier)
        assert manager.notifier.config.enabled is False

    def test_create_from_missing_config(self, temp_slipstream_dir):
        """Create manager with no notifier when config file missing."""
        from src.notifications.manager import NotificationManager

        config_path = temp_slipstream_dir / "nonexistent.json"

        manager = NotificationManager.from_config(config_path)

        assert manager.notifier is None

    def test_create_with_invalid_telegram_config(self, temp_slipstream_dir):
        """Create manager with no notifier when telegram config invalid."""
        from src.notifications.manager import NotificationManager

        config_path = temp_slipstream_dir / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "telegram": {
                        # Missing required bot_token
                        "chat_id": "987654",
                    }
                }
            )
        )

        manager = NotificationManager.from_config(config_path)

        assert manager.notifier is None
