"""Scenario and step models for verification testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Step:
    """A single step in a scenario."""

    action: str
    params: dict[str, Any] = field(default_factory=dict)
    expect: dict[str, Any] = field(default_factory=dict)
    expect_result: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Step:
        """Create step from dictionary."""
        return cls(
            action=data["action"],
            params=data.get("params", {}),
            expect=data.get("expect", {}),
            expect_result=data.get("expect_result", {}),
            description=data.get("description", ""),
        )


@dataclass
class StepResult:
    """Result of executing a step."""

    step: Step
    success: bool
    actual: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0.0


@dataclass
class Scenario:
    """A test scenario with multiple steps."""

    name: str
    description: str
    steps: list[Step]
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> Scenario:
        """Load scenario from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(
            name=data["name"],
            description=data.get("description", ""),
            steps=[Step.from_dict(s) for s in data["steps"]],
            tags=data.get("tags", []),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Scenario:
        """Create scenario from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            steps=[Step.from_dict(s) for s in data["steps"]],
            tags=data.get("tags", []),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "steps": [
                {
                    "action": s.action,
                    "params": s.params,
                    "expect": s.expect,
                    "expect_result": s.expect_result,
                    "description": s.description,
                }
                for s in self.steps
            ],
            "tags": self.tags,
        }


@dataclass
class ScenarioResult:
    """Result of running a scenario."""

    scenario: Scenario
    success: bool
    step_results: list[StepResult]
    duration_ms: float = 0.0

    @property
    def failed_steps(self) -> list[StepResult]:
        """Get failed step results."""
        return [r for r in self.step_results if not r.success]

    def summary(self) -> str:
        """Generate a human-readable summary."""
        status = "PASSED" if self.success else "FAILED"
        passed = sum(1 for r in self.step_results if r.success)
        total = len(self.step_results)
        lines = [
            f"Scenario: {self.scenario.name} - {status}",
            f"Steps: {passed}/{total} passed ({self.duration_ms:.1f}ms)",
        ]

        if not self.success:
            lines.append("Failed steps:")
            for r in self.failed_steps:
                lines.append(f"  - {r.step.action}: {r.error}")

        return "\n".join(lines)
