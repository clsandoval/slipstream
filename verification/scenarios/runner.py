"""Scenario runner for executing test scenarios."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import websockets

from src.mcp.server import SwimCoachServer
from verification.mocks import MockVisionStateStore, MockTranscriptStream
from verification.scenarios.models import (
    Scenario,
    Step,
    StepResult,
    ScenarioResult,
)


@dataclass
class ScenarioRunner:
    """
    Executes test scenarios against the server.

    Coordinates mocks, server, and WebSocket client
    to run integration tests.
    """

    config_dir: Path
    mock_vision: MockVisionStateStore | None = None
    mock_transcript: MockTranscriptStream | None = None

    _server: SwimCoachServer | None = field(default=None, repr=False)
    _ws: Any = field(default=None, repr=False)
    _last_state: dict[str, Any] | None = field(default=None, repr=False)

    async def setup(self) -> None:
        """Initialize server and connections."""
        self.mock_vision = self.mock_vision or MockVisionStateStore()

        self._server = SwimCoachServer(
            websocket_port=0,
            push_interval=0.1,
            config_dir=self.config_dir,
            vision_state_store=self.mock_vision,
        )
        await self._server.start()

        # Connect WebSocket
        uri = f"ws://localhost:{self._server.websocket_server.port}"
        self._ws = await websockets.connect(uri)

        # Get initial state
        msg = await self._ws.recv()
        self._last_state = json.loads(msg)

    async def teardown(self) -> None:
        """Clean up resources."""
        if self._ws:
            await self._ws.close()
        if self._server:
            await self._server.stop()

    async def run(self, scenario: Scenario) -> ScenarioResult:
        """
        Run a scenario.

        Args:
            scenario: Scenario to execute

        Returns:
            ScenarioResult with pass/fail and details
        """
        start = time.perf_counter()
        step_results: list[StepResult] = []

        for step in scenario.steps:
            result = await self._execute_step(step)
            step_results.append(result)

            if not result.success:
                break  # Stop on first failure

        duration = (time.perf_counter() - start) * 1000
        success = all(r.success for r in step_results)

        return ScenarioResult(
            scenario=scenario,
            success=success,
            step_results=step_results,
            duration_ms=duration,
        )

    async def run_all(self, scenarios: list[Scenario]) -> list[ScenarioResult]:
        """
        Run multiple scenarios.

        Args:
            scenarios: List of scenarios to execute

        Returns:
            List of ScenarioResults
        """
        results = []
        for scenario in scenarios:
            # Reset state between scenarios
            if self.mock_vision:
                self.mock_vision.reset()
            result = await self.run(scenario)
            results.append(result)
        return results

    async def _execute_step(self, step: Step) -> StepResult:
        """Execute a single step."""
        start = time.perf_counter()

        try:
            # Execute action
            action_result = await self._execute_action(step.action, step.params)

            # Wait for state update if needed
            if step.expect:
                await self._wait_for_state_update()

            # Check expectations on state
            if step.expect:
                errors = self._check_expectations(step.expect)
                if errors:
                    return StepResult(
                        step=step,
                        success=False,
                        actual=self._last_state or {},
                        result=action_result or {},
                        error="; ".join(errors),
                        duration_ms=(time.perf_counter() - start) * 1000,
                    )

            # Check expectations on action result
            if step.expect_result and action_result:
                errors = self._check_result_expectations(
                    step.expect_result, action_result
                )
                if errors:
                    return StepResult(
                        step=step,
                        success=False,
                        actual=self._last_state or {},
                        result=action_result,
                        error="; ".join(errors),
                        duration_ms=(time.perf_counter() - start) * 1000,
                    )

            return StepResult(
                step=step,
                success=True,
                actual=self._last_state or {},
                result=action_result or {},
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        except Exception as e:
            return StepResult(
                step=step,
                success=False,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    async def _execute_action(
        self, action: str, params: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Execute an action."""
        if action == "start_session":
            return self._server._start_session()
        elif action == "end_session":
            return await self._server._end_session()
        elif action == "wait":
            await asyncio.sleep(params.get("duration", 1.0))
            return None
        elif action == "set_swimming":
            self.mock_vision.set_swimming(params.get("value", True))
            return None
        elif action == "set_stroke_count":
            self.mock_vision.set_stroke_count(params["count"])
            return None
        elif action == "set_stroke_rate":
            self.mock_vision.set_stroke_rate(params["rate"])
            return None
        elif action == "get_stroke_rate":
            return self._server.metric_bridge.get_stroke_rate()
        elif action == "get_stroke_count":
            return self._server.metric_bridge.get_stroke_count()
        else:
            raise ValueError(f"Unknown action: {action}")

    async def _wait_for_state_update(self, timeout: float = 2.0) -> None:
        """Wait for WebSocket state update with fresh data.

        Drains any pending messages to ensure we get the latest state.
        """
        end_time = asyncio.get_event_loop().time() + timeout
        last_msg = None

        while asyncio.get_event_loop().time() < end_time:
            try:
                # Short timeout to drain quickly
                msg = await asyncio.wait_for(self._ws.recv(), timeout=0.2)
                last_msg = msg
            except asyncio.TimeoutError:
                # No more messages pending - we have the latest
                break

        if last_msg:
            self._last_state = json.loads(last_msg)

    def _check_expectations(self, expect: dict[str, Any]) -> list[str]:
        """Check expectations against current state."""
        errors = []

        for path, expected in expect.items():
            actual = self._get_nested(self._last_state, path)
            if actual != expected:
                errors.append(f"{path}: expected {expected}, got {actual}")

        return errors

    def _check_result_expectations(
        self, expect: dict[str, Any], result: dict[str, Any]
    ) -> list[str]:
        """Check expectations against action result."""
        errors = []

        for key, expected in expect.items():
            actual = result.get(key)
            if actual != expected:
                errors.append(f"result.{key}: expected {expected}, got {actual}")

        return errors

    def _get_nested(self, obj: dict | None, path: str) -> Any:
        """Get nested value by dot-separated path."""
        if obj is None:
            return None

        parts = path.split(".")
        current = obj
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current
