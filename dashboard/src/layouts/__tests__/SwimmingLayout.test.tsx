import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SwimmingLayout } from '../SwimmingLayout';
import { mockSwimmingState } from '../../mocks/state';

describe('SwimmingLayout', () => {
  // Test 1: Shows giant stroke rate
  it('displays stroke rate prominently', () => {
    render(<SwimmingLayout state={mockSwimmingState()} />);
    expect(screen.getByText('54')).toBeInTheDocument();
  });

  // Test 2: Shows session timer
  it('displays session timer', () => {
    render(<SwimmingLayout state={mockSwimmingState()} />);
    expect(screen.getByText('5:00')).toBeInTheDocument();
  });

  // Test 3: Shows voice indicator
  it('displays voice indicator', () => {
    render(<SwimmingLayout state={mockSwimmingState()} />);
    expect(screen.getByText('Listening')).toBeInTheDocument();
  });

  // Test 4: Minimal layout (few elements)
  it('has minimal layout', () => {
    const { container } = render(<SwimmingLayout state={mockSwimmingState()} />);
    // Should have limited number of main sections
    const sections = container.querySelectorAll('[data-section]');
    expect(sections.length).toBeLessThanOrEqual(4);
  });

  // Test 5: Rate graph visible
  it('shows rate sparkline', () => {
    render(<SwimmingLayout state={mockSwimmingState()} />);
    // Graph shows "No data" when history is empty
    expect(screen.getByText('No data')).toBeInTheDocument();
  });

  // Test 6: Shows trend arrow
  it('displays trend arrow', () => {
    render(<SwimmingLayout state={mockSwimmingState()} />);
    expect(screen.getByText('↔')).toBeInTheDocument(); // stable trend
  });
});
