# Branch 7: Notifications

**Branch**: `feature/notifications`
**Scope**: Post-Session Notifications
**Dependencies**: Branch 2 (mcp-server-core)
**Complexity**: Low

---

## Description

Send session summaries via SMS or Telegram after workout completion.

---

## Components

| Component | Description |
|-----------|-------------|
| Notification service | Abstract base + implementations |
| Telegram integration | Bot API, message formatting |
| SMS integration | Twilio or similar provider |
| Session summary format | Markdown template |
| Integration | Trigger on `end_session` |

---

## File Structure

```
src/notifications/
├── __init__.py
├── base.py                # Abstract NotificationService
├── telegram.py            # Telegram bot implementation
├── sms.py                 # SMS via Twilio
├── formatter.py           # Summary message formatting
└── config.py              # API keys, preferences
```

---

## Key Interfaces

```python
class NotificationService(ABC):
    @abstractmethod
    async def send(self, recipient: str, message: str) -> bool:
        """Send notification, return success status."""
        ...

class TelegramNotifier(NotificationService):
    def __init__(self, bot_token: str):
        ...

class SMSNotifier(NotificationService):
    def __init__(self, twilio_sid: str, twilio_token: str, from_number: str):
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
- [ ] SMS messages send successfully
- [ ] Summary format is clear and readable
- [ ] Notifications triggered on session end
- [ ] Handles API failures gracefully

---

## Upstream Dependencies

Requires:
- Branch 2: `feature/mcp-server-core` (session data for summary)
