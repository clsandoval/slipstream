# Dashboard - TDD Implementation Plan

## Overview

Test-Driven Development plan for Branch 6: Dashboard. React poolside display with real-time metrics, adaptive layouts, and voice status indicators.

**Dependencies**: Branch 2 (mcp-server-core) - can start early with mocks
**Complexity**: Medium

---

## Architecture

The dashboard is a React TypeScript application that connects to the MCP server via WebSocket and renders different layouts based on system state.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DASHBOARD ARCHITECTURE                               │
│                                                                              │
│  MCP Server                           React Dashboard                        │
│  ┌──────────────────┐                ┌──────────────────────────────────────┐│
│  │ WebSocket Server │────────────────│ useWebSocket()                       ││
│  │ Port 8765        │  StateUpdate   │   └─ Connects, reconnects, parses    ││
│  │                  │  JSON every    │                                      ││
│  │ Pushes at 250ms  │  250ms         │ useSystemState()                     ││
│  └──────────────────┘                │   └─ Derives layout state            ││
│                                      │                                      ││
│                                      │ <App>                                ││
│                                      │   └─ Layout Router                   ││
│                                      │       ├─ SleepingLayout              ││
│                                      │       ├─ StandbyLayout               ││
│                                      │       ├─ SwimmingLayout              ││
│                                      │       ├─ RestingLayout               ││
│                                      │       └─ SummaryLayout               ││
│                                      └──────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Push-Based Updates**: Dashboard is entirely reactive - it renders whatever the server sends. No client-side requests.

2. **Layout State Machine**: Dashboard derives which layout to show from WebSocket state:
   - No connection → SLEEPING
   - Connected, no session → STANDBY
   - Session active + is_swimming → SWIMMING
   - Session active + !is_swimming → RESTING
   - Session just ended → SUMMARY

3. **Component Isolation**: Each component receives typed props and can be tested independently with mock data.

4. **Poolside Readability**: All text must be readable from 10ft. Minimum font sizes enforced in theme.

---

## Phase 1: TypeScript Types & Mock Data

**Goal**: Define TypeScript interfaces matching WebSocket messages and create mock data generators.

### Tests First (`src/__tests__/types.test.ts`)

```typescript
import { describe, it, expect } from 'vitest';
import { isValidStateUpdate, parseStateUpdate } from '../types/state';
import { mockStateUpdate, mockSwimmingState, mockRestingState } from '../mocks/state';

describe('StateUpdate Types', () => {
  // Test 1: Valid state update parses correctly
  it('parses valid state update JSON', () => {
    const json = JSON.stringify(mockStateUpdate());
    const result = parseStateUpdate(json);
    expect(result).toBeDefined();
    expect(result.type).toBe('state_update');
  });

  // Test 2: Invalid JSON returns null
  it('returns null for invalid JSON', () => {
    const result = parseStateUpdate('not json');
    expect(result).toBeNull();
  });

  // Test 3: Missing required fields rejected
  it('rejects state update missing required fields', () => {
    const invalid = { type: 'state_update' }; // Missing session, system
    expect(isValidStateUpdate(invalid)).toBe(false);
  });

  // Test 4: Mock swimming state has correct shape
  it('mock swimming state is valid', () => {
    const state = mockSwimmingState();
    expect(isValidStateUpdate(state)).toBe(true);
    expect(state.session.active).toBe(true);
    expect(state.system.is_swimming).toBe(true);
  });

  // Test 5: Mock resting state has correct shape
  it('mock resting state is valid', () => {
    const state = mockRestingState();
    expect(isValidStateUpdate(state)).toBe(true);
    expect(state.session.active).toBe(true);
    expect(state.system.is_swimming).toBe(false);
  });

  // Test 6: SessionState type validation
  it('validates session state fields', () => {
    const state = mockStateUpdate();
    expect(typeof state.session.stroke_count).toBe('number');
    expect(typeof state.session.stroke_rate).toBe('number');
    expect(['increasing', 'stable', 'decreasing']).toContain(state.session.stroke_rate_trend);
  });

  // Test 7: SystemState type validation
  it('validates system state fields', () => {
    const state = mockStateUpdate();
    expect(typeof state.system.is_swimming).toBe('boolean');
    expect(typeof state.system.pose_detected).toBe('boolean');
    expect(['idle', 'listening', 'speaking']).toContain(state.system.voice_state);
  });
});
```

### Implementation

```typescript
// src/types/state.ts

export interface SessionState {
  active: boolean;
  elapsed_seconds: number;
  stroke_count: number;
  stroke_rate: number;
  stroke_rate_trend: 'increasing' | 'stable' | 'decreasing';
  estimated_distance_m: number;
}

export interface SystemState {
  is_swimming: boolean;
  pose_detected: boolean;
  voice_state: 'idle' | 'listening' | 'speaking';
}

export interface StateUpdate {
  type: 'state_update';
  timestamp: string;
  session: SessionState;
  system: SystemState;
}

export type LayoutState = 'SLEEPING' | 'STANDBY' | 'SWIMMING' | 'RESTING' | 'SUMMARY';

export function parseStateUpdate(json: string): StateUpdate | null {
  try {
    const data = JSON.parse(json);
    if (isValidStateUpdate(data)) {
      return data;
    }
    return null;
  } catch {
    return null;
  }
}

export function isValidStateUpdate(data: unknown): data is StateUpdate {
  if (typeof data !== 'object' || data === null) return false;
  const obj = data as Record<string, unknown>;

  return (
    obj.type === 'state_update' &&
    typeof obj.timestamp === 'string' &&
    typeof obj.session === 'object' &&
    typeof obj.system === 'object'
  );
}
```

```typescript
// src/mocks/state.ts

import { StateUpdate, SessionState, SystemState } from '../types/state';

export function mockSessionState(overrides: Partial<SessionState> = {}): SessionState {
  return {
    active: false,
    elapsed_seconds: 0,
    stroke_count: 0,
    stroke_rate: 0,
    stroke_rate_trend: 'stable',
    estimated_distance_m: 0,
    ...overrides,
  };
}

export function mockSystemState(overrides: Partial<SystemState> = {}): SystemState {
  return {
    is_swimming: false,
    pose_detected: false,
    voice_state: 'idle',
    ...overrides,
  };
}

export function mockStateUpdate(overrides: {
  session?: Partial<SessionState>;
  system?: Partial<SystemState>;
} = {}): StateUpdate {
  return {
    type: 'state_update',
    timestamp: new Date().toISOString(),
    session: mockSessionState(overrides.session),
    system: mockSystemState(overrides.system),
  };
}

export function mockSwimmingState(): StateUpdate {
  return mockStateUpdate({
    session: {
      active: true,
      elapsed_seconds: 300,
      stroke_count: 150,
      stroke_rate: 54,
      stroke_rate_trend: 'stable',
      estimated_distance_m: 270,
    },
    system: {
      is_swimming: true,
      pose_detected: true,
      voice_state: 'listening',
    },
  });
}

export function mockRestingState(): StateUpdate {
  return mockStateUpdate({
    session: {
      active: true,
      elapsed_seconds: 360,
      stroke_count: 180,
      stroke_rate: 0,
      stroke_rate_trend: 'stable',
      estimated_distance_m: 324,
    },
    system: {
      is_swimming: false,
      pose_detected: true,
      voice_state: 'listening',
    },
  });
}

export function mockStandbyState(): StateUpdate {
  return mockStateUpdate({
    session: { active: false },
    system: { pose_detected: true, voice_state: 'listening' },
  });
}
```

---

## Phase 2: WebSocket Hook

**Goal**: Custom hook for WebSocket connection with auto-reconnect.

### Tests First (`src/hooks/__tests__/useWebSocket.test.ts`)

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useWebSocket } from '../useWebSocket';
import WS from 'jest-websocket-mock';

describe('useWebSocket', () => {
  let server: WS;
  const TEST_URL = 'ws://localhost:8765';

  beforeEach(() => {
    server = new WS(TEST_URL);
  });

  afterEach(() => {
    WS.clean();
  });

  // Test 1: Connects to WebSocket server
  it('connects to WebSocket server', async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));

    await server.connected;
    expect(result.current.isConnected).toBe(true);
  });

  // Test 2: Parses received state updates
  it('parses received state updates', async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));
    await server.connected;

    act(() => {
      server.send(JSON.stringify({
        type: 'state_update',
        timestamp: new Date().toISOString(),
        session: { active: true, stroke_rate: 54 },
        system: { is_swimming: true },
      }));
    });

    await waitFor(() => {
      expect(result.current.state?.session.stroke_rate).toBe(54);
    });
  });

  // Test 3: Handles disconnection
  it('sets isConnected false on disconnect', async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));
    await server.connected;

    expect(result.current.isConnected).toBe(true);

    server.close();

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false);
    });
  });

  // Test 4: Auto-reconnects after disconnect
  it('attempts reconnection after disconnect', async () => {
    vi.useFakeTimers();
    const { result } = renderHook(() =>
      useWebSocket(TEST_URL, { reconnectInterval: 1000 })
    );

    await server.connected;
    server.close();

    // Create new server for reconnection
    server = new WS(TEST_URL);

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    await server.connected;
    expect(result.current.isConnected).toBe(true);

    vi.useRealTimers();
  });

  // Test 5: Ignores invalid messages
  it('ignores invalid JSON messages', async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));
    await server.connected;

    act(() => {
      server.send('not valid json');
    });

    // State should remain null/unchanged
    expect(result.current.state).toBeNull();
  });

  // Test 6: Provides connection status
  it('tracks connection status', async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));

    expect(result.current.connectionStatus).toBe('connecting');

    await server.connected;
    expect(result.current.connectionStatus).toBe('connected');

    server.close();
    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('disconnected');
    });
  });

  // Test 7: Cleans up on unmount
  it('closes connection on unmount', async () => {
    const { result, unmount } = renderHook(() => useWebSocket(TEST_URL));
    await server.connected;

    unmount();

    await server.closed;
  });

  // Test 8: Provides error state
  it('provides error on connection failure', async () => {
    server.close();

    const { result } = renderHook(() => useWebSocket('ws://invalid:9999'));

    await waitFor(() => {
      expect(result.current.error).toBeDefined();
    });
  });
});
```

### Implementation

```typescript
// src/hooks/useWebSocket.ts

import { useState, useEffect, useRef, useCallback } from 'react';
import { StateUpdate, parseStateUpdate } from '../types/state';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface UseWebSocketOptions {
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export interface UseWebSocketResult {
  state: StateUpdate | null;
  isConnected: boolean;
  connectionStatus: ConnectionStatus;
  error: Error | null;
}

export function useWebSocket(
  url: string,
  options: UseWebSocketOptions = {}
): UseWebSocketResult {
  const { reconnectInterval = 2000, maxReconnectAttempts = 10 } = options;

  const [state, setState] = useState<StateUpdate | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting');
  const [error, setError] = useState<Error | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;
      setConnectionStatus('connecting');
      setError(null);

      ws.onopen = () => {
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        const parsed = parseStateUpdate(event.data);
        if (parsed) {
          setState(parsed);
        }
      };

      ws.onclose = () => {
        setConnectionStatus('disconnected');
        scheduleReconnect();
      };

      ws.onerror = (e) => {
        setError(new Error('WebSocket error'));
        setConnectionStatus('error');
      };
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Connection failed'));
      setConnectionStatus('error');
    }
  }, [url]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      return;
    }

    reconnectTimeoutRef.current = setTimeout(() => {
      reconnectAttemptsRef.current += 1;
      connect();
    }, reconnectInterval);
  }, [connect, reconnectInterval, maxReconnectAttempts]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    state,
    isConnected: connectionStatus === 'connected',
    connectionStatus,
    error,
  };
}
```

---

## Phase 3: System State Hook

**Goal**: Derive layout state and provide computed values.

### Tests First (`src/hooks/__tests__/useSystemState.test.ts`)

```typescript
import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useSystemState } from '../useSystemState';
import { mockSwimmingState, mockRestingState, mockStandbyState } from '../../mocks/state';

describe('useSystemState', () => {
  // Test 1: Returns SLEEPING when no state
  it('returns SLEEPING layout when state is null', () => {
    const { result } = renderHook(() => useSystemState(null));
    expect(result.current.layoutState).toBe('SLEEPING');
  });

  // Test 2: Returns STANDBY when no active session
  it('returns STANDBY when session not active', () => {
    const { result } = renderHook(() => useSystemState(mockStandbyState()));
    expect(result.current.layoutState).toBe('STANDBY');
  });

  // Test 3: Returns SWIMMING when active and swimming
  it('returns SWIMMING when session active and is_swimming', () => {
    const { result } = renderHook(() => useSystemState(mockSwimmingState()));
    expect(result.current.layoutState).toBe('SWIMMING');
  });

  // Test 4: Returns RESTING when active but not swimming
  it('returns RESTING when session active but not swimming', () => {
    const { result } = renderHook(() => useSystemState(mockRestingState()));
    expect(result.current.layoutState).toBe('RESTING');
  });

  // Test 5: Provides formatted time
  it('formats elapsed time correctly', () => {
    const state = mockSwimmingState();
    state.session.elapsed_seconds = 125;

    const { result } = renderHook(() => useSystemState(state));
    expect(result.current.formattedTime).toBe('2:05');
  });

  // Test 6: Formats zero time
  it('formats zero elapsed time', () => {
    const state = mockSwimmingState();
    state.session.elapsed_seconds = 0;

    const { result } = renderHook(() => useSystemState(state));
    expect(result.current.formattedTime).toBe('0:00');
  });

  // Test 7: Formats hour+ time
  it('formats time over an hour', () => {
    const state = mockSwimmingState();
    state.session.elapsed_seconds = 3665; // 1:01:05

    const { result } = renderHook(() => useSystemState(state));
    expect(result.current.formattedTime).toBe('61:05');
  });

  // Test 8: Provides trend arrow
  it('returns correct trend arrow for increasing', () => {
    const state = mockSwimmingState();
    state.session.stroke_rate_trend = 'increasing';

    const { result } = renderHook(() => useSystemState(state));
    expect(result.current.trendArrow).toBe('↑');
  });

  // Test 9: Trend arrow for stable
  it('returns correct trend arrow for stable', () => {
    const state = mockSwimmingState();
    state.session.stroke_rate_trend = 'stable';

    const { result } = renderHook(() => useSystemState(state));
    expect(result.current.trendArrow).toBe('↔');
  });

  // Test 10: Trend arrow for decreasing
  it('returns correct trend arrow for decreasing', () => {
    const state = mockSwimmingState();
    state.session.stroke_rate_trend = 'decreasing';

    const { result } = renderHook(() => useSystemState(state));
    expect(result.current.trendArrow).toBe('↓');
  });

  // Test 11: Provides voice status text
  it('returns voice status text', () => {
    const state = mockSwimmingState();
    state.system.voice_state = 'listening';

    const { result } = renderHook(() => useSystemState(state));
    expect(result.current.voiceStatusText).toBe('Listening');
  });

  // Test 12: Provides formatted distance
  it('formats distance with units', () => {
    const state = mockSwimmingState();
    state.session.estimated_distance_m = 1234.5;

    const { result } = renderHook(() => useSystemState(state));
    expect(result.current.formattedDistance).toBe('1,235m');
  });
});
```

### Implementation

```typescript
// src/hooks/useSystemState.ts

import { useMemo } from 'react';
import { StateUpdate, LayoutState } from '../types/state';

export interface UseSystemStateResult {
  layoutState: LayoutState;
  formattedTime: string;
  trendArrow: string;
  voiceStatusText: string;
  formattedDistance: string;
  isConnected: boolean;
}

export function useSystemState(state: StateUpdate | null): UseSystemStateResult {
  return useMemo(() => {
    // Derive layout state
    let layoutState: LayoutState = 'SLEEPING';

    if (state) {
      if (!state.session.active) {
        layoutState = 'STANDBY';
      } else if (state.system.is_swimming) {
        layoutState = 'SWIMMING';
      } else {
        layoutState = 'RESTING';
      }
    }

    // Format time
    const elapsed = state?.session.elapsed_seconds ?? 0;
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    const formattedTime = `${minutes}:${seconds.toString().padStart(2, '0')}`;

    // Trend arrow
    const trendMap: Record<string, string> = {
      increasing: '↑',
      stable: '↔',
      decreasing: '↓',
    };
    const trendArrow = trendMap[state?.session.stroke_rate_trend ?? 'stable'];

    // Voice status
    const voiceMap: Record<string, string> = {
      idle: 'Idle',
      listening: 'Listening',
      speaking: 'Speaking',
    };
    const voiceStatusText = voiceMap[state?.system.voice_state ?? 'idle'];

    // Format distance
    const distance = Math.round(state?.session.estimated_distance_m ?? 0);
    const formattedDistance = `${distance.toLocaleString()}m`;

    return {
      layoutState,
      formattedTime,
      trendArrow,
      voiceStatusText,
      formattedDistance,
      isConnected: state !== null,
    };
  }, [state]);
}
```

---

## Phase 4: Core Components

**Goal**: Individual display components with poolside-readable styling.

### Tests First (`src/components/__tests__/`)

```typescript
// src/components/__tests__/StrokeRate.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StrokeRate } from '../StrokeRate';

describe('StrokeRate', () => {
  // Test 1: Displays rate value
  it('displays stroke rate', () => {
    render(<StrokeRate rate={54} trend="stable" />);
    expect(screen.getByText('54')).toBeInTheDocument();
  });

  // Test 2: Shows /min label
  it('shows per minute label', () => {
    render(<StrokeRate rate={54} trend="stable" />);
    expect(screen.getByText('/min')).toBeInTheDocument();
  });

  // Test 3: Shows trend arrow
  it('displays trend arrow', () => {
    render(<StrokeRate rate={54} trend="increasing" />);
    expect(screen.getByText('↑')).toBeInTheDocument();
  });

  // Test 4: Has large font for poolside visibility
  it('uses large font size', () => {
    render(<StrokeRate rate={54} trend="stable" />);
    const rateElement = screen.getByText('54');
    expect(rateElement).toHaveClass('text-giant');
  });

  // Test 5: Handles zero rate
  it('displays zero rate', () => {
    render(<StrokeRate rate={0} trend="stable" />);
    expect(screen.getByText('0')).toBeInTheDocument();
  });
});
```

```typescript
// src/components/__tests__/SessionTimer.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SessionTimer } from '../SessionTimer';

describe('SessionTimer', () => {
  // Test 1: Displays formatted time
  it('displays formatted time', () => {
    render(<SessionTimer time="14:32" />);
    expect(screen.getByText('14:32')).toBeInTheDocument();
  });

  // Test 2: Has session time label
  it('shows session time label', () => {
    render(<SessionTimer time="14:32" showLabel />);
    expect(screen.getByText('SESSION TIME')).toBeInTheDocument();
  });

  // Test 3: Large font for visibility
  it('uses large font', () => {
    render(<SessionTimer time="14:32" />);
    const timeElement = screen.getByText('14:32');
    expect(timeElement).toHaveClass('text-large');
  });
});
```

```typescript
// src/components/__tests__/VoiceIndicator.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { VoiceIndicator } from '../VoiceIndicator';

describe('VoiceIndicator', () => {
  // Test 1: Shows status dot
  it('renders status dot', () => {
    render(<VoiceIndicator status="listening" />);
    expect(screen.getByTestId('voice-dot')).toBeInTheDocument();
  });

  // Test 2: Shows status text
  it('displays status text', () => {
    render(<VoiceIndicator status="listening" />);
    expect(screen.getByText('Listening')).toBeInTheDocument();
  });

  // Test 3: Dot color changes with status
  it('has correct color for listening', () => {
    render(<VoiceIndicator status="listening" />);
    const dot = screen.getByTestId('voice-dot');
    expect(dot).toHaveClass('bg-green-500');
  });

  // Test 4: Speaking status
  it('shows speaking status', () => {
    render(<VoiceIndicator status="speaking" />);
    expect(screen.getByText('Speaking')).toBeInTheDocument();
    expect(screen.getByTestId('voice-dot')).toHaveClass('bg-blue-500');
  });

  // Test 5: Idle status
  it('shows idle status', () => {
    render(<VoiceIndicator status="idle" />);
    expect(screen.getByTestId('voice-dot')).toHaveClass('bg-gray-500');
  });

  // Test 6: Dot pulses when active
  it('dot pulses when listening', () => {
    render(<VoiceIndicator status="listening" />);
    expect(screen.getByTestId('voice-dot')).toHaveClass('animate-pulse');
  });
});
```

```typescript
// src/components/__tests__/RateGraph.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RateGraph } from '../RateGraph';

describe('RateGraph', () => {
  const mockHistory = [
    { timestamp: 1, rate: 50 },
    { timestamp: 2, rate: 52 },
    { timestamp: 3, rate: 54 },
    { timestamp: 4, rate: 53 },
    { timestamp: 5, rate: 55 },
  ];

  // Test 1: Renders SVG sparkline
  it('renders sparkline SVG', () => {
    render(<RateGraph history={mockHistory} />);
    expect(screen.getByRole('img', { name: /rate graph/i })).toBeInTheDocument();
  });

  // Test 2: Handles empty history
  it('renders placeholder for empty history', () => {
    render(<RateGraph history={[]} />);
    expect(screen.getByText('No data')).toBeInTheDocument();
  });

  // Test 3: Handles single data point
  it('renders with single point', () => {
    render(<RateGraph history={[{ timestamp: 1, rate: 50 }]} />);
    expect(screen.getByRole('img')).toBeInTheDocument();
  });

  // Test 4: Scales to container
  it('fills container width', () => {
    const { container } = render(<RateGraph history={mockHistory} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', '100%');
  });
});
```

```typescript
// src/components/__tests__/DistanceEstimate.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DistanceEstimate } from '../DistanceEstimate';

describe('DistanceEstimate', () => {
  // Test 1: Displays distance
  it('displays formatted distance', () => {
    render(<DistanceEstimate distance="1,234m" />);
    expect(screen.getByText('1,234m')).toBeInTheDocument();
  });

  // Test 2: Shows label
  it('shows estimated label', () => {
    render(<DistanceEstimate distance="500m" showLabel />);
    expect(screen.getByText('EST. DISTANCE')).toBeInTheDocument();
  });

  // Test 3: Shows tilde for estimate
  it('shows tilde prefix', () => {
    render(<DistanceEstimate distance="500m" showTilde />);
    expect(screen.getByText('~500m')).toBeInTheDocument();
  });
});
```

### Implementation

```typescript
// src/components/StrokeRate.tsx
interface StrokeRateProps {
  rate: number;
  trend: 'increasing' | 'stable' | 'decreasing';
}

const trendArrows = {
  increasing: '↑',
  stable: '↔',
  decreasing: '↓',
};

export function StrokeRate({ rate, trend }: StrokeRateProps) {
  return (
    <div className="flex items-center justify-center gap-4">
      <span className="text-giant font-bold">{Math.round(rate)}</span>
      <div className="flex flex-col items-start">
        <span className="text-large text-muted">/min</span>
        <span className="text-large">{trendArrows[trend]}</span>
      </div>
    </div>
  );
}
```

```typescript
// src/components/SessionTimer.tsx
interface SessionTimerProps {
  time: string;
  showLabel?: boolean;
}

export function SessionTimer({ time, showLabel = false }: SessionTimerProps) {
  return (
    <div className="text-center">
      <div className="text-large font-mono">{time}</div>
      {showLabel && <div className="text-sm text-muted uppercase">Session Time</div>}
    </div>
  );
}
```

```typescript
// src/components/VoiceIndicator.tsx
interface VoiceIndicatorProps {
  status: 'idle' | 'listening' | 'speaking';
}

const statusConfig = {
  idle: { color: 'bg-gray-500', text: 'Idle', pulse: false },
  listening: { color: 'bg-green-500', text: 'Listening', pulse: true },
  speaking: { color: 'bg-blue-500', text: 'Speaking', pulse: true },
};

export function VoiceIndicator({ status }: VoiceIndicatorProps) {
  const config = statusConfig[status];

  return (
    <div className="flex items-center gap-2">
      <div
        data-testid="voice-dot"
        className={`w-3 h-3 rounded-full ${config.color} ${config.pulse ? 'animate-pulse' : ''}`}
      />
      <span className="text-sm">{config.text}</span>
    </div>
  );
}
```

---

## Phase 5: Layout Components

**Goal**: Adaptive layouts for different system states.

### Tests First (`src/layouts/__tests__/`)

```typescript
// src/layouts/__tests__/SwimmingLayout.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SwimmingLayout } from '../SwimmingLayout';
import { mockSwimmingState } from '../../mocks/state';

describe('SwimmingLayout', () => {
  // Test 1: Shows giant stroke rate
  it('displays stroke rate prominently', () => {
    render(<SwimmingLayout state={mockSwimmingState()} />);
    expect(screen.getByText('54')).toBeInTheDocument();
  });

  // Test 2: Shows session timer
  it('displays session timer', () => {
    render(<SwimmingLayout state={mockSwimmingState()} />);
    expect(screen.getByText('5:00')).toBeInTheDocument();
  });

  // Test 3: Shows voice indicator
  it('displays voice indicator', () => {
    render(<SwimmingLayout state={mockSwimmingState()} />);
    expect(screen.getByText('Listening')).toBeInTheDocument();
  });

  // Test 4: Minimal layout (few elements)
  it('has minimal layout', () => {
    const { container } = render(<SwimmingLayout state={mockSwimmingState()} />);
    // Should have limited number of main sections
    const sections = container.querySelectorAll('[data-section]');
    expect(sections.length).toBeLessThanOrEqual(4);
  });

  // Test 5: Rate graph visible
  it('shows rate sparkline', () => {
    render(<SwimmingLayout state={mockSwimmingState()} />);
    expect(screen.getByRole('img', { name: /rate graph/i })).toBeInTheDocument();
  });
});
```

```typescript
// src/layouts/__tests__/RestingLayout.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RestingLayout } from '../RestingLayout';
import { mockRestingState } from '../../mocks/state';

describe('RestingLayout', () => {
  // Test 1: Shows session timer
  it('displays session timer with label', () => {
    render(<RestingLayout state={mockRestingState()} />);
    expect(screen.getByText('SESSION TIME')).toBeInTheDocument();
  });

  // Test 2: Shows rest timer (placeholder for workout integration)
  it('has rest timer section', () => {
    render(<RestingLayout state={mockRestingState()} />);
    expect(screen.getByTestId('rest-timer')).toBeInTheDocument();
  });

  // Test 3: Shows last interval summary
  it('displays last interval section', () => {
    render(<RestingLayout state={mockRestingState()} />);
    expect(screen.getByText('LAST INTERVAL')).toBeInTheDocument();
  });

  // Test 4: Shows rate graph
  it('displays session rate graph', () => {
    render(<RestingLayout state={mockRestingState()} />);
    expect(screen.getByRole('img', { name: /rate graph/i })).toBeInTheDocument();
  });

  // Test 5: Shows coach message area
  it('has coach message section', () => {
    render(<RestingLayout state={mockRestingState()} />);
    expect(screen.getByTestId('coach-message')).toBeInTheDocument();
  });

  // Test 6: Shows voice indicator
  it('displays voice indicator', () => {
    render(<RestingLayout state={mockRestingState()} />);
    expect(screen.getByText('Listening')).toBeInTheDocument();
  });

  // Test 7: More detail than swimming layout
  it('has expanded layout', () => {
    const { container } = render(<RestingLayout state={mockRestingState()} />);
    const sections = container.querySelectorAll('[data-section]');
    expect(sections.length).toBeGreaterThan(4);
  });
});
```

```typescript
// src/layouts/__tests__/StandbyLayout.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StandbyLayout } from '../StandbyLayout';

describe('StandbyLayout', () => {
  // Test 1: Shows ready message
  it('displays ready to swim message', () => {
    render(<StandbyLayout />);
    expect(screen.getByText(/ready to swim/i)).toBeInTheDocument();
  });

  // Test 2: Shows voice indicator
  it('displays voice indicator', () => {
    render(<StandbyLayout voiceState="listening" />);
    expect(screen.getByText('Listening')).toBeInTheDocument();
  });

  // Test 3: Shows current time
  it('displays current time', () => {
    render(<StandbyLayout />);
    expect(screen.getByTestId('clock')).toBeInTheDocument();
  });
});
```

```typescript
// src/layouts/__tests__/SleepingLayout.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SleepingLayout } from '../SleepingLayout';

describe('SleepingLayout', () => {
  // Test 1: Shows clock only
  it('displays clock', () => {
    render(<SleepingLayout />);
    expect(screen.getByTestId('clock')).toBeInTheDocument();
  });

  // Test 2: Minimal content
  it('has minimal content', () => {
    const { container } = render(<SleepingLayout />);
    // Should be very sparse
    expect(container.textContent?.length).toBeLessThan(100);
  });

  // Test 3: Dark/ambient styling
  it('has ambient dark styling', () => {
    const { container } = render(<SleepingLayout />);
    expect(container.firstChild).toHaveClass('bg-black');
  });
});
```

### Implementation

```typescript
// src/layouts/SwimmingLayout.tsx
import { StateUpdate } from '../types/state';
import { StrokeRate } from '../components/StrokeRate';
import { SessionTimer } from '../components/SessionTimer';
import { RateGraph } from '../components/RateGraph';
import { VoiceIndicator } from '../components/VoiceIndicator';
import { useSystemState } from '../hooks/useSystemState';

interface SwimmingLayoutProps {
  state: StateUpdate;
}

export function SwimmingLayout({ state }: SwimmingLayoutProps) {
  const { formattedTime } = useSystemState(state);

  return (
    <div className="h-screen flex flex-col items-center justify-center bg-slate-900 text-white p-8">
      {/* Timer - top */}
      <div data-section="timer" className="mb-8">
        <SessionTimer time={formattedTime} />
      </div>

      {/* Giant stroke rate - center */}
      <div data-section="rate" className="mb-8">
        <StrokeRate
          rate={state.session.stroke_rate}
          trend={state.session.stroke_rate_trend}
        />
      </div>

      {/* Sparkline - bottom center */}
      <div data-section="graph" className="w-full max-w-xl mb-8">
        <RateGraph history={[]} /> {/* Will be connected to rate history */}
      </div>

      {/* Voice indicator - bottom right */}
      <div data-section="voice" className="absolute bottom-8 right-8">
        <VoiceIndicator status={state.system.voice_state} />
      </div>
    </div>
  );
}
```

```typescript
// src/layouts/RestingLayout.tsx
import { StateUpdate } from '../types/state';
import { SessionTimer } from '../components/SessionTimer';
import { RateGraph } from '../components/RateGraph';
import { VoiceIndicator } from '../components/VoiceIndicator';
import { DistanceEstimate } from '../components/DistanceEstimate';
import { useSystemState } from '../hooks/useSystemState';

interface RestingLayoutProps {
  state: StateUpdate;
  coachMessage?: string;
}

export function RestingLayout({ state, coachMessage }: RestingLayoutProps) {
  const { formattedTime, formattedDistance } = useSystemState(state);

  return (
    <div className="h-screen bg-slate-900 text-white p-8">
      {/* Header row */}
      <div className="flex justify-between mb-8">
        <div data-section="timer">
          <SessionTimer time={formattedTime} showLabel />
        </div>
        <div data-section="rest" data-testid="rest-timer">
          <div className="text-large">REST</div>
          <div className="text-muted">0:45 remaining</div>
        </div>
      </div>

      {/* Two-column content */}
      <div className="grid grid-cols-2 gap-8 mb-8">
        <div data-section="last-interval">
          <h3 className="text-sm uppercase text-muted mb-2">Last Interval</h3>
          <div>Avg: {state.session.stroke_rate} /min</div>
          <div>Est: {formattedDistance}</div>
          <div>Strokes: {state.session.stroke_count}</div>
        </div>
        <div data-section="next-up">
          <h3 className="text-sm uppercase text-muted mb-2">Next Up</h3>
          <div>INTERVAL 2 of 4</div>
          <div>4:00 duration</div>
        </div>
      </div>

      {/* Rate graph */}
      <div data-section="graph" className="mb-8">
        <RateGraph history={[]} />
      </div>

      {/* Coach message */}
      <div data-section="coach" data-testid="coach-message" className="p-4 bg-slate-800 rounded mb-4">
        <span className="text-muted">COACH: </span>
        <span>{coachMessage || "Ready when you are!"}</span>
      </div>

      {/* Voice indicator */}
      <div data-section="voice">
        <VoiceIndicator status={state.system.voice_state} />
      </div>
    </div>
  );
}
```

---

## Phase 6: App & Layout Router

**Goal**: Main app component that switches layouts based on state.

### Tests First (`src/__tests__/App.test.tsx`)

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { App } from '../App';
import WS from 'jest-websocket-mock';
import { mockSwimmingState, mockRestingState, mockStandbyState } from '../mocks/state';

describe('App', () => {
  let server: WS;

  beforeEach(() => {
    server = new WS('ws://localhost:8765');
  });

  afterEach(() => {
    WS.clean();
  });

  // Test 1: Shows sleeping layout on no connection
  it('shows sleeping layout when disconnected', () => {
    render(<App />);
    // Before connection established
    expect(screen.getByTestId('sleeping-layout')).toBeInTheDocument();
  });

  // Test 2: Shows standby after connection without session
  it('shows standby layout when connected without session', async () => {
    render(<App />);
    await server.connected;

    server.send(JSON.stringify(mockStandbyState()));

    await waitFor(() => {
      expect(screen.getByText(/ready to swim/i)).toBeInTheDocument();
    });
  });

  // Test 3: Shows swimming layout when swimming
  it('shows swimming layout when session active and swimming', async () => {
    render(<App />);
    await server.connected;

    server.send(JSON.stringify(mockSwimmingState()));

    await waitFor(() => {
      expect(screen.getByTestId('swimming-layout')).toBeInTheDocument();
    });
  });

  // Test 4: Shows resting layout when not swimming
  it('shows resting layout when session active but not swimming', async () => {
    render(<App />);
    await server.connected;

    server.send(JSON.stringify(mockRestingState()));

    await waitFor(() => {
      expect(screen.getByTestId('resting-layout')).toBeInTheDocument();
    });
  });

  // Test 5: Transitions between layouts smoothly
  it('transitions from swimming to resting', async () => {
    render(<App />);
    await server.connected;

    server.send(JSON.stringify(mockSwimmingState()));
    await waitFor(() => {
      expect(screen.getByTestId('swimming-layout')).toBeInTheDocument();
    });

    server.send(JSON.stringify(mockRestingState()));
    await waitFor(() => {
      expect(screen.getByTestId('resting-layout')).toBeInTheDocument();
    });
  });

  // Test 6: Has dark theme
  it('uses dark theme', () => {
    const { container } = render(<App />);
    expect(container.firstChild).toHaveClass('dark');
  });

  // Test 7: Shows connection status indicator
  it('shows connection status when disconnected', async () => {
    render(<App />);
    await server.connected;
    server.close();

    await waitFor(() => {
      expect(screen.getByText(/disconnected/i)).toBeInTheDocument();
    });
  });
});
```

### Implementation

```typescript
// src/App.tsx
import { useWebSocket } from './hooks/useWebSocket';
import { useSystemState } from './hooks/useSystemState';
import { SleepingLayout } from './layouts/SleepingLayout';
import { StandbyLayout } from './layouts/StandbyLayout';
import { SwimmingLayout } from './layouts/SwimmingLayout';
import { RestingLayout } from './layouts/RestingLayout';
import { SummaryLayout } from './layouts/SummaryLayout';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8765';

export function App() {
  const { state, isConnected, connectionStatus } = useWebSocket(WS_URL);
  const { layoutState } = useSystemState(state);

  return (
    <div className="dark">
      {/* Connection status overlay */}
      {connectionStatus === 'disconnected' && (
        <div className="absolute top-4 left-4 bg-red-500 text-white px-3 py-1 rounded z-50">
          Disconnected
        </div>
      )}

      {/* Layout router */}
      {layoutState === 'SLEEPING' && (
        <div data-testid="sleeping-layout">
          <SleepingLayout />
        </div>
      )}

      {layoutState === 'STANDBY' && state && (
        <div data-testid="standby-layout">
          <StandbyLayout voiceState={state.system.voice_state} />
        </div>
      )}

      {layoutState === 'SWIMMING' && state && (
        <div data-testid="swimming-layout">
          <SwimmingLayout state={state} />
        </div>
      )}

      {layoutState === 'RESTING' && state && (
        <div data-testid="resting-layout">
          <RestingLayout state={state} />
        </div>
      )}

      {layoutState === 'SUMMARY' && state && (
        <div data-testid="summary-layout">
          <SummaryLayout state={state} />
        </div>
      )}
    </div>
  );
}
```

---

## Phase 7: Styling & Theme

**Goal**: Dark theme with poolside-readable fonts.

### Tests First (`src/styles/__tests__/theme.test.ts`)

```typescript
import { describe, it, expect } from 'vitest';
import { theme } from '../theme';

describe('Theme', () => {
  // Test 1: Has dark background
  it('defines dark background colors', () => {
    expect(theme.colors.background).toBe('#0f172a'); // slate-900
  });

  // Test 2: Has readable text colors
  it('defines high-contrast text', () => {
    expect(theme.colors.text).toBe('#f8fafc'); // slate-50
  });

  // Test 3: Giant text size defined
  it('defines giant text size for rates', () => {
    expect(parseInt(theme.fontSize.giant)).toBeGreaterThanOrEqual(96);
  });

  // Test 4: Large text readable from 10ft
  it('defines large text for poolside visibility', () => {
    expect(parseInt(theme.fontSize.large)).toBeGreaterThanOrEqual(48);
  });

  // Test 5: Monospace font for numbers
  it('uses monospace for numeric displays', () => {
    expect(theme.fontFamily.mono).toContain('mono');
  });
});
```

### Implementation

```css
/* src/styles/theme.css */
:root {
  /* Colors - Dark theme for reduced glare */
  --color-background: #0f172a;       /* slate-900 */
  --color-surface: #1e293b;          /* slate-800 */
  --color-text: #f8fafc;             /* slate-50 */
  --color-text-muted: #94a3b8;       /* slate-400 */
  --color-accent: #38bdf8;           /* sky-400 */
  --color-success: #22c55e;          /* green-500 */
  --color-warning: #f59e0b;          /* amber-500 */

  /* Font sizes - Poolside readable (10ft distance) */
  --font-giant: 8rem;                /* 128px - stroke rate */
  --font-large: 4rem;                /* 64px - timer, labels */
  --font-medium: 2rem;               /* 32px - secondary info */
  --font-small: 1.25rem;             /* 20px - captions */
}

/* Utility classes */
.text-giant {
  font-size: var(--font-giant);
  line-height: 1;
}

.text-large {
  font-size: var(--font-large);
  line-height: 1.1;
}

.text-medium {
  font-size: var(--font-medium);
}

.text-muted {
  color: var(--color-text-muted);
}

/* Dark theme base */
.dark {
  background-color: var(--color-background);
  color: var(--color-text);
}
```

---

## File Structure After TDD

```
dashboard/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── vitest.config.ts
├── index.html
├── public/
│   └── favicon.ico
├── src/
│   ├── index.tsx
│   ├── App.tsx
│   ├── __tests__/
│   │   ├── App.test.tsx
│   │   └── types.test.ts
│   ├── types/
│   │   └── state.ts
│   ├── mocks/
│   │   └── state.ts
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useSystemState.ts
│   │   └── __tests__/
│   │       ├── useWebSocket.test.ts
│   │       └── useSystemState.test.ts
│   ├── components/
│   │   ├── StrokeRate.tsx
│   │   ├── SessionTimer.tsx
│   │   ├── RateGraph.tsx
│   │   ├── VoiceIndicator.tsx
│   │   ├── DistanceEstimate.tsx
│   │   ├── CoachMessage.tsx
│   │   └── __tests__/
│   │       ├── StrokeRate.test.tsx
│   │       ├── SessionTimer.test.tsx
│   │       ├── RateGraph.test.tsx
│   │       ├── VoiceIndicator.test.tsx
│   │       └── DistanceEstimate.test.tsx
│   ├── layouts/
│   │   ├── SleepingLayout.tsx
│   │   ├── StandbyLayout.tsx
│   │   ├── SwimmingLayout.tsx
│   │   ├── RestingLayout.tsx
│   │   ├── SummaryLayout.tsx
│   │   └── __tests__/
│   │       ├── SleepingLayout.test.tsx
│   │       ├── StandbyLayout.test.tsx
│   │       ├── SwimmingLayout.test.tsx
│   │       ├── RestingLayout.test.tsx
│   │       └── SummaryLayout.test.tsx
│   └── styles/
│       ├── theme.css
│       ├── theme.ts
│       ├── animations.css
│       └── __tests__/
│           └── theme.test.ts
```

---

## Implementation Order (TDD Red-Green-Refactor)

| Order | Component | Tests | Implementation |
|-------|-----------|-------|----------------|
| 1 | Types & Mocks | `types.test.ts` | `types/state.ts`, `mocks/state.ts` |
| 2 | useWebSocket | `useWebSocket.test.ts` | `hooks/useWebSocket.ts` |
| 3 | useSystemState | `useSystemState.test.ts` | `hooks/useSystemState.ts` |
| 4 | Core Components | `components/__tests__/*` | Individual components |
| 5 | Theme | `theme.test.ts` | `styles/theme.css` |
| 6 | Layouts | `layouts/__tests__/*` | Layout components |
| 7 | App | `App.test.tsx` | `App.tsx` |

---

## Test Execution

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run specific test file
npm test -- src/hooks/__tests__/useWebSocket.test.ts

# Run with coverage
npm run test:coverage

# Run component tests only
npm test -- src/components/__tests__

# Run layout tests only
npm test -- src/layouts/__tests__
```

---

## Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "vitest": "^1.0.0",
    "jest-websocket-mock": "^2.5.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

---

## Success Criteria

From the requirements:

- [x] Dashboard connects to WebSocket and displays state
- [x] Layout transitions smoothly between states
- [x] Text readable from 10ft distance (pool)
- [x] Dark theme reduces glare
- [x] Voice indicator shows correct status
- [x] Works with mock data for early development

Additional criteria:

- [ ] All unit tests pass
- [ ] All component tests pass
- [ ] All layout tests pass
- [ ] >80% code coverage
- [ ] Responsive (works on various screen sizes)
- [ ] No console errors during operation
- [ ] Reconnects automatically after disconnect

---

## Notes

1. **Mock-First Development**: All components can be developed and tested with mock data before MCP server integration.

2. **WebSocket Mock**: `jest-websocket-mock` provides a fake WebSocket server for realistic testing.

3. **Vitest**: Using Vitest for fast, Vite-compatible testing with good React support.

4. **Tailwind CSS**: For rapid styling with dark theme utilities built-in.

5. **Layout State Machine**: Simple state derivation rather than complex state machine library - keeps it testable.

6. **Rate History for Graph**: The `RateGraph` component will need rate history data. This will be added in the swim-metrics integration - for now, we pass an empty array.

7. **Workout Integration**: The resting layout has placeholders for workout/interval data that will come from Branch 5.

8. **Coach Message**: Placeholder for messages from Claude integration (Branch 9).

---

## Appendix: ASCII Layout Reference

### SWIMMING Layout (Minimal)

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
│         ▁▂▃▄▅▆▅▄▃▄▅▆▇▆▅▄▅▆▅▄▃▄▅▆▇▆▅▄▃▂▁▂▃▄▅▆▅▄▃▂                           │
│                                                                             │
│                                                     ◉ Listening             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### RESTING Layout (Expanded)

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
│  ▁▂▃▄▅▆▅▄▃▄▅▆▇▆▅▄▅▆▅▄▃▄▅▆▇▆▅▄▃▂▁▂▃▄▅▆▅▄▃▂ (session so far)                  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  COACH: "Solid interval! You held 52 consistently. Ready for the next?"    │
│                                                                             │
│  ◉ Listening...                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```
