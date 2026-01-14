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
    expect(screen.getByText('Est. Distance')).toBeInTheDocument();
  });

  // Test 3: Shows tilde for estimate
  it('shows tilde prefix', () => {
    render(<DistanceEstimate distance="500m" showTilde />);
    expect(screen.getByText('~500m')).toBeInTheDocument();
  });

  // Test 4: Label hidden by default
  it('hides label by default', () => {
    render(<DistanceEstimate distance="500m" />);
    expect(screen.queryByText('Est. Distance')).not.toBeInTheDocument();
  });

  // Test 5: Tilde hidden by default
  it('hides tilde by default', () => {
    render(<DistanceEstimate distance="500m" />);
    expect(screen.getByText('500m')).toBeInTheDocument();
    expect(screen.queryByText('~500m')).not.toBeInTheDocument();
  });

  // Test 6: Uses monospace font
  it('uses monospace font', () => {
    render(<DistanceEstimate distance="500m" />);
    const distanceElement = screen.getByText('500m');
    expect(distanceElement).toHaveClass('font-mono');
  });
});
