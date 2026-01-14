interface StrokeRateProps {
  rate: number;
  trend: 'increasing' | 'stable' | 'decreasing';
}

const trendArrows = {
  increasing: '↑',
  stable: '↔',
  decreasing: '↓',
};

export function StrokeRate({ rate, trend }: StrokeRateProps) {
  return (
    <div className="flex items-center justify-center gap-4">
      <span className="text-giant font-bold">{Math.round(rate)}</span>
      <div className="flex flex-col items-start">
        <span className="text-large text-muted">/min</span>
        <span className="text-large">{trendArrows[trend]}</span>
      </div>
    </div>
  );
}
