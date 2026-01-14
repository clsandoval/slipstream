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
    const data: unknown = JSON.parse(json);
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

  if (obj.type !== 'state_update') return false;
  if (typeof obj.timestamp !== 'string') return false;
  if (typeof obj.session !== 'object' || obj.session === null) return false;
  if (typeof obj.system !== 'object' || obj.system === null) return false;

  const session = obj.session as Record<string, unknown>;
  const system = obj.system as Record<string, unknown>;

  // Validate session fields
  if (typeof session.active !== 'boolean') return false;
  if (typeof session.elapsed_seconds !== 'number') return false;
  if (typeof session.stroke_count !== 'number') return false;
  if (typeof session.stroke_rate !== 'number') return false;
  if (!['increasing', 'stable', 'decreasing'].includes(session.stroke_rate_trend as string)) return false;
  if (typeof session.estimated_distance_m !== 'number') return false;

  // Validate system fields
  if (typeof system.is_swimming !== 'boolean') return false;
  if (typeof system.pose_detected !== 'boolean') return false;
  if (!['idle', 'listening', 'speaking'].includes(system.voice_state as string)) return false;

  return true;
}
