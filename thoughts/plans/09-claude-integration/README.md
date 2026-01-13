# Branch 9: Claude Integration

**Branch**: `feature/claude-integration`
**Scope**: Claude Code CLI Configuration
**Dependencies**: All other branches (final integration)
**Complexity**: Low

---

## Description

Final integration connecting Claude Code CLI to the MCP server, including TTS output and agent behavior configuration.

---

## Components

| Component | Description |
|-----------|-------------|
| MCP configuration | `.mcp.json` with swim-coach server |
| Environment setup | VIDEO_SOURCE, paths |
| TTS integration | ElevenLabs/OpenAI for voice output |
| Agent behavior | Polling loop, coaching patterns |
| System prompt | Claude's swim coach persona |

---

## File Structure

```
.mcp.json                      # MCP server configuration
src/tts/
├── __init__.py
├── tts_service.py             # Text-to-speech wrapper
├── elevenlabs.py              # ElevenLabs implementation
├── openai_tts.py              # OpenAI TTS implementation
└── speaker.py                 # Audio playback control
docs/
├── agent_behavior.md          # How Claude uses the tools
├── coaching_patterns.md       # Example coaching dialogues
└── system_prompt.md           # Claude's persona
```

---

## MCP Configuration

```json
{
  "mcpServers": {
    "swim-coach": {
      "command": "python",
      "args": ["-m", "swim_coach_mcp"],
      "env": {
        "VIDEO_SOURCE": "rtsp://192.168.1.100/stream",
        "SLIPSTREAM_HOME": "/home/swim/.slipstream"
      }
    }
  }
}
```

---

## Agent Behavior

Claude operates in a polling loop:

```
1. Call get_voice_input(timeout=10)
2. If has_input:
   - Process user message
   - Call relevant swim tools
   - Respond via TTS (during rest only)
3. If !has_input and session active:
   - Check get_status() for state changes
   - Proactive coaching during rest
4. Loop
```

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

---

## Success Criteria

- [ ] Claude Code CLI connects to MCP server
- [ ] Voice input loop works correctly
- [ ] TTS plays through poolside speaker
- [ ] Agent provides helpful coaching
- [ ] Respects "don't interrupt swimming" rule

---

## Upstream Dependencies

Requires all other branches:
- Branch 1: `feature/vision-pipeline`
- Branch 2: `feature/mcp-server-core`
- Branch 3: `feature/stt-service`
- Branch 4: `feature/swim-metrics`
- Branch 5: `feature/workout-system`
- Branch 6: `feature/dashboard`
- Branch 7: `feature/notifications`
- Branch 8: `feature/verification`

This is the final integration branch.
