import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StrokeRate } from '../StrokeRate';

describe('StrokeRate', () => {
  // Test 1: Displays rate value
  it('displays stroke rate', () => {
    render(<StrokeRate rate={54} trend="stable" />);
    expect(screen.getByText('54')).toBeInTheDocument();
  });

  // Test 2: Shows /min label
  it('shows per minute label', () => {
    render(<StrokeRate rate={54} trend="stable" />);
    expect(screen.getByText('/min')).toBeInTheDocument();
  });

  // Test 3: Shows trend arrow
  it('displays trend arrow', () => {
    render(<StrokeRate rate={54} trend="increasing" />);
    expect(screen.getByText('↑')).toBeInTheDocument();
  });

  // Test 4: Has large font for poolside visibility
  it('uses large font size', () => {
    render(<StrokeRate rate={54} trend="stable" />);
    const rateElement = screen.getByText('54');
    expect(rateElement).toHaveClass('text-giant');
  });

  // Test 5: Handles zero rate
  it('displays zero rate', () => {
    render(<StrokeRate rate={0} trend="stable" />);
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  // Additional trend tests
  it('displays stable trend arrow', () => {
    render(<StrokeRate rate={54} trend="stable" />);
    expect(screen.getByText('↔')).toBeInTheDocument();
  });

  it('displays decreasing trend arrow', () => {
    render(<StrokeRate rate={54} trend="decreasing" />);
    expect(screen.getByText('↓')).toBeInTheDocument();
  });

  it('rounds decimal rates', () => {
    render(<StrokeRate rate={54.7} trend="stable" />);
    expect(screen.getByText('55')).toBeInTheDocument();
  });
});
