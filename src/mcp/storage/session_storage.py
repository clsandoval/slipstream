"""Session file I/O to ~/.slipstream/sessions/."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _default_sessions_dir() -> Path:
    """Get default sessions directory."""
    return Path.home() / ".slipstream" / "sessions"


@dataclass
class SessionStorage:
    """Manages session file storage."""

    sessions_dir: Path = field(default_factory=_default_sessions_dir)

    def create_session(self, session_id: str, started_at: datetime) -> dict[str, Any]:
        """Create a new session file.

        Args:
            session_id: Unique session identifier
            started_at: Session start timestamp

        Returns:
            Session data dict
        """
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        session_data = {
            "session_id": session_id,
            "started_at": started_at.isoformat(),
            "ended_at": None,
            "stroke_count": 0,
            "stroke_rate_avg": 0.0,
            "duration_seconds": 0,
            "estimated_distance_m": 0.0,
        }

        session_path = self._session_path(session_id)
        session_path.write_text(json.dumps(session_data, indent=2))

        return session_data

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session data dict or None if not found
        """
        session_path = self._session_path(session_id)
        if not session_path.exists():
            return None

        return json.loads(session_path.read_text())

    def update_session(self, session_id: str, updates: dict[str, Any]) -> None:
        """Update session with new data.

        Args:
            session_id: Session identifier
            updates: Dict of fields to update
        """
        session_path = self._session_path(session_id)
        if not session_path.exists():
            return

        session_data = json.loads(session_path.read_text())
        session_data.update(updates)
        session_path.write_text(json.dumps(session_data, indent=2))

    def list_sessions(self, limit: int = 10) -> list[dict[str, Any]]:
        """List sessions sorted by date (newest first).

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session data dicts
        """
        if not self.sessions_dir.exists():
            return []

        session_files = sorted(
            self.sessions_dir.glob("*.json"),
            reverse=True,
            key=lambda p: p.stem,
        )

        sessions = []
        for session_file in session_files[:limit]:
            sessions.append(json.loads(session_file.read_text()))

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete session file.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        session_path = self._session_path(session_id)
        if not session_path.exists():
            return False

        session_path.unlink()
        return True

    def generate_session_id(self) -> str:
        """Generate session ID from current timestamp.

        Returns:
            Session ID in format YYYY-MM-DD_HHMM
        """
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%d_%H%M")

    def _session_path(self, session_id: str) -> Path:
        """Get file path for session.

        Args:
            session_id: Session identifier

        Returns:
            Path to session JSON file
        """
        return self.sessions_dir / f"{session_id}.json"
