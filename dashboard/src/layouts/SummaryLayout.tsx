import type { StateUpdate } from '../types/state';
import { useSystemState } from '../hooks/useSystemState';

interface SummaryLayoutProps {
  state: StateUpdate;
}

export function SummaryLayout({ state }: SummaryLayoutProps) {
  const { formattedTime, formattedDistance } = useSystemState(state);

  return (
    <div className="h-screen bg-slate-900 text-white p-8 flex flex-col items-center justify-center">
      <h1 className="text-large mb-8">Session Complete</h1>

      <div className="grid grid-cols-2 gap-8 text-center">
        <div>
          <div className="text-muted uppercase text-sm mb-2">Duration</div>
          <div className="text-medium font-mono">{formattedTime}</div>
        </div>
        <div>
          <div className="text-muted uppercase text-sm mb-2">Distance</div>
          <div className="text-medium font-mono">{formattedDistance}</div>
        </div>
        <div>
          <div className="text-muted uppercase text-sm mb-2">Strokes</div>
          <div className="text-medium font-mono">{state.session.stroke_count}</div>
        </div>
        <div>
          <div className="text-muted uppercase text-sm mb-2">Avg Rate</div>
          <div className="text-medium font-mono">{state.session.stroke_rate}/min</div>
        </div>
      </div>
    </div>
  );
}
