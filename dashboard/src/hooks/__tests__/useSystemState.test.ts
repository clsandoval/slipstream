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
    state.session.elapsed_seconds = 3665; // 61:05

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

  // Additional tests
  it('returns default trend arrow when state is null', () => {
    const { result } = renderHook(() => useSystemState(null));
    expect(result.current.trendArrow).toBe('↔');
  });

  it('returns default voice status when state is null', () => {
    const { result } = renderHook(() => useSystemState(null));
    expect(result.current.voiceStatusText).toBe('Idle');
  });
});
