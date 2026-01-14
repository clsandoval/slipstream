import type { StateUpdate } from '../types/state';
import { StrokeRate } from '../components/StrokeRate';
import { SessionTimer } from '../components/SessionTimer';
import { RateGraph } from '../components/RateGraph';
import { VoiceIndicator } from '../components/VoiceIndicator';
import { useSystemState } from '../hooks/useSystemState';

interface SwimmingLayoutProps {
  state: StateUpdate;
}

export function SwimmingLayout({ state }: SwimmingLayoutProps) {
  const { formattedTime } = useSystemState(state);

  return (
    <div className="h-screen flex flex-col items-center justify-center bg-slate-900 text-white p-8 relative">
      {/* Timer - top */}
      <div data-section="timer" className="mb-8">
        <SessionTimer time={formattedTime} />
      </div>

      {/* Giant stroke rate - center */}
      <div data-section="rate" className="mb-8">
        <StrokeRate
          rate={state.session.stroke_rate}
          trend={state.session.stroke_rate_trend}
        />
      </div>

      {/* Sparkline - bottom center */}
      <div data-section="graph" className="w-full max-w-xl mb-8">
        <RateGraph history={[]} /> {/* Will be connected to rate history */}
      </div>

      {/* Voice indicator - bottom right */}
      <div data-section="voice" className="absolute bottom-8 right-8">
        <VoiceIndicator status={state.system.voice_state} />
      </div>
    </div>
  );
}
