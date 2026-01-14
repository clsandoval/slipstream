interface SessionTimerProps {
  time: string;
  showLabel?: boolean;
}

export function SessionTimer({ time, showLabel = false }: SessionTimerProps) {
  return (
    <div className="text-center">
      <div className="text-large font-mono">{time}</div>
      {showLabel && <div className="text-sm text-muted uppercase">Session Time</div>}
    </div>
  );
}
