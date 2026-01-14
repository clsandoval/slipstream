# Branch 9: Claude Integration

**Branch**: `feature/claude-integration`
**Scope**: Python Agent with Claude SDK
**Dependencies**: All other branches (final integration)
**Complexity**: Medium

---

## Description

Final integration using the Claude Agent SDK to create a Python-based swim coach agent. The agent monitors the transcript log for new voice input, queries Claude with MCP tools for swim data, and speaks responses via TTS.

---

## Components

| Component | Description |
|-----------|-------------|
| Python agent | Infinite loop monitoring transcript.log |
| Claude SDK client | Maintains conversation context across exchanges |
| MCP connection | SDK connects to swim-coach MCP server |
| TTS integration | ElevenLabs/OpenAI for voice output |
| System prompt | Claude's swim coach persona |

---

## File Structure

```
src/agent/
├── __init__.py
├── agent.py               # Main infinite loop + Claude SDK client
├── transcript_watcher.py  # Monitors transcript.log for new content
└── config.py              # Agent configuration

src/tts/
├── __init__.py
├── tts_service.py         # Text-to-speech wrapper
├── elevenlabs.py          # ElevenLabs implementation
├── openai_tts.py          # OpenAI TTS implementation
└── speaker.py             # Audio playback control

docs/
├── agent_behavior.md      # How Claude uses the tools
├── coaching_patterns.md   # Example coaching dialogues
└── system_prompt.md       # Claude's persona
```

---

## Architecture

### Transcript-Based Input

The STT service (Branch 3) continuously writes transcriptions to `~/.slipstream/transcript.log`. When the user presses the button, it writes a `<<<COMMIT>>>` marker indicating the message is complete.

```
# Example transcript.log content
[2024-01-15 10:23:45] What's my stroke rate?
<<<COMMIT>>>
[2024-01-15 10:24:12] How am I doing compared to yesterday?
<<<COMMIT>>>
```

### Agent Loop

```python
# src/agent/agent.py
async def main():
    last_position = 0

    options = ClaudeAgentOptions(
        model="claude-sonnet-4-20250514",
        system_prompt=SWIM_COACH_PROMPT,
        mcp_servers={
            "swim-coach": {
                "command": "uv",
                "args": ["run", "python", "-m", "src.mcp.server"]
            }
        },
        allowed_tools=[
            "mcp__swim-coach__get_status",
            "mcp__swim-coach__get_stroke_rate",
            "mcp__swim-coach__get_stroke_count",
            "mcp__swim-coach__start_session",
            "mcp__swim-coach__end_session",
            "mcp__swim-coach__start_workout",
            "mcp__swim-coach__skip_segment",
        ]
    )

    async with ClaudeSDKClient(options) as client:
        while True:
            # Check transcript.log for new committed content
            new_messages = read_new_lines(TRANSCRIPT_LOG, last_position)

            if new_messages:
                await client.query(new_messages)
                async for message in client.receive_response():
                    # Speak response via TTS
                    await speak(message)
                last_position = get_current_position()
            else:
                await asyncio.sleep(2)  # Sleep if nothing new
```

---

## Key Design Decisions

### No Turn Detection Needed

The STT service writes continuously to transcript.log. The `<<<COMMIT>>>` marker from the button press tells the agent when a message is complete. No inference needed.

### Persistent Conversation Context

The `ClaudeSDKClient` maintains conversation context across multiple exchanges. The agent remembers previous questions and can reference earlier swim data.

### Simple Mental Model

- Transcript log = "inbox"
- Agent checks periodically
- Button press = "send message"
- Agent responds via TTS

---

## Coaching Patterns

### During Rest (Proactive)

- Summarize last interval
- Provide encouragement
- Preview next segment
- Keep responses brief (<15 seconds)

### User Queries

- "What's my stroke rate?" → get_stroke_rate, brief response
- "How am I doing?" → comparison to previous sessions
- "Skip this interval" → skip_segment, confirm

### Don't Interrupt Swimming

- Only speak during rest periods
- Dashboard is primary feedback during active swimming
- Agent checks session state before speaking

---

## TTS Integration

```python
# src/tts/tts_service.py
class TTSService:
    def __init__(self, provider: str = "elevenlabs"):
        self.provider = self._init_provider(provider)

    async def speak(self, text: str) -> None:
        audio = await self.provider.synthesize(text)
        await self.speaker.play(audio)
```

Providers:
- **ElevenLabs**: Higher quality, requires API key
- **OpenAI TTS**: Good fallback, requires API key

---

## Configuration

```python
# src/agent/config.py
@dataclass
class AgentConfig:
    transcript_log: Path = Path.home() / ".slipstream" / "transcript.log"
    poll_interval: float = 2.0  # seconds
    tts_provider: str = "elevenlabs"
    model: str = "claude-sonnet-4-20250514"
```

Environment variables:
```bash
ANTHROPIC_API_KEY=...
ELEVENLABS_API_KEY=...
OPENAI_API_KEY=...  # fallback TTS
```

---

## Success Criteria

- [ ] Python agent runs as persistent process
- [ ] Agent detects new transcript content after <<<COMMIT>>>
- [ ] Claude SDK connects to MCP swim-coach server
- [ ] Agent queries swim tools correctly
- [ ] TTS plays through poolside speaker
- [ ] Conversation context persists across exchanges
- [ ] Agent provides helpful coaching
- [ ] Respects "don't interrupt swimming" rule

---

## Upstream Dependencies

Requires all other branches:
- Branch 1: `feature/vision-pipeline`
- Branch 2: `feature/mcp-server-core`
- Branch 3: `feature/stt-service` (provides transcript.log + <<<COMMIT>>> markers)
- Branch 4: `feature/swim-metrics`
- Branch 5: `feature/workout-system`
- Branch 6: `feature/dashboard`
- Branch 7: `feature/notifications`
- Branch 8: `feature/verification`

This is the final integration branch.
