"""Workout template storage.

Save and retrieve workout templates for reuse.
Templates are stored as JSON files in the templates directory.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.mcp.workout.models import Workout


def _sanitize_filename(name: str) -> str:
    """Convert workout name to safe filename."""
    safe = "".join(c if c.isalnum() or c in "- _" else "_" for c in name)
    return safe.lower().replace(" ", "_")[:50]


@dataclass
class TemplateStorage:
    """
    Storage for workout templates.

    Saves workout definitions as JSON files for reuse.
    """

    template_dir: Path

    def __post_init__(self) -> None:
        """Ensure template directory exists."""
        self.template_dir.mkdir(parents=True, exist_ok=True)

    def save(self, workout: Workout) -> Path:
        """
        Save workout as template.

        Args:
            workout: Workout to save

        Returns:
            Path to saved template file
        """
        filename = f"{_sanitize_filename(workout.name)}_{workout.workout_id}.json"
        path = self.template_dir / filename

        with open(path, "w") as f:
            json.dump(workout.to_dict(), f, indent=2)

        return path

    def get(self, workout_id: str) -> Workout | None:
        """
        Get template by workout ID.

        Args:
            workout_id: ID of workout to retrieve

        Returns:
            Workout if found, None otherwise
        """
        for path in self.template_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                if data.get("workout_id") == workout_id:
                    return Workout.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                continue
        return None

    def list(self, limit: int = 10) -> list[Workout]:
        """
        List all templates.

        Args:
            limit: Maximum number to return

        Returns:
            List of Workout templates, newest first
        """
        templates: list[Workout] = []

        for path in self.template_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                templates.append(Workout.from_dict(data))
            except (json.JSONDecodeError, KeyError):
                continue

        # Sort by created_at, newest first
        templates.sort(key=lambda w: w.created_at, reverse=True)

        return templates[:limit]

    def delete(self, workout_id: str) -> bool:
        """
        Delete template by workout ID.

        Args:
            workout_id: ID of workout to delete

        Returns:
            True if deleted, False if not found
        """
        for path in self.template_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                if data.get("workout_id") == workout_id:
                    path.unlink()
                    return True
            except (json.JSONDecodeError, KeyError):
                continue
        return False
