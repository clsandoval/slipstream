import { useWebSocket } from './hooks/useWebSocket';
import { useSystemState } from './hooks/useSystemState';
import { SleepingLayout } from './layouts/SleepingLayout';
import { StandbyLayout } from './layouts/StandbyLayout';
import { SwimmingLayout } from './layouts/SwimmingLayout';
import { RestingLayout } from './layouts/RestingLayout';
import { SummaryLayout } from './layouts/SummaryLayout';
import './index.css';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8765';

export function App() {
  const { state, connectionStatus } = useWebSocket(WS_URL);
  const { layoutState } = useSystemState(state);

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
          <SwimmingLayout state={state} />
        </div>
      )}

      {layoutState === 'RESTING' && state && (
        <div data-testid="resting-layout">
          <RestingLayout state={state} />
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
