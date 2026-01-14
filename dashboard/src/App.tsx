import { useRef, useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { useSystemState } from './hooks/useSystemState';
import { SleepingLayout } from './layouts/SleepingLayout';
import { StandbyLayout } from './layouts/StandbyLayout';
import { SwimmingLayout } from './layouts/SwimmingLayout';
import { RestingLayout } from './layouts/RestingLayout';
import { SummaryLayout } from './layouts/SummaryLayout';
import './index.css';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8765';
const MAX_HISTORY_POINTS = 50;

interface RateDataPoint {
  timestamp: number;
  rate: number;
}

export function App() {
  const { state, connectionStatus } = useWebSocket(WS_URL);
  const { layoutState } = useSystemState(state);
  const rateHistoryRef = useRef<RateDataPoint[]>([]);

  // Track rate history
  useEffect(() => {
    if (state && state.session.active && state.system.is_swimming && state.session.stroke_rate > 0) {
      const newPoint: RateDataPoint = {
        timestamp: Date.now(),
        rate: state.session.stroke_rate,
      };

      rateHistoryRef.current = [
        ...rateHistoryRef.current.slice(-MAX_HISTORY_POINTS + 1),
        newPoint,
      ];
    }
  }, [state]);

  // Clear history when session ends
  useEffect(() => {
    if (!state?.session.active) {
      rateHistoryRef.current = [];
    }
  }, [state?.session.active]);

  const rateHistory = rateHistoryRef.current;

  return (
    <div className="dark">
      {/* Connection status overlay */}
      {connectionStatus === 'disconnected' && (
        <div className="absolute top-4 left-4 bg-red-500 text-white px-3 py-1 rounded z-50">
          Disconnected
        </div>
      )}

      {/* Layout router */}
      {layoutState === 'SLEEPING' && (
        <div data-testid="sleeping-layout">
          <SleepingLayout />
        </div>
      )}

      {layoutState === 'STANDBY' && state && (
        <div data-testid="standby-layout">
          <StandbyLayout voiceState={state.system.voice_state} />
        </div>
      )}

      {layoutState === 'SWIMMING' && state && (
        <div data-testid="swimming-layout">
          <SwimmingLayout state={state} rateHistory={rateHistory} />
        </div>
      )}

      {layoutState === 'RESTING' && state && (
        <div data-testid="resting-layout">
          <RestingLayout state={state} rateHistory={rateHistory} />
        </div>
      )}

      {layoutState === 'SUMMARY' && state && (
        <div data-testid="summary-layout">
          <SummaryLayout state={state} />
        </div>
      )}
    </div>
  );
}

export default App;
