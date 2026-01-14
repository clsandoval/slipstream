interface DistanceEstimateProps {
  distance: string;
  showLabel?: boolean;
  showTilde?: boolean;
}

export function DistanceEstimate({ distance, showLabel = false, showTilde = false }: DistanceEstimateProps) {
  return (
    <div className="text-center">
      <div className="text-large font-mono">
        {showTilde && '~'}{distance}
      </div>
      {showLabel && <div className="text-sm text-muted uppercase">Est. Distance</div>}
    </div>
  );
}
