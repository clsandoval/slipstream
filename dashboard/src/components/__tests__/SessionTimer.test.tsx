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
    expect(screen.getByText('Session Time')).toBeInTheDocument();
  });

  // Test 3: Large font for visibility
  it('uses large font', () => {
    render(<SessionTimer time="14:32" />);
    const timeElement = screen.getByText('14:32');
    expect(timeElement).toHaveClass('text-large');
  });

  // Test 4: Label hidden by default
  it('hides label by default', () => {
    render(<SessionTimer time="14:32" />);
    expect(screen.queryByText('Session Time')).not.toBeInTheDocument();
  });

  // Test 5: Uses monospace font
  it('uses monospace font', () => {
    render(<SessionTimer time="14:32" />);
    const timeElement = screen.getByText('14:32');
    expect(timeElement).toHaveClass('font-mono');
  });
});
