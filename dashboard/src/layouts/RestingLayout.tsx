import { useRef, useEffect } from 'react';
import type { StateUpdate } from '../types/state';
import { RateGraph } from '../components/RateGraph';
import { VoiceIndicator } from '../components/VoiceIndicator';
import { useSystemState } from '../hooks/useSystemState';

interface RateDataPoint {
  timestamp: number;
  rate: number;
}

interface TranscriptionEntry {
  text: string;
  timestamp: string;
}

interface RestingLayoutProps {
  state: StateUpdate;
  coachMessage?: string;
  rateHistory?: RateDataPoint[];
}

export function RestingLayout({ state, coachMessage, rateHistory = [] }: RestingLayoutProps) {
  const { formattedTime, formattedDistance } = useSystemState(state);
  const transcriptionLogRef = useRef<TranscriptionEntry[]>([]);
  const lastSeenTranscription = useRef<string>('');

  // Track transcriptions
  useEffect(() => {
    if (state.system.last_transcription &&
        state.system.last_transcription !== lastSeenTranscription.current) {
      lastSeenTranscription.current = state.system.last_transcription;
      transcriptionLogRef.current = [
        ...transcriptionLogRef.current.slice(-4), // Keep last 5
        {
          text: state.system.last_transcription,
          timestamp: state.system.transcription_timestamp || new Date().toISOString(),
        },
      ];
    }
  }, [state.system.last_transcription, state.system.transcription_timestamp]);

  const transcriptionLog = transcriptionLogRef.current;

  return (
    <div className="h-screen bg-slate-900 text-white flex flex-col">
      {/* Header - Session time and REST indicator */}
      <div className="flex justify-between items-start p-8 pb-4">
        <div data-section="timer">
          <div className="text-6xl font-mono font-bold">{formattedTime}</div>
          <div className="text-muted text-lg uppercase tracking-wider mt-1">Session</div>
        </div>
        <div data-section="rest" data-testid="rest-timer" className="text-right">
          <div className="text-5xl font-bold text-green-400">REST</div>
          <div className="text-muted text-lg mt-1">Take a breather</div>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 px-8 py-4 grid grid-cols-3 gap-6">
        {/* Left column - Stats */}
        <div className="space-y-4">
          <div className="bg-slate-800 rounded-xl p-5">
            <div className="text-muted text-sm uppercase tracking-wider mb-2">Strokes</div>
            <div className="text-4xl font-mono font-bold">{state.session.stroke_count}</div>
          </div>
          <div className="bg-slate-800 rounded-xl p-5">
            <div className="text-muted text-sm uppercase tracking-wider mb-2">Distance</div>
            <div className="text-4xl font-mono font-bold">{formattedDistance}</div>
          </div>
          <div className="bg-slate-800 rounded-xl p-5">
            <div className="text-muted text-sm uppercase tracking-wider mb-2">Avg Rate</div>
            <div className="text-3xl font-mono font-bold">
              {rateHistory.length > 0
                ? Math.round(rateHistory.reduce((sum, p) => sum + p.rate, 0) / rateHistory.length)
                : state.session.stroke_rate}
              <span className="text-xl text-muted">/min</span>
            </div>
          </div>
        </div>

        {/* Center column - Graph and Coach */}
        <div className="space-y-4">
          <div className="bg-slate-800 rounded-xl p-5">
            <div className="text-muted text-sm uppercase tracking-wider mb-3">Session Rate</div>
            <div className="h-20">
              <RateGraph history={rateHistory} />
            </div>
          </div>

          {/* Coach message */}
          <div data-section="coach" data-testid="coach-message" className="bg-slate-800/50 rounded-xl p-5 border border-slate-700 flex-1">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
              <span className="text-sky-400 font-medium text-sm uppercase">Coach</span>
            </div>
            <p className="text-xl">{coachMessage || "Great work! Ready when you are."}</p>
          </div>
        </div>

        {/* Right column - Transcription Log */}
        <div className="bg-slate-800 rounded-xl p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-4">
            <div className={`w-2 h-2 rounded-full ${state.system.voice_state === 'listening' ? 'bg-green-400 animate-pulse' : 'bg-slate-600'}`} />
            <span className="text-muted text-sm uppercase tracking-wider">Voice Log</span>
          </div>

          <div className="flex-1 space-y-3 overflow-hidden">
            {transcriptionLog.length === 0 ? (
              <div className="text-muted text-sm italic">Waiting for voice input...</div>
            ) : (
              transcriptionLog.map((entry, i) => (
                <div
                  key={entry.timestamp + i}
                  className={`p-3 rounded-lg ${i === transcriptionLog.length - 1 ? 'bg-slate-700' : 'bg-slate-700/50'}`}
                >
                  <div className="text-sm text-muted mb-1">
                    {new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </div>
                  <div className={`${i === transcriptionLog.length - 1 ? 'text-white' : 'text-slate-400'}`}>
                    "{entry.text}"
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Footer - Voice indicator */}
      <div data-section="voice" className="p-8 pt-4 flex justify-end">
        <VoiceIndicator status={state.system.voice_state} />
      </div>
    </div>
  );
}
