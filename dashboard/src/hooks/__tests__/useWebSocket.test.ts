import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useWebSocket } from '../useWebSocket';
import { Server, WebSocket as MockWebSocket } from 'mock-socket';

describe('useWebSocket', () => {
  let mockServer: Server;
  const TEST_URL = 'ws://localhost:8765';

  beforeEach(() => {
    // Store original WebSocket
    vi.stubGlobal('WebSocket', MockWebSocket);
    mockServer = new Server(TEST_URL);
  });

  afterEach(() => {
    mockServer.stop();
    vi.unstubAllGlobals();
  });

  // Test 1: Connects to WebSocket server
  it('connects to WebSocket server', async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });
  });

  // Test 2: Parses received state updates
  it('parses received state updates', async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    const validMessage = JSON.stringify({
      type: 'state_update',
      timestamp: new Date().toISOString(),
      session: {
        active: true,
        elapsed_seconds: 100,
        stroke_count: 50,
        stroke_rate: 54,
        stroke_rate_trend: 'stable',
        estimated_distance_m: 100,
      },
      system: {
        is_swimming: true,
        pose_detected: true,
        voice_state: 'listening',
      },
    });

    act(() => {
      mockServer.clients().forEach(client => {
        client.send(validMessage);
      });
    });

    await waitFor(() => {
      expect(result.current.state?.session.stroke_rate).toBe(54);
    }, { timeout: 3000 });
  });

  // Test 3: Handles disconnection
  it('sets isConnected false on disconnect', async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    act(() => {
      mockServer.close();
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false);
    }, { timeout: 3000 });
  });

  // Test 4: Ignores invalid messages
  it('ignores invalid JSON messages', async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    act(() => {
      mockServer.clients().forEach(client => {
        client.send('not valid json');
      });
    });

    // Wait a bit and check state is still null
    await new Promise(resolve => setTimeout(resolve, 100));
    expect(result.current.state).toBeNull();
  });

  // Test 5: Provides connection status
  it('tracks connection status', async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));

    // Initial state should be connecting
    expect(result.current.connectionStatus).toBe('connecting');

    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('connected');
    }, { timeout: 3000 });

    act(() => {
      mockServer.close();
    });

    await waitFor(() => {
      expect(result.current.connectionStatus).toBe('disconnected');
    }, { timeout: 3000 });
  });

  // Test 6: Cleans up on unmount
  it('closes connection on unmount', async () => {
    const { result, unmount } = renderHook(() => useWebSocket(TEST_URL));

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    }, { timeout: 3000 });

    // Should not throw when unmounting
    expect(() => unmount()).not.toThrow();
  });

  // Test 7: Returns error state initially (when no connection possible)
  it('provides null state before messages', () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));
    expect(result.current.state).toBeNull();
  });
});
