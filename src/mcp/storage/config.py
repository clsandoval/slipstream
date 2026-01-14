"""User configuration management."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class NotificationConfig:
    """Notification settings for session summaries."""

    telegram_enabled: bool = False
    telegram_chat_id: str | None = None
    sms_enabled: bool = False
    sms_phone: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "telegram_enabled": self.telegram_enabled,
            "telegram_chat_id": self.telegram_chat_id,
            "sms_enabled": self.sms_enabled,
            "sms_phone": self.sms_phone,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NotificationConfig:
        """Create from dictionary."""
        return cls(
            telegram_enabled=data.get("telegram_enabled", False),
            telegram_chat_id=data.get("telegram_chat_id"),
            sms_enabled=data.get("sms_enabled", False),
            sms_phone=data.get("sms_phone"),
        )


def _default_config_path() -> Path:
    """Get default config path."""
    return Path.home() / ".slipstream" / "config.json"


@dataclass
class Config:
    """User configuration for Slipstream."""

    dps_ratio: float = 1.8
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    config_path: Path = field(default_factory=_default_config_path)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (excluding config_path)."""
        return {
            "dps_ratio": self.dps_ratio,
            "notifications": self.notifications.to_dict(),
        }

    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        """Load configuration from file, creating default if missing."""
        config_path = path or _default_config_path()

        if config_path.exists():
            data = json.loads(config_path.read_text())
            return cls(
                dps_ratio=data.get("dps_ratio", 1.8),
                notifications=NotificationConfig.from_dict(
                    data.get("notifications", {})
                ),
                config_path=config_path,
            )
        else:
            config = cls(config_path=config_path)
            config.save()
            return config
