import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RestingLayout } from '../RestingLayout';
import { mockRestingState } from '../../mocks/state';

describe('RestingLayout', () => {
  // Test 1: Shows session timer
  it('displays session timer with label', () => {
    render(<RestingLayout state={mockRestingState()} />);
    expect(screen.getByText('Session Time')).toBeInTheDocument();
  });

  // Test 2: Shows rest timer (placeholder for workout integration)
  it('has rest timer section', () => {
    render(<RestingLayout state={mockRestingState()} />);
    expect(screen.getByTestId('rest-timer')).toBeInTheDocument();
  });

  // Test 3: Shows last interval summary
  it('displays last interval section', () => {
    render(<RestingLayout state={mockRestingState()} />);
    expect(screen.getByText('Last Interval')).toBeInTheDocument();
  });

  // Test 4: Shows rate graph
  it('displays session rate graph', () => {
    render(<RestingLayout state={mockRestingState()} />);
    // Graph shows "No data" when history is empty
    expect(screen.getByText('No data')).toBeInTheDocument();
  });

  // Test 5: Shows coach message area
  it('has coach message section', () => {
    render(<RestingLayout state={mockRestingState()} />);
    expect(screen.getByTestId('coach-message')).toBeInTheDocument();
  });

  // Test 6: Shows voice indicator
  it('displays voice indicator', () => {
    render(<RestingLayout state={mockRestingState()} />);
    expect(screen.getByText('Listening')).toBeInTheDocument();
  });

  // Test 7: More detail than swimming layout
  it('has expanded layout', () => {
    const { container } = render(<RestingLayout state={mockRestingState()} />);
    const sections = container.querySelectorAll('[data-section]');
    expect(sections.length).toBeGreaterThan(4);
  });

  // Test 8: Shows custom coach message
  it('displays custom coach message', () => {
    render(<RestingLayout state={mockRestingState()} coachMessage="Great job!" />);
    expect(screen.getByText('Great job!')).toBeInTheDocument();
  });

  // Test 9: Shows default coach message
  it('displays default coach message when none provided', () => {
    render(<RestingLayout state={mockRestingState()} />);
    expect(screen.getByText('Ready when you are!')).toBeInTheDocument();
  });
});
