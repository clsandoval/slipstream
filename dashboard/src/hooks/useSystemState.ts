import { useMemo } from 'react';
import type { StateUpdate, LayoutState } from '../types/state';

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
