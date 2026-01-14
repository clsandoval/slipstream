import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RateGraph } from '../RateGraph';

describe('RateGraph', () => {
  const mockHistory = [
    { timestamp: 1, rate: 50 },
    { timestamp: 2, rate: 52 },
    { timestamp: 3, rate: 54 },
    { timestamp: 4, rate: 53 },
    { timestamp: 5, rate: 55 },
  ];

  // Test 1: Renders SVG sparkline
  it('renders sparkline SVG', () => {
    render(<RateGraph history={mockHistory} />);
    expect(screen.getByRole('img', { name: /rate graph/i })).toBeInTheDocument();
  });

  // Test 2: Handles empty history
  it('renders placeholder for empty history', () => {
    render(<RateGraph history={[]} />);
    expect(screen.getByText('No data')).toBeInTheDocument();
  });

  // Test 3: Handles single data point
  it('renders with single point', () => {
    render(<RateGraph history={[{ timestamp: 1, rate: 50 }]} />);
    expect(screen.getByRole('img')).toBeInTheDocument();
  });

  // Test 4: Scales to container
  it('fills container width', () => {
    const { container } = render(<RateGraph history={mockHistory} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', '100%');
  });

  // Test 5: Has correct aria label
  it('has accessible aria label', () => {
    render(<RateGraph history={mockHistory} />);
    const svg = screen.getByRole('img');
    expect(svg).toHaveAttribute('aria-label', 'rate graph');
  });
});
