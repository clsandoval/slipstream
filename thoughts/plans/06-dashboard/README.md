# Branch 6: Dashboard

**Branch**: `feature/dashboard`
**Scope**: React Dashboard Application
**Dependencies**: Branch 2 (mcp-server-core) - can start early with mocks
**Complexity**: Medium

---

## Description

The poolside display showing real-time metrics, workout progress, and voice status with adaptive layouts for different system states.

---

## Components

| Component | Description |
|-----------|-------------|
| React app | Create React App with TypeScript, dark theme |
| WebSocket client | Connect to MCP server, handle reconnection |
| State displays | SLEEPING, STANDBY, SESSION, SUMMARY views |
| Adaptive layouts | Minimal when swimming, rich when resting |
| Stroke rate display | Giant numbers + trend arrow |
| Rate graph | Sparkline visualization (last 2 min) |
| Workout display | Interval progress, segment info, rest timer |
| Voice indicator | Status dot with state labels |
| Coach message | Fading message display during rest |

---

## File Structure

```
dashboard/
├── package.json
├── tsconfig.json
├── public/
│   └── index.html
├── src/
│   ├── index.tsx
│   ├── App.tsx
│   ├── types/
│   │   └── state.ts           # TypeScript interfaces
│   ├── hooks/
│   │   ├── useWebSocket.ts    # WebSocket connection
│   │   └── useSystemState.ts  # State management
│   ├── components/
│   │   ├── StrokeRate.tsx     # Giant rate display
│   │   ├── SessionTimer.tsx   # Elapsed time
│   │   ├── RateGraph.tsx      # Sparkline chart
│   │   ├── IntervalProgress.tsx
│   │   ├── VoiceIndicator.tsx
│   │   ├── CoachMessage.tsx
│   │   └── DistanceEstimate.tsx
│   ├── layouts/
│   │   ├── SleepingLayout.tsx
│   │   ├── StandbyLayout.tsx
│   │   ├── SwimmingLayout.tsx   # Minimal, giant metrics
│   │   ├── RestingLayout.tsx    # Expanded, rich info
│   │   └── SummaryLayout.tsx    # Post-session stats
│   └── styles/
│       ├── theme.css          # Dark theme, large fonts
│       └── animations.css     # Transitions, fades
```

---

## Layout States

| State | Layout | Primary Elements |
|-------|--------|------------------|
| SLEEPING | Off/Ambient | Clock only |
| STANDBY | Welcome | "Ready to swim", listening indicator |
| SWIMMING | Minimal | Giant stroke rate, time, interval |
| RESTING | Expanded | Last interval summary, next up, coach message |
| SUMMARY | Full | All stats, session graph |

---

## SWIMMING Layout (Minimal)

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
│         ▁▂▃▄▅▆▅▄▃▄▅▆▇▆▅▄▅▆▅▄▃▄▅▆▇▆▅▄▃▂▁▂▃▄▅▆▅▄▃▂                     │
│                                                                             │
│                                                     ◉ Listening             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## RESTING Layout (Expanded)

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
│  ◉ Listening...                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Success Criteria

- [ ] Dashboard connects to WebSocket and displays state
- [ ] Layout transitions smoothly between states
- [ ] Text readable from 10ft distance (pool)
- [ ] Dark theme reduces glare
- [ ] Voice indicator shows correct status
- [ ] Works with mock data for early development

---

## Upstream Dependencies

Requires:
- Branch 2: `feature/mcp-server-core` (WebSocket protocol)

Can start early with mock data before mcp-server-core is complete.
