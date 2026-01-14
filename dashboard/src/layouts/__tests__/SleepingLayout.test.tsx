import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SleepingLayout } from '../SleepingLayout';

describe('SleepingLayout', () => {
  // Test 1: Shows clock only
  it('displays clock', () => {
    render(<SleepingLayout />);
    expect(screen.getByTestId('clock')).toBeInTheDocument();
  });

  // Test 2: Minimal content
  it('has minimal content', () => {
    const { container } = render(<SleepingLayout />);
    // Should be very sparse - just the clock
    expect(container.textContent?.length).toBeLessThan(100);
  });

  // Test 3: Dark/ambient styling
  it('has ambient dark styling', () => {
    const { container } = render(<SleepingLayout />);
    expect(container.firstChild).toHaveClass('bg-black');
  });

  // Test 4: Clock shows time format
  it('shows time in clock', () => {
    render(<SleepingLayout />);
    const clock = screen.getByTestId('clock');
    // Should contain colon for time format (HH:MM)
    expect(clock.textContent).toMatch(/\d{1,2}:\d{2}/);
  });
});
