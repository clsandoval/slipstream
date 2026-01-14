import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { App } from '../App';
import { Server } from 'mock-socket';
import { mockSwimmingState, mockRestingState, mockStandbyState } from '../mocks/state';

describe('App', () => {
  let server: Server;

  beforeEach(() => {
    server = new Server('ws://localhost:8765');
  });

  afterEach(() => {
    server.close();
  });

  // Test 1: Shows sleeping layout on no connection
  it('shows sleeping layout when disconnected', async () => {
    server.close();
    render(<App />);
    // Before connection established, should show sleeping
    await waitFor(() => {
      expect(screen.getByTestId('sleeping-layout')).toBeInTheDocument();
    });
  });

  // Test 2: Shows standby after connection without session
  it('shows standby layout when connected without session', async () => {
    render(<App />);

    await waitFor(() => {
      // Server is ready
    }, { timeout: 1000 });

    act(() => {
      server.emit('message', JSON.stringify(mockStandbyState()));
    });

    await waitFor(() => {
      expect(screen.getByText(/ready to swim/i)).toBeInTheDocument();
    });
  });

  // Test 3: Shows swimming layout when swimming
  it('shows swimming layout when session active and swimming', async () => {
    render(<App />);

    await waitFor(() => {
      // Server is ready
    }, { timeout: 1000 });

    act(() => {
      server.emit('message', JSON.stringify(mockSwimmingState()));
    });

    await waitFor(() => {
      expect(screen.getByTestId('swimming-layout')).toBeInTheDocument();
    });
  });

  // Test 4: Shows resting layout when not swimming
  it('shows resting layout when session active but not swimming', async () => {
    render(<App />);

    await waitFor(() => {
      // Server is ready
    }, { timeout: 1000 });

    act(() => {
      server.emit('message', JSON.stringify(mockRestingState()));
    });

    await waitFor(() => {
      expect(screen.getByTestId('resting-layout')).toBeInTheDocument();
    });
  });

  // Test 5: Transitions between layouts smoothly
  it('transitions from swimming to resting', async () => {
    render(<App />);

    await waitFor(() => {
      // Server is ready
    }, { timeout: 1000 });

    act(() => {
      server.emit('message', JSON.stringify(mockSwimmingState()));
    });

    await waitFor(() => {
      expect(screen.getByTestId('swimming-layout')).toBeInTheDocument();
    });

    act(() => {
      server.emit('message', JSON.stringify(mockRestingState()));
    });

    await waitFor(() => {
      expect(screen.getByTestId('resting-layout')).toBeInTheDocument();
    });
  });

  // Test 6: Has dark theme
  it('uses dark theme', () => {
    render(<App />);
    const darkContainer = document.querySelector('.dark');
    expect(darkContainer).toBeInTheDocument();
  });

  // Test 7: Shows connection status indicator
  it('shows connection status when disconnected', async () => {
    render(<App />);

    await waitFor(() => {
      // Wait for initial connection
    }, { timeout: 1000 });

    act(() => {
      server.close();
    });

    await waitFor(() => {
      expect(screen.getByText(/disconnected/i)).toBeInTheDocument();
    });
  });
});
