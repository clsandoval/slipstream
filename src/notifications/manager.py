"""Notification orchestration for session events."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.notifications.formatter import format_summary
from src.notifications.telegram import TelegramConfig, TelegramNotifier

logger = logging.getLogger(__name__)


@dataclass
class NotificationManager:
    """Orchestrates session end notifications."""

    notifier: TelegramNotifier | None = None

    async def on_session_end(self, session: dict[str, Any]) -> bool:
        """
        Send notification for completed session.

        Args:
            session: Session data dict

        Returns:
            True if notification sent (or no notifier configured)
        """
        if self.notifier is None:
            logger.debug("No notifier configured, skipping notification")
            return True

        try:
            message = format_summary(session)
            success = await self.notifier.send(message)

            if success:
                logger.info(
                    f"Session notification sent for {session.get('session_id')}"
                )
            else:
                logger.warning(
                    f"Failed to send notification for {session.get('session_id')}"
                )

            return success

        except Exception as e:
            logger.error(f"Notification error: {e}")
            return False

    @classmethod
    def from_config(cls, config_path: Path) -> NotificationManager:
        """
        Create manager from config file.

        Args:
            config_path: Path to config.json

        Returns:
            Configured NotificationManager
        """
        notifier = None

        if config_path.exists():
            try:
                config_data = json.loads(config_path.read_text())
                telegram_config = config_data.get("telegram")

                if telegram_config:
                    try:
                        tg_config = TelegramConfig.from_dict(telegram_config)
                        notifier = TelegramNotifier(tg_config)
                        logger.info("Telegram notifier configured")
                    except ValueError as e:
                        logger.warning(f"Invalid telegram config: {e}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse config: {e}")

        return cls(notifier=notifier)
