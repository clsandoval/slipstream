import type { StateUpdate } from '../types/state';
import { SessionTimer } from '../components/SessionTimer';
import { RateGraph } from '../components/RateGraph';
import { VoiceIndicator } from '../components/VoiceIndicator';
import { useSystemState } from '../hooks/useSystemState';

interface RestingLayoutProps {
  state: StateUpdate;
  coachMessage?: string;
}

export function RestingLayout({ state, coachMessage }: RestingLayoutProps) {
  const { formattedTime, formattedDistance } = useSystemState(state);

  return (
    <div className="h-screen bg-slate-900 text-white p-8">
      {/* Header row */}
      <div className="flex justify-between mb-8">
        <div data-section="timer">
          <SessionTimer time={formattedTime} showLabel />
        </div>
        <div data-section="rest" data-testid="rest-timer">
          <div className="text-large">REST</div>
          <div className="text-muted">0:45 remaining</div>
        </div>
      </div>

      {/* Two-column content */}
      <div className="grid grid-cols-2 gap-8 mb-8">
        <div data-section="last-interval">
          <h3 className="text-sm uppercase text-muted mb-2">Last Interval</h3>
          <div>Avg: {state.session.stroke_rate} /min</div>
          <div>Est: {formattedDistance}</div>
          <div>Strokes: {state.session.stroke_count}</div>
        </div>
        <div data-section="next-up">
          <h3 className="text-sm uppercase text-muted mb-2">Next Up</h3>
          <div>INTERVAL 2 of 4</div>
          <div>4:00 duration</div>
        </div>
      </div>

      {/* Rate graph */}
      <div data-section="graph" className="mb-8">
        <RateGraph history={[]} />
      </div>

      {/* Coach message */}
      <div data-section="coach" data-testid="coach-message" className="p-4 bg-slate-800 rounded mb-4">
        <span className="text-muted">COACH: </span>
        <span>{coachMessage || "Ready when you are!"}</span>
      </div>

      {/* Voice indicator */}
      <div data-section="voice">
        <VoiceIndicator status={state.system.voice_state} />
      </div>
    </div>
  );
}
