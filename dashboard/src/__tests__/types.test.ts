import { describe, it, expect } from 'vitest';
import { isValidStateUpdate, parseStateUpdate } from '../types/state';
import { mockStateUpdate, mockSwimmingState, mockRestingState } from '../mocks/state';

describe('StateUpdate Types', () => {
  // Test 1: Valid state update parses correctly
  it('parses valid state update JSON', () => {
    const json = JSON.stringify(mockStateUpdate());
    const result = parseStateUpdate(json);
    expect(result).toBeDefined();
    expect(result?.type).toBe('state_update');
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

  // Additional edge case tests
  it('rejects null data', () => {
    expect(isValidStateUpdate(null)).toBe(false);
  });

  it('rejects non-object data', () => {
    expect(isValidStateUpdate('string')).toBe(false);
    expect(isValidStateUpdate(123)).toBe(false);
  });

  it('rejects wrong type field', () => {
    const invalid = { ...mockStateUpdate(), type: 'wrong_type' };
    expect(isValidStateUpdate(invalid)).toBe(false);
  });
});
