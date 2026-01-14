# Notifications - TDD Implementation Plan

## Overview

Test-Driven Development plan for Branch 7: Notifications. Telegram integration to send session summaries after workout completion.

**Dependencies**: Branch 2 (mcp-server-core), Branch 4 (swim-metrics)
**Complexity**: Low

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       NOTIFICATIONS ARCHITECTURE                             │
│                                                                              │
│  MCP Server                           Notifications                          │
│  ┌──────────────────┐                ┌──────────────────────────────────────┐│
│  │ end_session()    │───triggers────▶│ NotificationManager                  ││
│  │   session_data   │                │   └─ on_session_end(session)         ││
│  └──────────────────┘                │                                      ││
│                                      │ SessionFormatter                      ││
│  Session Storage                     │   └─ format_summary(session) → str   ││
│  ┌──────────────────┐                │                                      ││
│  │ session.json     │                │ TelegramNotifier                      ││
│  │   stroke_count   │                │   └─ send(message) → bool            ││
│  │   stroke_rate_avg│                └──────────────────────────────────────┘│
│  │   duration_secs  │                              │                         │
│  │   distance_m     │                              ▼                         │
│  └──────────────────┘                    Telegram Bot API                    │
│                                          POST /sendMessage                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **TelegramNotifier**: Simple async HTTP client using `httpx`. No external Telegram library needed for just `sendMessage`.

2. **SessionFormatter**: Pure function that takes session dict, returns formatted string. Easy to test, no side effects.

3. **NotificationManager**: Orchestrates the flow. Called by MCP server on session end. Handles enable/disable logic.

4. **Config in ~/.slipstream/config.json**: Telegram settings stored alongside other user config.

---

## Phase 1: Session Formatter

**Goal**: Format session data into readable Telegram message.

### Tests First (`tests/notifications/test_formatter.py`)

```python
import pytest
from datetime import datetime


class TestSessionFormatter:
    """Test session summary formatting."""

    # Test 1: Basic format with all fields
    def test_format_complete_session(self):
        # Given session with all data populated
        session = {
            "session_id": "2024-01-15_1430",
            "started_at": "2024-01-15T14:30:00+00:00",
            "ended_at": "2024-01-15T15:02:14+00:00",
            "stroke_count": 842,
            "stroke_rate_avg": 53.2,
            "duration_seconds": 1934,
            "estimated_distance_m": 1515.6,
        }
        # When format_summary called
        # Then returns formatted message with all fields

    # Test 2: Duration formatting
    @pytest.mark.parametrize("seconds,expected", [
        (60, "1:00"),
        (125, "2:05"),
        (1934, "32:14"),
        (3661, "1:01:01"),
    ])
    def test_format_duration(self, seconds, expected):
        # Given session with duration_seconds
        # When format_summary called
        # Then duration formatted correctly

    # Test 3: Distance formatting with comma separator
    @pytest.mark.parametrize("meters,expected", [
        (150.0, "150m"),
        (1200.5, "1,201m"),
        (2500.0, "2,500m"),
    ])
    def test_format_distance(self, meters, expected):
        # Given session with estimated_distance_m
        # When format_summary called
        # Then distance formatted with commas, rounded

    # Test 4: Stroke rate formatting
    def test_format_stroke_rate(self):
        # Given session with stroke_rate_avg=53.2
        # When format_summary called
        # Then shows "53/min" (rounded to int)

    # Test 5: Handle zero/missing values gracefully
    def test_format_empty_session(self):
        # Given session with zeros
        session = {
            "session_id": "2024-01-15_1430",
            "stroke_count": 0,
            "stroke_rate_avg": 0.0,
            "duration_seconds": 0,
            "estimated_distance_m": 0.0,
        }
        # When format_summary called
        # Then returns valid message without errors

    # Test 6: Message includes emoji header
    def test_format_includes_header(self):
        # Given any session
        # When format_summary called
        # Then message starts with "🏊 Swim Session Complete"

    # Test 7: Message is valid for Telegram (under 4096 chars)
    def test_format_message_length(self):
        # Given session with maximum reasonable values
        # When format_summary called
        # Then len(message) < 4096
```

### Implementation

```python
# src/notifications/formatter.py
from typing import Any


def format_duration(seconds: int) -> str:
    """Format seconds as MM:SS or H:MM:SS."""
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"


def format_distance(meters: float) -> str:
    """Format distance with comma separator."""
    rounded = round(meters)
    return f"{rounded:,}m"


def format_summary(session: dict[str, Any]) -> str:
    """
    Format session data as Telegram message.

    Args:
        session: Session dict from SessionStorage

    Returns:
        Formatted message string
    """
    duration = format_duration(session.get("duration_seconds", 0))
    distance = format_distance(session.get("estimated_distance_m", 0.0))
    stroke_rate = round(session.get("stroke_rate_avg", 0.0))
    stroke_count = session.get("stroke_count", 0)

    lines = [
        "🏊 Swim Session Complete",
        "",
        f"Duration: {duration}",
        f"Est. Distance: ~{distance}",
        f"Avg Stroke Rate: {stroke_rate}/min",
        f"Total Strokes: {stroke_count:,}",
    ]

    return "\n".join(lines)
```

---

## Phase 2: Telegram Notifier

**Goal**: Send messages via Telegram Bot API.

### Tests First (`tests/notifications/test_telegram.py`)

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestTelegramConfig:
    """Test Telegram configuration."""

    # Test 1: Config from dict
    def test_config_from_dict(self):
        # Given dict with telegram settings
        data = {
            "bot_token": "123456:ABC-DEF",
            "chat_id": "987654321",
            "enabled": True,
        }
        # When TelegramConfig.from_dict(data)
        # Then config has correct values

    # Test 2: Config defaults enabled to True
    def test_config_default_enabled(self):
        # Given dict without enabled field
        data = {"bot_token": "123456:ABC", "chat_id": "987654"}
        # When TelegramConfig.from_dict(data)
        # Then enabled defaults to True

    # Test 3: Config to dict
    def test_config_to_dict(self):
        # Given TelegramConfig instance
        # When to_dict() called
        # Then returns serializable dict

    # Test 4: Config validates required fields
    def test_config_validates_required(self):
        # Given dict missing bot_token
        # When TelegramConfig.from_dict(data)
        # Then raises ValueError


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

    # Test 5: Send message successfully
    @pytest.mark.asyncio
    async def test_send_success(self, config):
        # Given notifier with valid config
        # And mocked httpx returning 200
        # When send("Hello") called
        # Then returns True
        # And POST made to correct URL with correct payload

    # Test 6: Send message returns False on API error
    @pytest.mark.asyncio
    async def test_send_api_error(self, config):
        # Given mocked httpx returning 400
        # When send("Hello") called
        # Then returns False
        # And no exception raised

    # Test 7: Send message returns False on network error
    @pytest.mark.asyncio
    async def test_send_network_error(self, config):
        # Given mocked httpx raising ConnectError
        # When send("Hello") called
        # Then returns False
        # And no exception raised

    # Test 8: Send skips when disabled
    @pytest.mark.asyncio
    async def test_send_disabled(self):
        # Given config with enabled=False
        # When send("Hello") called
        # Then returns True (no-op success)
        # And no HTTP request made

    # Test 9: Correct API URL formation
    def test_api_url(self, config):
        # Given config with bot_token="123456:ABC"
        # When notifier created
        # Then api_url is "https://api.telegram.org/bot123456:ABC/sendMessage"

    # Test 10: Payload includes chat_id and text
    @pytest.mark.asyncio
    async def test_payload_format(self, config):
        # Given notifier
        # When send("Test message") called
        # Then payload is {"chat_id": "987654321", "text": "Test message"}

    # Test 11: Handles rate limiting (429)
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, config):
        # Given mocked httpx returning 429
        # When send("Hello") called
        # Then returns False
        # And logs rate limit warning
```

### Implementation

```python
# src/notifications/telegram.py
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
        """Create config from dict."""
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
        """Convert to dict."""
        return {
            "bot_token": self.bot_token,
            "chat_id": self.chat_id,
            "enabled": self.enabled,
        }


class TelegramNotifier:
    """Send messages via Telegram Bot API."""

    def __init__(self, config: TelegramConfig):
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
```

---

## Phase 3: Notification Manager

**Goal**: Orchestrate notification sending on session end.

### Tests First (`tests/notifications/test_manager.py`)

```python
import pytest
from unittest.mock import AsyncMock, Mock, patch


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

    # Test 1: on_session_end sends formatted message
    @pytest.mark.asyncio
    async def test_on_session_end_sends_message(self, mock_notifier, sample_session):
        # Given NotificationManager with mock notifier
        # When on_session_end(session) called
        # Then notifier.send called with formatted message

    # Test 2: Uses formatter for message
    @pytest.mark.asyncio
    async def test_uses_formatter(self, mock_notifier, sample_session):
        # Given manager
        # When on_session_end(session) called
        # Then message contains session data (duration, distance, etc.)

    # Test 3: Returns success status
    @pytest.mark.asyncio
    async def test_returns_success(self, mock_notifier, sample_session):
        # Given notifier.send returns True
        # When on_session_end called
        # Then returns True

    # Test 4: Returns failure status
    @pytest.mark.asyncio
    async def test_returns_failure(self, mock_notifier, sample_session):
        # Given notifier.send returns False
        # When on_session_end called
        # Then returns False

    # Test 5: Handles notifier exception gracefully
    @pytest.mark.asyncio
    async def test_handles_exception(self, mock_notifier, sample_session):
        # Given notifier.send raises exception
        # When on_session_end called
        # Then returns False, no exception propagated

    # Test 6: Skips notification when no notifier configured
    @pytest.mark.asyncio
    async def test_no_notifier_configured(self, sample_session):
        # Given manager with notifier=None
        # When on_session_end called
        # Then returns True (no-op)

    # Test 7: Logs notification result
    @pytest.mark.asyncio
    async def test_logs_result(self, mock_notifier, sample_session, caplog):
        # Given manager
        # When on_session_end called
        # Then logs success/failure message


class TestNotificationManagerFactory:
    """Test manager creation from config."""

    # Test 8: Create from config with telegram enabled
    def test_create_with_telegram(self, temp_slipstream_dir):
        # Given config.json with telegram section
        # When NotificationManager.from_config(config_path) called
        # Then manager has TelegramNotifier

    # Test 9: Create from config without telegram
    def test_create_without_telegram(self, temp_slipstream_dir):
        # Given config.json without telegram section
        # When NotificationManager.from_config(config_path) called
        # Then manager has notifier=None

    # Test 10: Create from config with telegram disabled
    def test_create_telegram_disabled(self, temp_slipstream_dir):
        # Given config.json with telegram.enabled=False
        # When NotificationManager.from_config(config_path) called
        # Then manager has TelegramNotifier with enabled=False
```

### Implementation

```python
# src/notifications/manager.py
from __future__ import annotations

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
                logger.info(f"Session notification sent for {session.get('session_id')}")
            else:
                logger.warning(f"Failed to send notification for {session.get('session_id')}")

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
        import json

        notifier = None

        if config_path.exists():
            config_data = json.loads(config_path.read_text())
            telegram_config = config_data.get("telegram")

            if telegram_config:
                try:
                    tg_config = TelegramConfig.from_dict(telegram_config)
                    notifier = TelegramNotifier(tg_config)
                    logger.info("Telegram notifier configured")
                except ValueError as e:
                    logger.warning(f"Invalid telegram config: {e}")

        return cls(notifier=notifier)
```

---

## Phase 4: MCP Server Integration

**Goal**: Trigger notifications on session end.

### Tests First (`tests/notifications/test_integration.py`)

```python
import pytest
from unittest.mock import AsyncMock, patch


class TestMCPNotificationIntegration:
    """Test notification integration with MCP server."""

    # Test 1: end_session triggers notification
    @pytest.mark.asyncio
    async def test_end_session_triggers_notification(self):
        # Given server with NotificationManager
        # And active session
        # When end_session tool called
        # Then notification_manager.on_session_end called with session data

    # Test 2: Notification failure doesn't block session end
    @pytest.mark.asyncio
    async def test_notification_failure_doesnt_block(self):
        # Given notification_manager.on_session_end returns False
        # When end_session called
        # Then session still ends successfully
        # And response indicates notification failed

    # Test 3: Session data passed correctly to notification
    @pytest.mark.asyncio
    async def test_session_data_passed(self):
        # Given session with stroke_count=100, duration=300
        # When end_session called
        # Then notification receives complete session data

    # Test 4: No notification when manager not configured
    @pytest.mark.asyncio
    async def test_no_notification_without_manager(self):
        # Given server without NotificationManager
        # When end_session called
        # Then session ends, no notification attempt


class TestConfigIntegration:
    """Test config loading for notifications."""

    # Test 5: Config includes telegram section
    def test_config_has_telegram_section(self, temp_slipstream_dir):
        # Given config.json with telegram settings
        # When Config.load() called
        # Then config.telegram is TelegramConfig

    # Test 6: Config telegram section optional
    def test_config_telegram_optional(self, temp_slipstream_dir):
        # Given config.json without telegram
        # When Config.load() called
        # Then config.telegram is None
```

### Implementation Updates

```python
# src/mcp/tools/session_tools.py (update end_session)
async def end_session() -> dict:
    """End the current swim session."""
    # ... existing logic ...

    # After session saved, trigger notification
    if state_store.notification_manager:
        session_data = session_storage.get_session(session_id)
        notification_sent = await state_store.notification_manager.on_session_end(
            session_data
        )
        result["notification_sent"] = notification_sent

    return result
```

```python
# src/mcp/server.py (update)
from src.notifications.manager import NotificationManager


class SwimCoachServer:
    def __init__(self, ...):
        # ... existing init ...

        # Notifications
        config_path = Path.home() / ".slipstream" / "config.json"
        self.notification_manager = NotificationManager.from_config(config_path)
        self.state_store.notification_manager = self.notification_manager
```

---

## Test Fixtures

```python
# tests/notifications/conftest.py

import pytest
from pathlib import Path
import json


@pytest.fixture
def temp_slipstream_dir(tmp_path):
    """Temporary ~/.slipstream directory."""
    slipstream_dir = tmp_path / ".slipstream"
    slipstream_dir.mkdir()
    return slipstream_dir


@pytest.fixture
def config_with_telegram(temp_slipstream_dir):
    """Config with telegram enabled."""
    config_path = temp_slipstream_dir / "config.json"
    config_path.write_text(json.dumps({
        "dps_ratio": 1.8,
        "telegram": {
            "bot_token": "123456:ABC-DEF-test",
            "chat_id": "987654321",
            "enabled": True,
        }
    }))
    return config_path


@pytest.fixture
def sample_session():
    """Sample completed session."""
    return {
        "session_id": "2024-01-15_1430",
        "started_at": "2024-01-15T14:30:00+00:00",
        "ended_at": "2024-01-15T15:02:14+00:00",
        "stroke_count": 842,
        "stroke_rate_avg": 53.2,
        "duration_seconds": 1934,
        "estimated_distance_m": 1515.6,
    }
```

---

## File Structure After TDD

```
src/notifications/
├── __init__.py
├── formatter.py           # format_summary, format_duration, format_distance
├── telegram.py            # TelegramConfig, TelegramNotifier
└── manager.py             # NotificationManager

tests/notifications/
├── __init__.py
├── conftest.py            # Fixtures
├── test_formatter.py      # 7 tests
├── test_telegram.py       # 11 tests
├── test_manager.py        # 10 tests
└── test_integration.py    # 6 tests
```

---

## Implementation Order (TDD Red-Green-Refactor)

| Order | Component | Tests | Implementation |
|-------|-----------|-------|----------------|
| 1 | Formatter | `test_formatter.py` | `formatter.py` |
| 2 | Telegram Config | `test_telegram.py::TestTelegramConfig` | `telegram.py` (config) |
| 3 | Telegram Notifier | `test_telegram.py::TestTelegramNotifier` | `telegram.py` (notifier) |
| 4 | Notification Manager | `test_manager.py` | `manager.py` |
| 5 | MCP Integration | `test_integration.py` | Update `server.py`, `session_tools.py` |

---

## Test Execution

```bash
# Phase 1: Formatter
uv run pytest tests/notifications/test_formatter.py -v

# Phase 2-3: Telegram
uv run pytest tests/notifications/test_telegram.py -v

# Phase 4: Manager
uv run pytest tests/notifications/test_manager.py -v

# Phase 5: Integration
uv run pytest tests/notifications/test_integration.py -v

# All notification tests
uv run pytest tests/notifications/ -v

# Full test suite
uv run pytest tests/ -v
```

---

## Success Criteria

From the requirements:

- [ ] Telegram messages send successfully
- [ ] Summary format is clear and readable
- [ ] Notifications triggered on session end
- [ ] Handles API failures gracefully
- [ ] Configurable enable/disable

Additional criteria:

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] >90% code coverage on new files
- [ ] No notification failure blocks session end
- [ ] Logs provide visibility into notification status

---

## Config Schema

Add to `~/.slipstream/config.json`:

```json
{
  "dps_ratio": 1.8,
  "telegram": {
    "bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
    "chat_id": "987654321",
    "enabled": true
  }
}
```

---

## Notes

1. **httpx over requests**: Using `httpx` for async HTTP. Already a common async HTTP client, no heavy dependencies.

2. **No retry logic**: Simple fail-fast approach. Telegram API is reliable. If it fails once, user can check logs.

3. **Chat ID**: User needs to message the bot first and get their chat ID. Document this in setup instructions.

4. **Bot token security**: Stored in user config at `~/.slipstream/config.json`. Not committed to repo.

5. **Message format**: Keep simple. Telegram supports markdown but plain text is more reliable across clients.
