"""MCP tools for session management."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

from src.mcp.state_store import (
    NoActiveSessionError,
    SessionActiveError,
    StateStore,
)
from src.mcp.storage.session_storage import SessionStorage

logger = logging.getLogger(__name__)


def create_session_tools(
    state_store: StateStore,
    session_storage: SessionStorage,
) -> list[Callable[[], dict[str, Any] | Coroutine[Any, Any, dict[str, Any]]]]:
    """Create session management tools for MCP registration.

    Args:
        state_store: In-memory state store
        session_storage: Session file storage

    Returns:
        List of tool functions [start_session, end_session, get_status]
    """

    def start_session() -> dict[str, Any]:
        """Begin a new swim session.

        Returns a dict with session_id and started_at, or error if already active.
        """
        try:
            session_id = state_store.start_session()
            started_at = datetime.now(timezone.utc)

            # Create session file
            session_storage.create_session(session_id, started_at)

            return {
                "session_id": session_id,
                "started_at": started_at.isoformat(),
            }
        except SessionActiveError:
            return {"error": "A session is already active"}

    async def end_session() -> dict[str, Any]:
        """End current session and save data.

        Returns a dict with session summary, or error if no active session.
        """
        try:
            summary = state_store.end_session()
            session_id = summary["session_id"]

            # Update session file with final data
            session_storage.update_session(
                session_id,
                {
                    "ended_at": summary["ended_at"],
                    "duration_seconds": summary["duration_seconds"],
                    "stroke_count": summary["stroke_count"],
                    "stroke_rate_avg": summary["stroke_rate_avg"],
                    "estimated_distance_m": summary["estimated_distance_m"],
                },
            )

            result: dict[str, Any] = {"summary": summary}

            # Trigger notification if configured
            if state_store.notification_manager:
                try:
                    notification_sent = (
                        await state_store.notification_manager.on_session_end(summary)
                    )
                    result["notification_sent"] = notification_sent
                except Exception as e:
                    logger.error(f"Notification error: {e}")
                    result["notification_sent"] = False

            return result
        except NoActiveSessionError:
            return {"error": "No active session to end"}

    def get_status() -> dict[str, Any]:
        """Get current system status.

        Returns a dict with session and system state information.
        """
        state_update = state_store.get_state_update()

        return {
            "session_active": state_update.session.active,
            "elapsed_seconds": state_update.session.elapsed_seconds,
            "stroke_count": state_update.session.stroke_count,
            "stroke_rate": state_update.session.stroke_rate,
            "stroke_rate_trend": state_update.session.stroke_rate_trend,
            "estimated_distance_m": state_update.session.estimated_distance_m,
            "is_swimming": state_update.system.is_swimming,
            "pose_detected": state_update.system.pose_detected,
            "voice_state": state_update.system.voice_state,
        }

    return [start_session, end_session, get_status]
