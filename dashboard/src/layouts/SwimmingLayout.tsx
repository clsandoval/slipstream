import type { StateUpdate } from '../types/state';
import { RateGraph } from '../components/RateGraph';
import { VoiceIndicator } from '../components/VoiceIndicator';
import { useSystemState } from '../hooks/useSystemState';

interface RateDataPoint {
  timestamp: number;
  rate: number;
}

interface SwimmingLayoutProps {
  state: StateUpdate;
  rateHistory?: RateDataPoint[];
}

const trendArrows: Record<string, string> = {
  increasing: '↑',
  stable: '→',
  decreasing: '↓',
};

const trendColors: Record<string, string> = {
  increasing: 'text-green-400',
  stable: 'text-slate-400',
  decreasing: 'text-amber-400',
};

export function SwimmingLayout({ state, rateHistory = [] }: SwimmingLayoutProps) {
  const { formattedTime, formattedDistance } = useSystemState(state);

  return (
    <div className="h-screen bg-slate-900 text-white flex flex-col items-center justify-center relative">
      {/* Timer - top */}
      <div data-section="timer" className="absolute top-8 left-8">
        <div className="text-5xl font-mono font-bold">{formattedTime}</div>
        <div className="text-muted text-sm uppercase tracking-wider mt-1">Session</div>
      </div>

      {/* Stroke count - top right */}
      <div className="absolute top-8 right-8 text-right">
        <div className="text-4xl font-mono font-bold">{state.session.stroke_count}</div>
        <div className="text-muted text-sm uppercase tracking-wider mt-1">Strokes</div>
      </div>

      {/* Giant stroke rate - center */}
      <div data-section="rate" className="flex items-baseline gap-4 mb-8">
        <span className="text-[10rem] font-bold font-mono leading-none">
          {Math.round(state.session.stroke_rate)}
        </span>
        <div className="flex flex-col">
          <span className="text-4xl text-muted">/min</span>
          <span className={`text-4xl ${trendColors[state.session.stroke_rate_trend]}`}>
            {trendArrows[state.session.stroke_rate_trend]}
          </span>
        </div>
      </div>

      {/* Distance estimate */}
      <div className="text-2xl text-muted mb-8">
        ~{formattedDistance}
      </div>

      {/* Sparkline - bottom center */}
      <div data-section="graph" className="w-full max-w-2xl px-8 mb-8">
        <div className="bg-slate-800/50 rounded-xl p-4">
          <div className="h-16">
            <RateGraph history={rateHistory} />
          </div>
        </div>
      </div>

      {/* Voice indicator - bottom right */}
      <div data-section="voice" className="absolute bottom-8 right-8">
        <VoiceIndicator status={state.system.voice_state} />
      </div>
    </div>
  );
}
