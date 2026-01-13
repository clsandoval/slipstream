# Local Models Data Flow

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            LOCAL MODELS ON JETSON ORIN                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                           SPECIALIZED ML MODELS                             │ │
│  │                                                                             │ │
│  │   ┌─────────────────────────────┐    ┌─────────────────────────────────┐   │ │
│  │   │     POSE ESTIMATION         │    │      SPEECH-TO-TEXT             │   │ │
│  │   │     (YOLO11-Pose-s)         │    │      (Whisper-small)            │   │ │
│  │   │                             │    │                                  │   │ │
│  │   │   Camera ──▶ Keypoints      │    │   Microphone ──▶ Text           │   │ │
│  │   │                             │    │                                  │   │ │
│  │   │   30 FPS, <50ms latency     │    │   <500ms for 3s audio           │   │ │
│  │   └─────────────────────────────┘    └─────────────────────────────────┘   │ │
│  │                                                                             │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                              │                              │                    │
│                              ▼                              ▼                    │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                      SIMPLE PYTHON (NOT ML)                                 │ │
│  │                                                                             │ │
│  │   ┌─────────────────────────────┐    ┌─────────────────────────────────┐   │ │
│  │   │    POST-ESTIMATION          │    │     AGENT / MCP                  │   │ │
│  │   │                             │    │                                  │   │ │
│  │   │    • Stroke Detection       │    │    • Tool Calls                  │   │ │
│  │   │    • Rate Calculation       │    │    • State Management            │   │ │
│  │   │    • Trend Analysis         │    │    • Dashboard Updates           │   │ │
│  │   └─────────────────────────────┘    └─────────────────────────────────┘   │ │
│  │                                                                             │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                             │                                    │
└─────────────────────────────────────────────┼────────────────────────────────────┘
                                              │
                                              ▼
                              ┌───────────────────────────────┐
                              │           CLOUD               │
                              │                               │
                              │   • LLM (Claude API)          │
                              │   • TTS (ElevenLabs/OpenAI)   │
                              │                               │
                              └───────────────────────────────┘
```

## Pose Estimation Pipeline Detail

```
┌────────────┐     ┌──────────────────┐     ┌───────────────────┐     ┌─────────────────┐
│  IP Camera │────▶│  YOLO11-Pose-s   │────▶│  Keypoint Buffer  │────▶│ Stroke Detector │
│  (RTSP)    │     │  (TensorRT)      │     │  (300 frames)     │     │ (Peak Detection)│
└────────────┘     └──────────────────┘     └───────────────────┘     └─────────────────┘
      │                    │                         │                        │
      │                    │                         │                        ▼
   1080p30             30 FPS               Wrist Y-position        ┌─────────────────┐
   H.264            17 keypoints               over time            │  Stroke Rate    │
   ~3Mbps           x,y,confidence                                  │  Calculator     │
                                                                    └─────────────────┘
                                                                           │
                                                                           ▼
                                                                    ┌─────────────────┐
                                                                    │   State Store   │
                                                                    │  (SwimState)    │
                                                                    └─────────────────┘
```

## STT Pipeline Detail

```
┌────────────────┐     ┌─────────────────┐     ┌──────────────────┐     ┌───────────────┐
│  Bone Conduction│────▶│  Voice Activity │────▶│  Whisper-small   │────▶│ Claude Agent  │
│  Headset Mic    │     │  Detection      │     │  (CTranslate2)   │     │ (via MCP)     │
└────────────────┘     └─────────────────┘     └──────────────────┘     └───────────────┘
      │                       │                        │                       │
      │                       │                        │                       ▼
   16kHz                 Segments               Transcribed             ┌───────────────┐
   Mono                  speech only            text                    │  Tool Calls   │
   BT Audio                                                             │  + Response   │
                                                                        └───────────────┘
```

## Laptop Verification Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         LAPTOP (BEFORE BUYING HARDWARE)                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   STEP 1: Record Test Data                                                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  • Record 10-min swimming video (phone, side angle)                      │   │
│   │  • Manually count strokes in 2-min clip → ground_truth.json             │   │
│   │  • Record voice command audio samples                                    │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                       │
│                                          ▼                                       │
│   STEP 2: Verify Pose Model                                                      │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  Video ──▶ YOLO11-Pose ──▶ keypoints.json                               │   │
│   │                                                                          │   │
│   │  Check:                                                                  │   │
│   │  • Wrist keypoints detected in >90% of frames?                          │   │
│   │  • Keypoint confidence >0.5?                                            │   │
│   │  • Processing at >30 FPS?                                               │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                       │
│                                          ▼                                       │
│   STEP 3: Verify Stroke Detection Algorithm                                      │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  keypoints.json ──▶ StrokeDetector ──▶ detected_strokes.json            │   │
│   │                                                                          │   │
│   │  Compare to ground_truth.json:                                          │   │
│   │  • Stroke rate within ±2 strokes/min?                                   │   │
│   │  • Individual stroke timestamps within ±0.5s?                           │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                       │
│                                          ▼                                       │
│   STEP 4: Verify STT                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  test_audio.wav ──▶ Whisper ──▶ transcription                           │   │
│   │                                                                          │   │
│   │  Check:                                                                  │   │
│   │  • "What's my stroke rate?" → correctly transcribed?                    │   │
│   │  • Latency <1s for 3s audio?                                            │   │
│   │  • Works with added pool noise?                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                       │
│                                          ▼                                       │
│   STEP 5: Mock Integration Test                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  MockPoseStream ──▶ StrokeDetector ──▶ MCP Server ──▶ Dashboard         │   │
│   │                                                                          │   │
│   │  Verify full pipeline works before real hardware                         │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## What Runs Where

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DEPLOYMENT LOCATIONS                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                        JETSON ORIN (LOCAL)                               │   │
│   │                                                                          │   │
│   │   ML MODELS:                    POST-PROCESSING:                        │   │
│   │   ├── YOLO11-Pose-s.engine      ├── stroke_detector.py                  │   │
│   │   └── whisper-small-ct2/        ├── rate_calculator.py                  │   │
│   │                                  └── state_store.py                      │   │
│   │                                                                          │   │
│   │   SERVERS:                       DASHBOARD:                              │   │
│   │   ├── MCP Server (Python)        └── React app (localhost:3000)         │   │
│   │   └── WebSocket Server                                                   │   │
│   │                                                                          │   │
│   │   Claude Code CLI ◀─── Runs locally, calls cloud API                    │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                           CLOUD (REMOTE)                                 │   │
│   │                                                                          │   │
│   │   ├── Claude API (LLM reasoning)                                        │   │
│   │   └── ElevenLabs / OpenAI TTS (text-to-speech)                         │   │
│   │                                                                          │   │
│   │   ~100KB per request, tolerant of 100-500ms latency                     │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Key Insight: Only 2 Real ML Models

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           "ML" vs "NOT ML"                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   SPECIALIZED ML (needs GPU, training, optimization):                           │
│   ═══════════════════════════════════════════════════                          │
│   1. Pose Estimation (YOLO11-Pose-s)  ←  Pre-trained, just run inference        │
│   2. Speech-to-Text (Whisper-small)   ←  Pre-trained, just run inference        │
│                                                                                  │
│   NOT ML (just Python code you write):                                          │
│   ════════════════════════════════════                                          │
│   • Stroke detection     ← Peak detection on wrist Y trajectory                 │
│   • Rate calculation     ← Count peaks over time window                         │
│   • Trend analysis       ← Compare recent rate to earlier rate                  │
│   • State management     ← Python dataclasses                                   │
│   • Dashboard            ← React + WebSocket                                    │
│   • MCP Server           ← FastMCP library                                      │
│   • Voice activity       ← Simple energy threshold (or WebRTC VAD)              │
│                                                                                  │
│   CLOUD (someone else's ML):                                                    │
│   ══════════════════════════                                                    │
│   • LLM reasoning        ← Claude API                                           │
│   • Text-to-speech       ← ElevenLabs/OpenAI API                               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```
