# Branch 8: Verification

**Branch**: `feature/verification`
**Scope**: Testing Infrastructure & Validation
**Dependencies**: Branch 1 (vision-pipeline), Branch 3 (stt-service)
**Complexity**: Medium

---

## Description

Mock data generators, ground truth comparison, and integration tests for validating the complete system.

---

## Components

| Component | Description |
|-----------|-------------|
| Mock streams | `MockPoseStream`, `MockAudioStream` |
| Ground truth format | JSON annotation schema |
| Accuracy evaluation | Stroke rate comparison scripts |
| Benchmark scripts | FPS, latency measurements |
| Integration tests | End-to-end pipeline tests |
| Test data | Sample videos, audio, annotations |

---

## File Structure

```
verification/
├── pose/
│   ├── run_pose_on_video.py      # Extract keypoints from video
│   ├── stroke_detector_test.py   # Test stroke detection
│   ├── evaluate_accuracy.py      # Compare to ground truth
│   └── benchmark_fps.py          # Measure inference speed
├── stt/
│   ├── run_whisper_on_audio.py   # Transcribe test audio
│   ├── evaluate_wer.py           # Word Error Rate
│   └── benchmark_latency.py      # Transcription speed
├── mock/
│   ├── mock_pose_stream.py       # Synthetic keypoint data
│   └── mock_audio_stream.py      # Pre-recorded queries
├── integration/
│   ├── test_mcp_tools.py         # Test all MCP tools
│   ├── test_websocket.py         # Test dashboard updates
│   └── test_full_pipeline.py     # End-to-end test
├── test_data/
│   ├── videos/
│   │   ├── freestyle_2min_side.mp4
│   │   └── ...
│   ├── annotations/
│   │   └── freestyle_2min_side_strokes.json
│   └── audio/
│       ├── stroke_rate_query.wav
│       └── ...
└── config.yaml                   # Model paths, thresholds
```

---

## Ground Truth Format

```json
{
  "video": "freestyle_2min_side.mp4",
  "fps": 30,
  "strokes": [
    {"frame": 45, "time": 1.5, "arm": "left"},
    {"frame": 78, "time": 2.6, "arm": "right"},
    {"frame": 112, "time": 3.73, "arm": "left"}
  ],
  "notes": "Freestyle, moderate pace"
}
```

---

## Verification Checklists

### Pose Estimation
- [ ] Model loads without error
- [ ] Process test video end-to-end
- [ ] Wrist keypoints detected >90% of frames
- [ ] Keypoint confidence >0.5 average
- [ ] Stroke rate ±2 strokes/min vs ground truth
- [ ] Inference >30 FPS on laptop

### Speech-to-Text
- [ ] Model loads without error
- [ ] >95% accuracy on clean audio
- [ ] >85% accuracy with pool noise
- [ ] Latency <1s for 3s utterance

### Integration
- [ ] Mock pipeline end-to-end works
- [ ] Real video + algorithm matches ground truth
- [ ] 10-minute continuous test stable

---

## Success Criteria

- [ ] All verification checklists pass
- [ ] Mock streams work for development
- [ ] Integration tests cover critical paths
- [ ] Benchmarks documented

---

## Upstream Dependencies

Requires:
- Branch 1: `feature/vision-pipeline` (for pose testing)
- Branch 3: `feature/stt-service` (for STT testing)

This branch runs parallel throughout development.
