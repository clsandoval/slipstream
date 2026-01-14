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

  // Test 4: Default voice state is idle
  it('defaults to idle voice state', () => {
    render(<StandbyLayout />);
    expect(screen.getByText('Idle')).toBeInTheDocument();
  });
});
