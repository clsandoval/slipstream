import { WebSocketServer } from 'ws';

const wss = new WebSocketServer({ port: 8765 });

console.log('Dashboard Demo Server running on ws://localhost:8765');
console.log('Cycling through all states (5 seconds each)\n');

// State machine
const STATES = ['SLEEPING', 'STANDBY', 'SWIMMING', 'RESTING', 'SUMMARY'];
const STATE_DURATION = 5; // seconds per state

// Mock transcriptions for demo
const MOCK_TRANSCRIPTIONS = [
  "How many strokes was that?",
  "What's my average pace?",
  "That felt good",
  "I need more rest",
  "Start the next interval",
  "How much time left?",
  "What's my stroke count?",
];

let currentStateIndex = 0;
let stateStartTime = Date.now();
let elapsedSeconds = 0;
let strokeCount = 0;
let tickCount = 0;
let lastTranscription = '';
let transcriptionTimestamp = '';
let transcriptionIndex = 0;

function getCurrentState() {
  return STATES[currentStateIndex];
}

function getSecondsInState() {
  return Math.floor((Date.now() - stateStartTime) / 1000);
}

function advanceState() {
  currentStateIndex = (currentStateIndex + 1) % STATES.length;
  stateStartTime = Date.now();

  // Reset session data when starting fresh cycle
  if (currentStateIndex === 0) {
    elapsedSeconds = 0;
    strokeCount = 0;
    lastTranscription = '';
  }

  console.log(`\n→ Switching to: ${getCurrentState()}`);
  console.log(`  (${STATE_DURATION} seconds remaining)`);
}

wss.on('connection', (ws) => {
  console.log('\nClient connected');
  console.log(`Current state: ${getCurrentState()}`);

  const interval = setInterval(() => {
    tickCount++;

    // Check if we should advance to next state
    if (getSecondsInState() >= STATE_DURATION) {
      advanceState();
    }

    const currentState = getCurrentState();
    const secondsRemaining = STATE_DURATION - getSecondsInState();

    // Update elapsed time once per second
    if (tickCount % 4 === 0 && (currentState === 'SWIMMING' || currentState === 'RESTING')) {
      elapsedSeconds++;
    }

    // SLEEPING: Don't send any state updates (connection only)
    if (currentState === 'SLEEPING') {
      // No message sent - dashboard shows sleeping layout
      if (tickCount % 16 === 0) {
        console.log(`  SLEEPING: ${secondsRemaining}s remaining (no data sent)`);
      }
      return;
    }

    // Build state update based on current state
    let sessionActive = false;
    let isSwimming = false;
    let strokeRate = 0;
    let voiceState = 'idle';

    switch (currentState) {
      case 'STANDBY':
        sessionActive = false;
        voiceState = 'listening';
        if (tickCount % 16 === 0) {
          console.log(`  STANDBY: ${secondsRemaining}s remaining`);
        }
        break;

      case 'SWIMMING':
        sessionActive = true;
        isSwimming = true;
        strokeRate = 48 + Math.floor(Math.random() * 12);
        voiceState = 'listening';
        // Accumulate strokes
        if (tickCount % 4 === 0) {
          strokeCount += Math.floor(Math.random() * 2) + 1;
        }
        if (tickCount % 16 === 0) {
          console.log(`  SWIMMING: ${secondsRemaining}s | Rate: ${strokeRate}/min | Strokes: ${strokeCount}`);
        }
        break;

      case 'RESTING':
        sessionActive = true;
        isSwimming = false;
        strokeRate = 0;
        voiceState = 'listening';

        // Add a new transcription every ~2 seconds
        if (tickCount % 8 === 0) {
          lastTranscription = MOCK_TRANSCRIPTIONS[transcriptionIndex % MOCK_TRANSCRIPTIONS.length];
          transcriptionTimestamp = new Date().toISOString();
          transcriptionIndex++;
          console.log(`  💬 "${lastTranscription}"`);
        }

        if (tickCount % 16 === 0) {
          console.log(`  RESTING: ${secondsRemaining}s | Total strokes: ${strokeCount}`);
        }
        break;

      case 'SUMMARY':
        // For summary, we send session ended state
        sessionActive = false; // Session ended
        isSwimming = false;
        strokeRate = Math.floor(strokeCount / (elapsedSeconds / 60) || 52);
        voiceState = 'idle';
        if (tickCount % 16 === 0) {
          console.log(`  SUMMARY: ${secondsRemaining}s | Final: ${strokeCount} strokes, ${elapsedSeconds}s`);
        }
        break;
    }

    const trends = ['increasing', 'stable', 'decreasing'];

    const state = {
      type: 'state_update',
      timestamp: new Date().toISOString(),
      session: {
        active: sessionActive,
        elapsed_seconds: elapsedSeconds,
        stroke_count: strokeCount,
        stroke_rate: strokeRate,
        stroke_rate_trend: trends[Math.floor(Math.random() * 3)],
        estimated_distance_m: strokeCount * 1.8,
      },
      system: {
        is_swimming: isSwimming,
        pose_detected: sessionActive,
        voice_state: voiceState,
        last_transcription: lastTranscription || undefined,
        transcription_timestamp: transcriptionTimestamp || undefined,
      },
    };

    ws.send(JSON.stringify(state));
  }, 250);

  ws.on('close', () => {
    console.log('\nClient disconnected');
    clearInterval(interval);
  });
});

// Initial state announcement
console.log(`Starting with: ${getCurrentState()}`);
console.log(`(${STATE_DURATION} seconds per state)`);
