"""Telegram Bot API integration for notifications."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""

    bot_token: str
    chat_id: str
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TelegramConfig:
        """
        Create config from dict.

        Args:
            data: Dict with bot_token, chat_id, and optional enabled

        Returns:
            TelegramConfig instance

        Raises:
            ValueError: If required fields missing
        """
        if "bot_token" not in data:
            raise ValueError("bot_token is required")
        if "chat_id" not in data:
            raise ValueError("chat_id is required")

        return cls(
            bot_token=data["bot_token"],
            chat_id=data["chat_id"],
            enabled=data.get("enabled", True),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dict.

        Returns:
            Serializable dict
        """
        return {
            "bot_token": self.bot_token,
            "chat_id": self.chat_id,
            "enabled": self.enabled,
        }


class TelegramNotifier:
    """Send messages via Telegram Bot API."""

    def __init__(self, config: TelegramConfig):
        """
        Initialize notifier with config.

        Args:
            config: Telegram configuration
        """
        self.config = config
        self.api_url = f"https://api.telegram.org/bot{config.bot_token}/sendMessage"

    async def send(self, message: str) -> bool:
        """
        Send message to configured chat.

        Args:
            message: Text to send

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.config.enabled:
            logger.debug("Telegram notifications disabled, skipping")
            return True

        payload = {
            "chat_id": self.config.chat_id,
            "text": message,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    timeout=10.0,
                )

            if response.status_code == 200:
                logger.info("Telegram message sent successfully")
                return True
            elif response.status_code == 429:
                logger.warning("Telegram rate limited")
                return False
            else:
                logger.error(f"Telegram API error: {response.status_code}")
                return False

        except httpx.RequestError as e:
            logger.error(f"Telegram network error: {e}")
            return False
