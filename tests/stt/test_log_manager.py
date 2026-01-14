"""Tests for LogManager - transcript log file operations."""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from freezegun import freeze_time

import pytest

from src.stt.log_manager import LogManager


class TestAppendTranscription:
    """Tests for appending transcriptions to log."""

    def test_append_transcription(self, log_manager: LogManager, temp_log_path: Path):
        """Append transcription creates timestamped entry."""
        log_manager.append("hello world")

        content = temp_log_path.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 1
        # Format: 2026-01-11T08:30:15.123 hello world
        assert "hello world" in lines[0]
        # Check timestamp format (ISO 8601 with milliseconds)
        timestamp_part = lines[0].split(" ")[0]
        datetime.fromisoformat(timestamp_part)  # Raises if invalid

    def test_multiple_appends(self, log_manager: LogManager, temp_log_path: Path):
        """Multiple appends create multiple entries in order."""
        log_manager.append("first line")
        log_manager.append("second line")

        content = temp_log_path.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2
        assert "first line" in lines[0]
        assert "second line" in lines[1]

    def test_creates_log_file(self, temp_log_dir: Path):
        """Creates log file if it doesn't exist."""
        log_path = temp_log_dir / "new_transcript.log"
        assert not log_path.exists()

        manager = LogManager(log_path=log_path)
        manager.append("first entry")

        assert log_path.exists()
        assert "first entry" in log_path.read_text()

    def test_creates_parent_dir(self, tmp_path: Path):
        """Creates parent directory if it doesn't exist."""
        log_path = tmp_path / "new_dir" / "transcript.log"
        assert not log_path.parent.exists()

        manager = LogManager(log_path=log_path)
        manager.append("first")

        assert log_path.exists()
        assert "first" in log_path.read_text()

    def test_skip_empty_text(self, log_manager: LogManager, temp_log_path: Path):
        """Empty strings are not written to log."""
        log_manager.append("")
        log_manager.append("   ")  # Whitespace only

        assert not temp_log_path.exists() or temp_log_path.read_text() == ""

    def test_skip_none_text(self, log_manager: LogManager, temp_log_path: Path):
        """None values are handled gracefully."""
        log_manager.append(None)  # type: ignore

        assert not temp_log_path.exists() or temp_log_path.read_text() == ""


class TestLogRotation:
    """Tests for log rotation functionality."""

    def test_rotate_nonexistent_log(self, temp_log_dir: Path):
        """Rotation is no-op when log file doesn't exist."""
        log_path = temp_log_dir / "nonexistent.log"
        manager = LogManager(log_path=log_path)

        # Should not raise
        manager.rotate_if_needed()

        # File still doesn't exist
        assert not log_path.exists()

    @freeze_time("2026-01-11 08:00:00")
    def test_rotate_log(self, temp_log_dir: Path):
        """Log file older than 1 day is rotated with date suffix."""
        log_path = temp_log_dir / "transcript.log"
        manager = LogManager(log_path=log_path)

        # Create a log entry and set file mtime to "yesterday"
        manager.append("yesterday entry")
        yesterday_ts = datetime(2026, 1, 10, 8, 0, 0).timestamp()
        os.utime(log_path, (yesterday_ts, yesterday_ts))

        # Now rotate
        manager.rotate_if_needed()

        # Old file should be renamed
        rotated_file = temp_log_dir / "transcript.2026-01-10.log"
        assert rotated_file.exists()
        assert "yesterday entry" in rotated_file.read_text()

        # Current log should not exist after rotation
        assert not log_path.exists()

    def test_no_rotation_same_day(self, log_manager: LogManager, temp_log_path: Path):
        """Log file from same day is not rotated."""
        log_manager.append("today entry")
        original_content = temp_log_path.read_text()

        log_manager.rotate_if_needed()

        assert temp_log_path.read_text() == original_content

    @freeze_time("2026-01-11 08:00:00")
    def test_rotation_creates_new_file(self, temp_log_dir: Path):
        """After rotation, new entries go to fresh file."""
        log_path = temp_log_dir / "transcript.log"
        manager = LogManager(log_path=log_path)

        # Create entry and set mtime to yesterday
        manager.append("old entry")
        yesterday_ts = datetime(2026, 1, 10, 8, 0, 0).timestamp()
        os.utime(log_path, (yesterday_ts, yesterday_ts))

        manager.rotate_if_needed()
        manager.append("new entry")

        assert "new entry" in log_path.read_text()
        assert "old entry" not in log_path.read_text()


class TestCleanupOldLogs:
    """Tests for cleaning up old log files."""

    def test_cleanup_old_logs(self, temp_log_dir: Path):
        """Files older than retention period are deleted."""
        log_path = temp_log_dir / "transcript.log"
        manager = LogManager(log_path=log_path)

        # Create old log files
        old_log = temp_log_dir / "transcript.2026-01-01.log"
        old_log.write_text("old content")
        # Set modification time to 10 days ago
        old_time = time.time() - (10 * 24 * 60 * 60)
        os.utime(old_log, (old_time, old_time))

        recent_log = temp_log_dir / "transcript.2026-01-08.log"
        recent_log.write_text("recent content")

        manager.cleanup_old_logs(retention_days=7)

        assert not old_log.exists()
        assert recent_log.exists()

    def test_cleanup_preserves_current_log(self, log_manager: LogManager, temp_log_path: Path):
        """Current log file is never deleted during cleanup."""
        log_manager.append("current entry")

        log_manager.cleanup_old_logs(retention_days=0)

        assert temp_log_path.exists()

    def test_cleanup_handles_empty_dir(self, temp_log_dir: Path):
        """Cleanup works when no old logs exist."""
        log_path = temp_log_dir / "transcript.log"
        manager = LogManager(log_path=log_path)

        # Should not raise
        manager.cleanup_old_logs(retention_days=7)

    def test_cleanup_nonexistent_parent_dir(self, tmp_path: Path):
        """Cleanup is no-op when parent directory doesn't exist."""
        log_path = tmp_path / "nonexistent_dir" / "transcript.log"
        manager = LogManager(log_path=log_path)

        # Should not raise
        manager.cleanup_old_logs(retention_days=7)

    def test_cleanup_skips_current_log(self, temp_log_dir: Path):
        """Cleanup skips the current log file even if old."""
        import time

        log_path = temp_log_dir / "transcript.log"
        manager = LogManager(log_path=log_path)

        # Create current log file
        log_path.write_text("current content")

        # Also create an old rotated log that matches the pattern
        old_log = temp_log_dir / "transcript.2026-01-05.log"
        old_log.write_text("old content")
        old_time = time.time() - (10 * 24 * 60 * 60)  # 10 days ago
        os.utime(old_log, (old_time, old_time))

        manager.cleanup_old_logs(retention_days=7)

        # Old rotated log deleted
        assert not old_log.exists()
        # Current log preserved
        assert log_path.exists()
