import { useState, useEffect } from 'react';

export function SleepingLayout() {
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
    <div className="h-screen flex flex-col items-center justify-center bg-black text-white">
      <div data-testid="clock" className="text-large font-mono text-muted">
        {formattedTime}
      </div>
    </div>
  );
}
