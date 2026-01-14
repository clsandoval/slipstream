"""Transcript log file manager with rotation and cleanup."""

import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class LogManager:
    """Manages transcript log file operations.

    Handles appending transcriptions with timestamps, log rotation,
    and cleanup of old log files.
    """

    log_path: Path = field(default_factory=lambda: Path.home() / ".slipstream" / "transcript.log")

    def append(self, text: str | None) -> None:
        """Append timestamped transcription to log file.

        Args:
            text: Transcription text to append. Empty or whitespace-only
                  strings are ignored.
        """
        if text is None or not text.strip():
            return

        # Ensure parent directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Format: 2026-01-11T08:30:15.123 hello world
        timestamp = datetime.now().isoformat(timespec="milliseconds")
        line = f"{timestamp} {text.strip()}\n"

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line)

    def rotate_if_needed(self) -> None:
        """Rotate log file if it's from a previous day.

        Renames the current log file with a date suffix (e.g.,
        transcript.2026-01-10.log) if the file was last modified
        on a different day.
        """
        if not self.log_path.exists():
            return

        # Get file modification date
        mtime = os.path.getmtime(self.log_path)
        file_date = datetime.fromtimestamp(mtime).date()
        today = datetime.now().date()

        if file_date < today:
            # Rotate: rename with date suffix
            rotated_name = f"{self.log_path.stem}.{file_date.isoformat()}{self.log_path.suffix}"
            rotated_path = self.log_path.parent / rotated_name
            self.log_path.rename(rotated_path)

    def cleanup_old_logs(self, retention_days: int = 7) -> None:
        """Delete log files older than retention period.

        Args:
            retention_days: Number of days to keep log files. Files older
                           than this are deleted. The current log file is
                           never deleted.
        """
        if not self.log_path.parent.exists():
            return

        cutoff_time = time.time() - (retention_days * 24 * 60 * 60)

        for file_path in self.log_path.parent.glob("transcript.*.log"):
            # Skip the current log file
            if file_path == self.log_path:
                continue

            # Check modification time
            if os.path.getmtime(file_path) < cutoff_time:
                file_path.unlink()
