"""Tests for user configuration management."""

import json
from pathlib import Path

import pytest

from src.mcp.storage.config import Config, NotificationConfig


class TestNotificationConfig:
    """Tests for NotificationConfig dataclass."""

    def test_notification_config_defaults(self) -> None:
        """NotificationConfig has correct default values."""
        config = NotificationConfig()

        assert config.telegram_enabled is False
        assert config.telegram_chat_id is None
        assert config.sms_enabled is False
        assert config.sms_phone is None

    def test_notification_config_custom_values(self) -> None:
        """NotificationConfig accepts custom values."""
        config = NotificationConfig(
            telegram_enabled=True,
            telegram_chat_id="123456789",
            sms_enabled=True,
            sms_phone="+1234567890",
        )

        assert config.telegram_enabled is True
        assert config.telegram_chat_id == "123456789"
        assert config.sms_enabled is True
        assert config.sms_phone == "+1234567890"


class TestConfig:
    """Tests for Config class."""

    def test_config_defaults(self) -> None:
        """Config has correct default values."""
        config = Config()

        assert config.dps_ratio == 1.8
        assert config.notifications.telegram_enabled is False
        assert config.notifications.sms_enabled is False

    def test_load_config(self, temp_slipstream_dir: Path) -> None:
        """Load config from existing file."""
        config_path = temp_slipstream_dir / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "dps_ratio": 2.0,
                    "notifications": {
                        "telegram_enabled": True,
                        "telegram_chat_id": "12345",
                        "sms_enabled": False,
                        "sms_phone": None,
                    },
                }
            )
        )

        config = Config.load(config_path)

        assert config.dps_ratio == 2.0
        assert config.notifications.telegram_enabled is True
        assert config.notifications.telegram_chat_id == "12345"

    def test_load_creates_default_if_missing(self, temp_slipstream_dir: Path) -> None:
        """Load creates default config if file doesn't exist."""
        config_path = temp_slipstream_dir / "config.json"
        assert not config_path.exists()

        config = Config.load(config_path)

        assert config_path.exists()
        assert config.dps_ratio == 1.8
        assert config.notifications.telegram_enabled is False

    def test_save_config(self, temp_slipstream_dir: Path) -> None:
        """Save config to file."""
        config_path = temp_slipstream_dir / "config.json"
        config = Config(
            dps_ratio=2.5,
            notifications=NotificationConfig(telegram_enabled=True),
            config_path=config_path,
        )

        config.save()

        saved_data = json.loads(config_path.read_text())
        assert saved_data["dps_ratio"] == 2.5
        assert saved_data["notifications"]["telegram_enabled"] is True

    def test_dps_ratio_property(self, temp_slipstream_dir: Path) -> None:
        """Get DPS ratio."""
        config = Config(dps_ratio=1.8)
        assert config.dps_ratio == 1.8

    def test_notification_settings(self, temp_slipstream_dir: Path) -> None:
        """Access notification settings."""
        config = Config(
            notifications=NotificationConfig(
                telegram_enabled=True,
                telegram_chat_id="12345",
            )
        )

        assert config.notifications.telegram_enabled is True
        assert config.notifications.telegram_chat_id == "12345"

    def test_load_creates_parent_dir(self, tmp_path: Path) -> None:
        """Load creates parent directory if it doesn't exist."""
        config_path = tmp_path / "nonexistent" / "config.json"
        assert not config_path.parent.exists()

        config = Config.load(config_path)

        assert config_path.parent.exists()
        assert config_path.exists()
