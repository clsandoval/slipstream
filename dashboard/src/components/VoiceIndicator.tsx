interface VoiceIndicatorProps {
  status: 'idle' | 'listening' | 'speaking';
}

const statusConfig = {
  idle: { color: 'bg-gray-500', text: 'Idle', pulse: false },
  listening: { color: 'bg-green-500', text: 'Listening', pulse: true },
  speaking: { color: 'bg-blue-500', text: 'Speaking', pulse: true },
};

export function VoiceIndicator({ status }: VoiceIndicatorProps) {
  const config = statusConfig[status];

  return (
    <div className="flex items-center gap-2">
      <div
        data-testid="voice-dot"
        className={`w-3 h-3 rounded-full ${config.color} ${config.pulse ? 'animate-pulse' : ''}`}
      />
      <span className="text-sm">{config.text}</span>
    </div>
  );
}
