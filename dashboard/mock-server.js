import { WebSocketServer } from 'ws';

const wss = new WebSocketServer({ port: 8765 });

console.log('Mock WebSocket server running on ws://localhost:8765');

let isSwimming = true;
let elapsedSeconds = 0;
let strokeCount = 0;
let tickCount = 0;

wss.on('connection', (ws) => {
  console.log('Client connected');

  const interval = setInterval(() => {
    tickCount++;
    // Only increment seconds every 4 ticks (250ms * 4 = 1 second)
    if (tickCount % 4 === 0) {
      elapsedSeconds += 1;
    }

    // Toggle swimming/resting every 30 seconds (only on the exact tick)
    if (elapsedSeconds > 0 && elapsedSeconds % 30 === 0 && tickCount % 4 === 0) {
      isSwimming = !isSwimming;
      console.log(isSwimming ? 'Swimming...' : 'Resting...');
    }

    if (isSwimming) {
      strokeCount += Math.random() > 0.5 ? 1 : 0;
    }

    const strokeRate = isSwimming ? 48 + Math.floor(Math.random() * 12) : 0;

    const state = {
      type: 'state_update',
      timestamp: new Date().toISOString(),
      session: {
        active: true,
        elapsed_seconds: elapsedSeconds,
        stroke_count: strokeCount,
        stroke_rate: strokeRate,
        stroke_rate_trend: ['increasing', 'stable', 'decreasing'][Math.floor(Math.random() * 3)],
        estimated_distance_m: strokeCount * 1.8,
      },
      system: {
        is_swimming: isSwimming,
        pose_detected: true,
        voice_state: 'listening',
      },
    };

    ws.send(JSON.stringify(state));
  }, 250);

  ws.on('close', () => {
    console.log('Client disconnected');
    clearInterval(interval);
  });
});
