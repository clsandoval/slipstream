# Slipstream User Journey

**Version**: 0.1.1
**Status**: High-Level Design Complete

---

## User Profile

| Attribute | Value |
|-----------|-------|
| **Users** | Single user (solo) |
| **Goal** | General fitness + stroke improvement |
| **Frequency** | Daily |
| **Swim Style** | Mix of continuous swimming and intervals |

---

## System States

The system operates in three distinct states:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SYSTEM STATES                                  │
│                                                                          │
│   ┌──────────┐         ┌──────────┐         ┌──────────┐               │
│   │ SLEEPING │ ──────► │ STANDBY  │ ──────► │ SESSION  │               │
│   │          │ motion  │          │ "start" │          │               │
│   │ 1 FPS    │ detect  │ active   │ or auto │ swimming │               │
│   └──────────┘         └──────────┘         └──────────┘               │
│        ▲                    │                    │                       │
│        │                    │ timeout            │ "end" or             │
│        │                    │ (no activity)      │ timeout              │
│        │                    ▼                    │                       │
│        └────────────────────┴────────────────────┘                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

| State | Description | Power/Processing |
|-------|-------------|------------------|
| **Sleeping** | Polling mode. Captures 1 frame/minute, checks for presence/motion | Minimal |
| **Standby** | Person detected. Full vision active. Listening. Ready to plan or start | Medium |
| **Session** | Active swim session. Full tracking, coaching, dashboard live | Full |

---

## Complete User Journey

### Phase 1: Wake Up (Sleeping → Standby)

**Trigger**: System detects motion/presence in pool area

```
┌─────────────────────────────────────────────────────────────────────────┐
│ SLEEPING STATE                                                          │
│                                                                          │
│  • System captures 1 frame every 60 seconds                             │
│  • Runs lightweight person/motion detection                              │
│  • Dashboard: OFF or showing ambient clock                              │
│  • Audio: Not listening                                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ Motion/person detected in frame
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ TRANSITION TO STANDBY                                                    │
│                                                                          │
│  • Dashboard wakes up: "Good morning" or ambient welcome                │
│  • Audio: Begin listening for voice                                     │
│  • Vision: Spin up full pose estimation pipeline                        │
│  • System ready for conversation                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

**User experience**: Walk into pool room → TV turns on, system is ready to talk.

---

### Phase 2: Pre-Swim Planning (Standby)

**Location**: User is poolside, not yet in water

**Interaction**: Voice (user) ↔ Voice + Display (system)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PLANNING CONVERSATION (Optional)                                         │
│                                                                          │
│  User: "Hey, let's make a plan for today's workout"                     │
│                                                                          │
│  Coach: "Sure! How are you feeling today? And how much time do          │
│          you have?"                                                      │
│                                                                          │
│  User: "Feeling good, I have about 30 minutes"                          │
│                                                                          │
│  Coach: "How about this:                                                │
│          - 5 min warmup, easy pace                                      │
│          - 4 x 4 min intervals with 1 min rest                          │
│          - 5 min cooldown                                               │
│          Sound good?"                                                    │
│                                                                          │
│  User: "Yeah let's do it"                                               │
│                                                                          │
│  Coach: "Got it. I'll track your intervals. Just say 'start'            │
│          when you're in the water and ready."                           │
│                                                                          │
│  [Dashboard shows workout plan summary]                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

**Alternative flows**:
- Skip planning: Just get in and say "start session" for unstructured swim
- Reference past session: "Let's do what I did Tuesday" (Claude reads past session files)
- Quick start: "Start a 20-minute easy swim"

---

### Phase 3: Session Start (Standby → Session)

**Trigger options**:
1. Voice command: "Start" / "Start session" / "Go"
2. Auto-detect: System sees user in water + swimming motion begins

```
┌─────────────────────────────────────────────────────────────────────────┐
│ SESSION START                                                            │
│                                                                          │
│  User gets in pool                                                       │
│                                                                          │
│  User: "Start"                                                          │
│  --or--                                                                  │
│  [System detects swimming motion]                                        │
│                                                                          │
│  Coach: "Session started. Let's go!"                                    │
│                                                                          │
│  Dashboard transitions to SESSION VIEW:                                  │
│  ┌─────────────────────────────────────────┐                            │
│  │         00:00        WARMUP             │                            │
│  │                                          │                            │
│  │      STROKE RATE: --                     │                            │
│  │                                          │                            │
│  │  [Plan progress bar if applicable]       │                            │
│  └─────────────────────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Phase 4: During Session - Swimming

**State**: User is actively swimming

**Interaction**:
- Input: Voice (poolside mic picks up between breaths or during rest)
- Output: Dashboard (primary) + Voice (secondary, during rest only)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ACTIVE SWIMMING                                                          │
│                                                                          │
│  Dashboard (always visible):                                             │
│  ┌─────────────────────────────────────────┐                            │
│  │         12:34        INTERVAL 2/4       │                            │
│  │                                          │                            │
│  │      STROKE RATE: 54/min  ↔              │                            │
│  │                                          │                            │
│  │      TIME LEFT: 2:26                     │                            │
│  │      EST DISTANCE: ~400m                 │                            │
│  │                                          │                            │
│  │  ▁▂▃▄▅▄▄▅▆▅▄▃▄▅▄▃▄▅▆▅▄                  │                            │
│  └─────────────────────────────────────────┘                            │
│                                                                          │
│  System is:                                                              │
│  • Tracking stroke rate continuously                                     │
│  • Detecting swim vs rest state                                         │
│  • Accumulating session stats                                           │
│  • Listening for voice commands                                          │
│  • NOT interrupting while actively swimming                              │
└─────────────────────────────────────────────────────────────────────────┘
```

**Metrics displayed** (Phase 1+):
- Session time (total elapsed)
- Current interval + progress (if planned workout)
- Time remaining in interval
- Stroke rate (current, with trend indicator)
- Estimated distance (stroke count × user-configured distance-per-stroke ratio)

---

### Phase 5: During Session - Rest Intervals

**State**: User has stopped swimming (detected via pose estimation)

**Interaction**: Voice becomes bidirectional

```
┌─────────────────────────────────────────────────────────────────────────┐
│ REST INTERVAL                                                            │
│                                                                          │
│  [System detects swimming stopped]                                       │
│                                                                          │
│  Dashboard updates:                                                      │
│  ┌─────────────────────────────────────────┐                            │
│  │         14:00        REST 1:00          │                            │
│  │                                          │                            │
│  │      LAST INTERVAL:                      │                            │
│  │      Avg stroke rate: 52/min             │                            │
│  │      Est distance: ~100m                 │                            │
│  │                                          │
│  │      REST REMAINING: 0:45                │                            │
│  └─────────────────────────────────────────┘                            │
│                                                                          │
│  Proactive coaching (optional):                                          │
│  Coach: "Good interval! Your stroke rate was steady at 52.              │
│          45 seconds rest remaining."                                     │
│                                                                          │
│  User can ask questions:                                                 │
│  User: "How am I doing compared to last time?"                          │
│  Coach: "You're 2 strokes per minute faster than yesterday.             │
│          Feeling strong!"                                                │
│                                                                          │
│  Auto-resume detection:                                                  │
│  [System sees user start swimming again → next interval begins]          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Proactive coach behaviors** (during rest only):
- Interval summary ("that was a strong interval")
- Technique cues ("try to keep your stroke rate more consistent")
- Encouragement ("halfway done, keep it up")
- Rest countdown ("10 seconds")

**Voice queries user might ask**:
- "What's my stroke rate?"
- "How much time left?"
- "How many intervals left?"
- "How am I doing?"
- "Skip the rest" / "Start next interval"
- "Add another interval"
- "Let's wrap up after this one"

---

### Phase 6: Session End (Session → Standby)

**Trigger options**:
1. Voice: "End session" / "Stop" / "Done"
2. Planned workout complete + user confirms
3. Timeout: Extended inactivity (e.g., 5+ minutes no swimming)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ SESSION END                                                              │
│                                                                          │
│  User: "End session"                                                    │
│  --or--                                                                  │
│  Coach: "That's the last interval! Nice work. End session?"             │
│  User: "Yeah, done"                                                     │
│                                                                          │
│  Coach: "Great session! 32 minutes, 1,200 meters estimated.             │
│          Average stroke rate 53. I'll send you the summary."            │
│                                                                          │
│  Dashboard shows SESSION SUMMARY:                                        │
│  ┌─────────────────────────────────────────┐                            │
│  │         SESSION COMPLETE                 │                            │
│  │                                          │                            │
│  │      Duration: 32:14                     │                            │
│  │      Est Distance: ~1,200m               │                            │
│  │      Avg Stroke Rate: 53/min             │                            │
│  │      Intervals: 4 completed              │                            │
│  │                                          │                            │
│  │  ▁▂▃▄▅▄▄▅▆▅▄▃▄▅▄▃▄▅▆▅▄                  │                            │
│  │  (stroke rate over session)              │                            │
│  └─────────────────────────────────────────┘                            │
│                                                                          │
│  [Summary displayed for ~2 minutes or until user leaves]                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Phase 7: Post-Session (Standby → Sleeping)

**User experience**: Walk away, receive summary later

```
┌─────────────────────────────────────────────────────────────────────────┐
│ POST-SESSION                                                             │
│                                                                          │
│  Immediate:                                                              │
│  • Dashboard shows summary for ~2 min                                   │
│  • Session data saved locally                                           │
│                                                                          │
│  Async (background):                                                     │
│  • System sends text/notification with workout summary                  │
│  • Data synced to wherever (phone app? web dashboard? TBD)              │
│                                                                          │
│  After ~5 min no presence detected:                                      │
│  • System returns to SLEEPING state                                     │
│  • Dashboard turns off or shows ambient display                         │
│  • Vision returns to 1 frame/minute polling                             │
└─────────────────────────────────────────────────────────────────────────┘
```

**Text summary example**:
```
🏊 Swim Session Complete

Duration: 32:14
Est. Distance: ~1,200m
Avg Stroke Rate: 53/min

Intervals: 4 × 4min (all completed)
Notes: Stroke rate improved vs yesterday (+2/min)

[Link to full details]
```

---

## Key Interaction Principles

### Voice Design

| Principle | Description |
|-----------|-------------|
| **Don't interrupt swimming** | Coach only speaks during rest or when asked |
| **Brief responses** | Keep voice output short; user is exercising |
| **Dashboard is primary** | Voice confirms, dashboard shows detail |
| **Always listening** | No wake word needed (single user, private space) |

### Dashboard Design

| Principle | Description |
|-----------|-------------|
| **Glanceable** | Large text, readable from water with wet eyes |
| **Dark theme** | Reduce glare on wet surfaces |
| **State-aware** | Shows different info for swimming vs rest vs summary |
| **Auto-updating** | No user action needed; reflects current state |

### State Detection

| Detection | Method |
|-----------|--------|
| **Presence** | Person detected in frame (wake from sleep) |
| **Swimming** | Active arm motion detected via pose estimation |
| **Resting** | Person in water but no swimming motion |
| **Gone** | No person detected for extended period |

---

## Resolved Design Decisions

| Decision | Resolution |
|----------|------------|
| **Distance estimation** | User sets a **strokes-to-distance ratio** (e.g., 1 stroke = 1.5m). Distance = stroke count × ratio. User calibrates once, adjusts as needed. |
| **Text delivery** | SMS or Telegram. User configures their preferred method. |
| **Voice output** | Poolside speaker (not headset). Headset is input-only. |
| **Wake sensitivity** | 1 frame/minute confirmed sufficient. |

---

## Data & Storage Philosophy

**Principle: Agentic, not structured.**

| Aspect | Approach |
|--------|----------|
| **Session data** | Saved as local files (JSON, text, whatever makes sense) |
| **Workout plans** | No formal "saved workouts" feature. Claude Code CLI reads past session files and can reference/recreate them on request. |
| **Historical queries** | Claude Code CLI queries local filesystem. No database, no tables. |
| **Configuration** | Simple local config file (strokes-to-distance ratio, notification preferences, etc.) |

**Why this approach**:
- Claude Code CLI is inherently good at reading files and understanding context
- No need to build rigid data schemas when the AI can interpret freeform data
- Simplifies implementation; data format can evolve naturally
- User can say "do what I did last Tuesday" and Claude figures it out

**Example data flow**:
```
sessions/
  2026-01-11_morning.json    # Raw session data
  2026-01-10_evening.json
  2026-01-09_morning.json
  ...

User: "How does today compare to last week?"
Claude: [reads recent files, computes comparison, responds]

User: "Let's do that pyramid workout from last month"
Claude: [searches sessions for pyramid pattern, recreates plan]
```

---

## Open Questions (Remaining)

| Item | Notes |
|------|-------|
| **Auto-rest detection accuracy** | Can pose estimation reliably distinguish swimming vs standing? Needs testing. |
| **Speaker placement** | Where exactly? Volume levels for pool acoustics? |
| **Telegram/SMS setup** | Which service to use, API keys, phone number config |

---

## Phase 1 Scope (MVP User Journey)

For Phase 1, simplify to:

| Feature | Phase 1 | Later |
|---------|---------|-------|
| Session start | Voice command "start" | Auto-detect |
| Workout planning | No (unstructured swim) | Yes |
| During swim | Stroke rate on dashboard | + intervals, distance, cues |
| Rest detection | Manual ("rest" / "go") | Auto-detect |
| Session end | Voice command "end" | + auto-detect |
| Post-session | Summary on dashboard | + text notification |
| Sleep/wake | Always on standby | Polling sleep mode |

This lets us validate the core loop before adding intelligence.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-01-11 | Initial user journey draft |
| 0.1.1 | 2026-01-11 | Resolved design decisions: distance-per-stroke ratio, SMS/Telegram, poolside speaker, agentic data storage philosophy |
