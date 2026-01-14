"""
Verification module for integration testing.

Provides mock infrastructure, scenario-based testing, and E2E harness
for testing the full Slipstream stack without real hardware.
"""

from verification.mocks import MockVisionStateStore, MockTranscriptStream, Utterance

__all__ = ["MockVisionStateStore", "MockTranscriptStream", "Utterance"]
