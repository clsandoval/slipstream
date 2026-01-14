import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SummaryLayout } from '../SummaryLayout';
import { mockRestingState } from '../../mocks/state';

describe('SummaryLayout', () => {
  // Test 1: Shows session complete message
  it('displays session complete message', () => {
    render(<SummaryLayout state={mockRestingState()} />);
    expect(screen.getByText('Session Complete')).toBeInTheDocument();
  });

  // Test 2: Shows duration
  it('displays duration', () => {
    render(<SummaryLayout state={mockRestingState()} />);
    expect(screen.getByText('Duration')).toBeInTheDocument();
  });

  // Test 3: Shows distance
  it('displays distance', () => {
    render(<SummaryLayout state={mockRestingState()} />);
    expect(screen.getByText('Distance')).toBeInTheDocument();
  });

  // Test 4: Shows stroke count
  it('displays stroke count', () => {
    render(<SummaryLayout state={mockRestingState()} />);
    expect(screen.getByText('Strokes')).toBeInTheDocument();
    expect(screen.getByText('180')).toBeInTheDocument(); // from mockRestingState
  });

  // Test 5: Shows average rate
  it('displays average rate', () => {
    render(<SummaryLayout state={mockRestingState()} />);
    expect(screen.getByText('Avg Rate')).toBeInTheDocument();
  });
});
