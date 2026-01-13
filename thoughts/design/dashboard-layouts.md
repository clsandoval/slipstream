# Dashboard Layout Options

This document presents multiple dashboard layout options for the Slipstream poolside display. Each option addresses different trade-offs around what information to show and how.

---

## Key Design Questions

1. **Voice/Chat History**: Show it or not? If yes, how much?
2. **Claude Code CLI**: Visible or hidden? Small window or integrated?
3. **Information Density**: Minimal (glanceable) vs. rich (detailed)?
4. **State Awareness**: Same layout always vs. different layouts per state?

---

## OPTION A: Pure Metrics (No Chat/Voice Display)

**Philosophy**: The dashboard is a data display only. Voice is ephemeral - you hear it, it's gone. No visual record of conversation.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                                                                             │
│                            14:32                                            │
│                         SESSION TIME                                        │
│                                                                             │
│                                                                             │
│                     ┌─────────────────────┐                                 │
│                     │                     │                                 │
│                     │    54 /min   ↔      │                                 │
│                     │    STROKE RATE      │                                 │
│                     │                     │                                 │
│                     └─────────────────────┘                                 │
│                                                                             │
│                        INTERVAL 2 of 4                                      │
│                        2:26 remaining                                       │
│                                                                             │
│         ▁▂▃▄▅▆▅▄▃▄▅▆▇▆▅▄▅▆▅▄▃▄▅▆▅▄▃▄▅▆▇▆▅▄▃▂▁▂▃▄▅▆▅▄▃▂                     │
│                      stroke rate (last 2 min)                               │
│                                                                             │
│                        ~480m estimated                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Pros**:
- Maximum readability from water
- Zero distraction
- Largest possible fonts
- Cleanest visual design

**Cons**:
- No visual confirmation of what you said
- No record of coach feedback
- If you miss what the coach said, it's gone

**Best for**: Swimmers who want pure focus, trust the voice interaction

---

## OPTION B: Metrics + Last Coach Message

**Philosophy**: Show just the most recent coach statement. Brief, contextual, then fades.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                            14:32                                            │
│                         SESSION TIME                                        │
│                                                                             │
│                     ┌─────────────────────┐                                 │
│                     │    54 /min   ↔      │                                 │
│                     │    STROKE RATE      │                                 │
│                     └─────────────────────┘                                 │
│                                                                             │
│                        INTERVAL 2 of 4                                      │
│                        2:26 remaining                                       │
│                                                                             │
│         ▁▂▃▄▅▆▅▄▃▄▅▆▇▆▅▄▅▆▅▄▃▄▅▆▅▄▃▄▅▆▇▆▅▄▃▂▁▂▃▄▅▆▅▄▃▂                     │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  COACH: "Good pace! Your stroke rate is more consistent than yesterday."   │
│                                                           (fades after 10s) │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Pros**:
- Visual confirmation of coach feedback
- Can re-read if you missed something
- Minimal screen real estate
- Message fades, doesn't clutter

**Cons**:
- Only shows output, not your input
- Still loses history after fade

**Best for**: Balance between focus and feedback visibility

---

## OPTION C: Metrics + Mini Conversation (Last 2-3 Exchanges)

**Philosophy**: Show a small chat log with recent exchanges. Useful during rest periods.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│              14:32                              INTERVAL 2 of 4             │
│           SESSION TIME                          2:26 remaining              │
│                                                                             │
│                     ┌─────────────────────┐                                 │
│                     │    54 /min   ↔      │      ~480m estimated            │
│                     │    STROKE RATE      │                                 │
│                     └─────────────────────┘                                 │
│                                                                             │
│         ▁▂▃▄▅▆▅▄▃▄▅▆▇▆▅▄▅▆▅▄▃▄▅▆▅▄▃▄▅▆▇▆▅▄▃▂▁▂▃▄▅▆▅▄▃▂                     │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  YOU: "How am I doing compared to yesterday?"                       │   │
│  │  COACH: "You're 2 strokes/min faster and more consistent."         │   │
│  │  YOU: "Great, let's keep this pace"                                 │   │
│  │  COACH: "Got it. I'll let you know if you start to fade."          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Pros**:
- See recent conversation context
- Know what you asked and what was answered
- Helpful during rest periods

**Cons**:
- Takes up screen real estate
- Smaller fonts for metrics
- May be distracting during active swimming
- Text might be too small to read from water

**Best for**: Swimmers who want full conversation context, especially during rest

---

## OPTION D: Adaptive Layout (State-Dependent)

**Philosophy**: Different layouts for different states. Minimize during swimming, expand during rest.

### D1: SWIMMING (Minimal - Maximum Focus)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                                                                             │
│                            14:32                                            │
│                                                                             │
│                                                                             │
│                           54 /min   ↔                                       │
│                                                                             │
│                                                                             │
│                        INTERVAL 2 of 4                                      │
│                                                                             │
│         ▁▂▃▄▅▆▅▄▃▄▅▆▇▆▅▄▅▆▅▄▃▄▅▆▅▄▃▄▅▆▇▆▅▄▃▂▁▂▃▄▅▆▅▄▃▂                     │
│                                                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### D2: REST (Expanded - More Detail)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│         14:32                                              REST 0:45        │
│      SESSION TIME                                         remaining         │
│                                                                             │
├────────────────────────────────────┬────────────────────────────────────────┤
│                                    │                                        │
│       LAST INTERVAL                │       NEXT UP                          │
│       Avg: 52 /min                 │       INTERVAL 2 of 4                  │
│       Est: ~120m                   │       4:00 duration                    │
│       Strokes: 80                  │                                        │
│                                    │                                        │
├────────────────────────────────────┴────────────────────────────────────────┤
│                                                                             │
│  ▁▂▃▄▅▆▅▄▃▄▅▆▇▆▅▄▅▆▅▄▃▄▅▆▇▆▅▄▃▂▁▂▃▄▅▆▅▄▃▂ (session so far)                │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  COACH: "Solid interval! You held 52 consistently. Ready for the next?"    │
│                                                                             │
│  [Listening...]                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Pros**:
- Best of both worlds
- Maximum focus when swimming
- Rich detail when resting
- Coach message visible when it matters (during rest)

**Cons**:
- More complex to implement
- Layout transitions might be jarring
- Need to handle edge cases (what if they talk while swimming?)

**Best for**: The optimal UX - show what matters when it matters

---

## OPTION E: Split View with Claude Code CLI

**Philosophy**: Dedicate a portion of the screen to show Claude Code CLI activity. Debug-friendly.

### E1: Side Panel CLI
```
┌─────────────────────────────────────────────────┬───────────────────────────┐
│                                                 │                           │
│                    14:32                        │   CLAUDE CODE CLI         │
│                 SESSION TIME                    │   ─────────────────       │
│                                                 │                           │
│              ┌─────────────────┐                │   > get_stroke_rate()     │
│              │  54 /min   ↔    │                │   { rate: 54,             │
│              │  STROKE RATE    │                │     trend: "stable" }     │
│              └─────────────────┘                │                           │
│                                                 │   > get_session_time()    │
│                 INTERVAL 2 of 4                 │   { elapsed: "14:32" }    │
│                 2:26 remaining                  │                           │
│                                                 │   [Listening...]          │
│  ▁▂▃▄▅▆▅▄▃▄▅▆▇▆▅▄▅▆▅▄▃▄▅▆▅▄▃▄▅▆▅▄▃▂            │                           │
│                                                 │                           │
│                  ~480m estimated                │                           │
│                                                 │                           │
└─────────────────────────────────────────────────┴───────────────────────────┘
```

### E2: Bottom Bar CLI (Minimal)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                            14:32                                            │
│                         SESSION TIME                                        │
│                                                                             │
│                     ┌─────────────────────┐                                 │
│                     │    54 /min   ↔      │                                 │
│                     │    STROKE RATE      │                                 │
│                     └─────────────────────┘                                 │
│                                                                             │
│                        INTERVAL 2 of 4    |    ~480m estimated              │
│                                                                             │
│         ▁▂▃▄▅▆▅▄▃▄▅▆▇▆▅▄▅▆▅▄▃▄▅▆▅▄▃▄▅▆▇▆▅▄▃▂▁▂▃▄▅▆▅▄▃▂                     │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  CLI: get_stroke_rate() → 54/min stable | [Listening...]          2:26 left│
└─────────────────────────────────────────────────────────────────────────────┘
```

**Pros**:
- See exactly what Claude is doing
- Great for debugging and development
- Transparency into MCP tool calls
- Useful during testing phase

**Cons**:
- Clutters the interface
- Too technical for actual swimming use
- Distracting
- Takes screen real estate

**Best for**: Development/debugging mode only - NOT for actual swimming

---

## OPTION F: Voice Activity Indicator (No History)

**Philosophy**: Don't show chat history, but show voice activity status. Know when you're being heard.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                            14:32                                            │
│                         SESSION TIME                                        │
│                                                                             │
│                     ┌─────────────────────┐                                 │
│                     │    54 /min   ↔      │                                 │
│                     │    STROKE RATE      │                                 │
│                     └─────────────────────┘                                 │
│                                                                             │
│                        INTERVAL 2 of 4                                      │
│                        2:26 remaining                                       │
│                                                                             │
│         ▁▂▃▄▅▆▅▄▃▄▅▆▇▆▅▄▅▆▅▄▃▄▅▆▅▄▃▄▅▆▇▆▅▄▃▂▁▂▃▄▅▆▅▄▃▂                     │
│                                                                             │
│                          ~480m estimated                                    │
│                                                                             │
│                                                                             │
│                       ◉ Listening        ← small indicator, bottom center   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**States**:
- `◉ Listening` - Ready for voice input
- `◉ Hearing...` - Actively detecting speech
- `◉ Thinking...` - Claude processing
- `◉ Speaking...` - Coach is talking

**Pros**:
- Know the system is active
- Visual feedback that you're being heard
- Minimal screen usage
- Clean design

**Cons**:
- No content visibility
- Doesn't show what was said or heard

**Best for**: Clean design with just enough feedback to know voice is working

---

## OPTION G: Overlay Mode (Metrics Over Video)

**Philosophy**: Show the camera feed with metrics overlaid. See yourself swim.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  14:32                                                     INTERVAL 2/4    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                                                                      │  │
│  │                                                                      │  │
│  │                      [LIVE VIDEO FEED]                               │  │
│  │                    (you swimming, overhead view)                     │  │
│  │                                                                      │  │
│  │                                                                      │  │
│  │                                                                      │  │
│  │                                                                      │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│         54 /min ↔         │  2:26 left  │  ~480m   │  ◉ Listening          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Pros**:
- See your own form in real-time
- Pose keypoints could be overlaid (skeleton visualization)
- Very engaging, "smart mirror" feel
- Coach could reference what they see

**Cons**:
- Processing overhead to render video
- May be distracting
- Harder to read metrics over video
- TV refresh rate considerations

**Best for**: Advanced feature for form feedback (Phase 3+)

---

## OPTION H: The "Focus Zones" Layout

**Philosophy**: Divide screen into distinct zones with clear hierarchy. Primary zone is HUGE.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                         │ │
│ │                              54                                         │ │
│ │                            /min  ↔                                      │ │
│ │                                                                         │ │
│ │                        PRIMARY ZONE                                     │ │
│ │                    (current stroke rate)                                │ │
│ │                                                                         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────┐ │
│ │                   │  │                   │  │                           │ │
│ │      14:32        │  │   INTERVAL 2/4    │  │  ▁▂▃▄▅▆▅▄▃▄▅▆▇▆▅▄▃▂      │ │
│ │    SESSION TIME   │  │    2:26 left      │  │    (mini graph)           │ │
│ │                   │  │                   │  │                           │ │
│ └───────────────────┘  └───────────────────┘  └───────────────────────────┘ │
│                                                                             │
│                              ~480m estimated                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Pros**:
- Clear visual hierarchy
- Most important metric (stroke rate) is massive
- Secondary info available but not distracting
- Great for glancing from water

**Cons**:
- Less info in primary view
- Session time is secondary (maybe that should be bigger?)

**Best for**: When stroke rate is THE metric that matters most in real-time

---

## RECOMMENDATION MATRIX

| Option | Focus | Voice Visibility | Complexity | Best Phase |
|--------|-------|------------------|------------|------------|
| A: Pure Metrics | ★★★★★ | None | Low | Production |
| B: + Last Message | ★★★★ | Low (fading) | Low | Production |
| C: + Mini Convo | ★★★ | Medium | Medium | Production |
| D: Adaptive | ★★★★★ | Context-aware | High | Production |
| E: CLI Panel | ★★ | High (technical) | Medium | Dev/Debug |
| F: Voice Indicator | ★★★★★ | Minimal | Low | Production |
| G: Video Overlay | ★★★ | Optional | High | Phase 3+ |
| H: Focus Zones | ★★★★ | None | Low | Production |

---

## MY RECOMMENDATION

### For Phase 1 MVP: Option D (Adaptive) + Option F (Voice Indicator)

Combine the best of both:

1. **During SWIMMING**: Minimal layout (like D1) with voice indicator
   - Giant stroke rate, session time, interval info
   - Small "◉ Listening" indicator
   - No chat history, no distractions

2. **During REST**: Expanded layout (like D2) with last coach message
   - Show interval summary
   - Show coach feedback
   - Show upcoming interval
   - "◉ Listening..." more prominent

3. **POST-SESSION**: Full summary with session graph
   - All the stats
   - Full session stroke rate graph
   - Optional: conversation summary

### Why NOT show Claude Code CLI?

The CLI is an implementation detail. The user cares about:
- Their metrics
- Coach feedback
- What's next

They don't care about:
- MCP tool calls
- JSON responses
- System internals

**Exception**: A "developer mode" toggle could show CLI for debugging, but this should be OFF by default for actual swimming.

### Why NOT show full conversation history?

- You're swimming, not reading
- Voice is ephemeral by nature
- If you want to review conversation, do it after session
- Text is hard to read from water
- It clutters the interface

**Exception**: During REST, showing the last 1-2 exchanges can be helpful for context.

---

## STATE TRANSITION DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ┌──────────┐         motion          ┌──────────┐                         │
│   │ SLEEPING │ ─────────────────────▶  │ STANDBY  │                         │
│   │  (OFF)   │                         │ (READY)  │                         │
│   └──────────┘                         └──────────┘                         │
│        ▲                                    │                               │
│        │                                    │ "start" or                    │
│        │                                    │ swimming detected             │
│        │ 5min                               ▼                               │
│        │ timeout                       ┌──────────┐                         │
│        │                               │ SESSION  │◀────────┐               │
│        │                               └──────────┘         │               │
│        │                                    │               │               │
│        │                     swimming       │               │ swimming      │
│        │                     detected       │               │ resumes       │
│        │                         ┌──────────┴──────────┐    │               │
│        │                         ▼                     ▼    │               │
│        │                   ┌──────────┐          ┌──────────┐               │
│        │                   │ SWIMMING │          │  RESTING │───────────────┘│
│        │                   │ (ACTIVE) │ ◀──────▶ │  (REST)  │               │
│        │                   └──────────┘  motion  └──────────┘               │
│        │                                 stops        │                     │
│        │                                              │ "end" or            │
│        │                                              │ workout complete    │
│        │                                              ▼                     │
│        │                                        ┌──────────┐                │
│        └─────────────────────────────────────── │ SUMMARY  │                │
│                          (after 2 min)          └──────────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## DASHBOARD VIEW PER STATE

| State | View | Primary Info | Voice Display |
|-------|------|--------------|---------------|
| SLEEPING | OFF/Ambient | Clock only | None |
| STANDBY | Welcome | "Ready to swim" | "◉ Listening" |
| SWIMMING | Minimal | Rate, Time, Interval | "◉ Listening" (small) |
| RESTING | Expanded | Summary, Next Up, Coach | Last message + "◉ Listening" |
| SUMMARY | Full | All stats, Graph | None |

---

## NEXT STEPS

1. Pick a primary option (I recommend D+F hybrid)
2. Create wireframes/mockups
3. Build static HTML/CSS prototype
4. Test readability from 10ft distance
5. Iterate based on actual pool testing
