import { useState, useEffect } from 'react';
import { VoiceIndicator } from '../components/VoiceIndicator';

interface StandbyLayoutProps {
  voiceState?: 'idle' | 'listening' | 'speaking';
}

export function StandbyLayout({ voiceState = 'idle' }: StandbyLayoutProps) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => {
      setTime(new Date());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const formattedTime = time.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  });

  return (
    <div className="h-screen flex flex-col items-center justify-center bg-slate-900 text-white p-8">
      <div data-testid="clock" className="text-large font-mono mb-8">
        {formattedTime}
      </div>

      <div className="text-medium text-muted mb-8">
        Ready to swim
      </div>

      <div className="absolute bottom-8 right-8">
        <VoiceIndicator status={voiceState} />
      </div>
    </div>
  );
}
