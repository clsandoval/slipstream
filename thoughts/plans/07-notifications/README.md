# Branch 7: Notifications

**Branch**: `feature/notifications`
**Scope**: Post-Session Notifications (Telegram)
**Dependencies**: Branch 2 (mcp-server-core), Branch 4 (swim-metrics)
**Complexity**: Low

---

## Description

Send session summaries via Telegram after workout completion.

---

## Components

| Component | Description |
|-----------|-------------|
| Telegram notifier | Bot API integration |
| Session formatter | Summary message formatting |
| Notification manager | Orchestrates sending on session end |

---

## File Structure

```
src/notifications/
├── __init__.py
├── telegram.py            # Telegram bot implementation
├── formatter.py           # Summary message formatting
└── manager.py             # Notification orchestration
```

---

## Key Interfaces

```python
@dataclass
class TelegramConfig:
    bot_token: str
    chat_id: str
    enabled: bool = True

class TelegramNotifier:
    def __init__(self, config: TelegramConfig):
        ...

    async def send(self, message: str) -> bool:
        """Send message to configured chat, return success status."""
        ...

class SessionFormatter:
    def format_summary(self, session: SessionData) -> str:
        """Format session data as Telegram message."""
        ...
```

---

## Message Format

```
🏊 Swim Session Complete

Duration: 32:14
Est. Distance: ~1,200m
Avg Stroke Rate: 53/min

Intervals: 4 × 4min (all completed)
Notes: Stroke rate improved vs yesterday (+2/min)
```

---

## Success Criteria

- [ ] Telegram messages send successfully
- [ ] Summary format is clear and readable
- [ ] Notifications triggered on session end
- [ ] Handles API failures gracefully
- [ ] Configurable enable/disable

---

## Upstream Dependencies

Requires:
- Branch 2: `feature/mcp-server-core` (session data for summary)
- Branch 4: `feature/swim-metrics` (stroke metrics for summary)
