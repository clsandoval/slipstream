import type { StateUpdate, SessionState, SystemState } from '../types/state';

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
