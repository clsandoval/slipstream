interface RateDataPoint {
  timestamp: number;
  rate: number;
}

interface RateGraphProps {
  history: RateDataPoint[];
}

export function RateGraph({ history }: RateGraphProps) {
  if (history.length === 0) {
    return (
      <div className="w-full h-16 flex items-center justify-center text-muted">
        No data
      </div>
    );
  }

  // Calculate SVG path for sparkline
  const width = 100;
  const height = 40;
  const padding = 2;

  const rates = history.map(d => d.rate);
  const minRate = Math.min(...rates);
  const maxRate = Math.max(...rates);
  const range = maxRate - minRate || 1; // Avoid division by zero

  const points = history.map((d, i) => {
    const x = padding + ((width - 2 * padding) * i) / Math.max(history.length - 1, 1);
    const y = height - padding - ((d.rate - minRate) / range) * (height - 2 * padding);
    return `${x},${y}`;
  });

  const pathD = `M ${points.join(' L ')}`;

  return (
    <svg
      role="img"
      aria-label="rate graph"
      width="100%"
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className="stroke-accent"
    >
      <path
        d={pathD}
        fill="none"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
