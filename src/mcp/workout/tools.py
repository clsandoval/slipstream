"""MCP workout tools.

Creates tool functions for workout management that can be
registered with the MCP server.
"""

from __future__ import annotations

from typing import Any, Callable

from src.mcp.workout.models import Workout, WorkoutSegment
from src.mcp.workout.state_machine import (
    WorkoutStateMachine,
    WorkoutExistsError,
    NoWorkoutError,
    WorkoutAlreadyActiveError,
    WorkoutNotActiveError,
)
from src.mcp.workout.templates import TemplateStorage


def create_workout_tools(
    state_machine: WorkoutStateMachine,
    template_storage: TemplateStorage,
) -> list[Callable]:
    """
    Create workout management tools for MCP registration.

    Args:
        state_machine: WorkoutStateMachine instance
        template_storage: TemplateStorage instance

    Returns:
        List of tool functions for MCP
    """

    def create_workout(
        name: str,
        segments: list[dict[str, Any]],
        save_as_template: bool = False,
    ) -> dict[str, Any]:
        """
        Create a workout plan (does not start it).

        Creates a structured workout with multiple segments. Each segment
        can target duration, distance, or stroke rate.

        Args:
            name: Workout name (e.g., "4x100m Intervals")
            segments: List of segment definitions with type and targets
            save_as_template: If True, save for future reuse

        Returns:
            workout_id: Unique ID for this workout
            segments_count: Number of segments created
        """
        try:
            # Validate and convert segments
            workout_segments = []
            for seg in segments:
                if seg.get("type") not in ("warmup", "work", "rest", "cooldown"):
                    return {"error": f"Invalid segment type: {seg.get('type')}"}
                workout_segments.append(WorkoutSegment.from_dict(seg))

            workout = Workout(name=name, segments=workout_segments)
            result = state_machine.create_workout(workout)

            if save_as_template:
                template_storage.save(workout)

            return result

        except WorkoutExistsError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def start_workout() -> dict[str, Any]:
        """
        Begin executing a created workout.

        Transitions the workout from CREATED to ACTIVE state
        and starts tracking segment progress.

        Returns:
            started_at: ISO timestamp when workout started
            first_segment: Details of the first segment
            total_segments: Total number of segments
        """
        try:
            return state_machine.start_workout()
        except (NoWorkoutError, WorkoutAlreadyActiveError) as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def get_workout_status() -> dict[str, Any]:
        """
        Get current workout execution status.

        Returns comprehensive status including current segment,
        progress, elapsed time, and next segment preview.

        Returns:
            has_active_workout: Whether a workout is running
            workout_name: Name of current workout
            current_segment: Current segment details
            progress: Completion progress
            next_segment: Next segment preview
        """
        try:
            return state_machine.get_status()
        except Exception as e:
            return {"error": str(e)}

    def skip_segment() -> dict[str, Any]:
        """
        Skip current segment and advance to next.

        Marks the current segment as skipped and immediately
        advances to the next segment (or completes workout).

        Returns:
            skipped: Details of skipped segment
            now_on: Details of new current segment (or None if complete)
        """
        try:
            result = state_machine.skip_segment()
            return {
                "skipped": result.get("completed"),
                "now_on": result.get("now_on"),
                "workout_complete": result.get("workout_complete", False),
            }
        except WorkoutNotActiveError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def end_workout() -> dict[str, Any]:
        """
        End workout early.

        Terminates the current workout and returns a summary
        of completed segments.

        Returns:
            summary: Complete workout summary with all segment results
        """
        try:
            summary = state_machine.end_workout()
            state_machine.clear_workout()
            return {"summary": summary}
        except WorkoutNotActiveError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def list_workout_templates(limit: int = 10) -> dict[str, Any]:
        """
        List saved workout templates.

        Returns a list of previously saved workout templates
        that can be used to create new workouts.

        Args:
            limit: Maximum number of templates to return

        Returns:
            templates: List of template summaries
            count: Total number of templates
        """
        try:
            templates = template_storage.list(limit=limit)
            return {
                "templates": [t.to_dict() for t in templates],
                "count": len(templates),
            }
        except Exception as e:
            return {"error": str(e)}

    return [
        create_workout,
        start_workout,
        get_workout_status,
        skip_segment,
        end_workout,
        list_workout_templates,
    ]
