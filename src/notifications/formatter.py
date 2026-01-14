"""Session summary formatting for notifications."""

from typing import Any


def format_duration(seconds: int) -> str:
    """
    Format seconds as MM:SS or H:MM:SS.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"


def format_distance(meters: float) -> str:
    """
    Format distance with comma separator.

    Args:
        meters: Distance in meters

    Returns:
        Formatted distance string with 'm' suffix
    """
    rounded = round(meters)
    return f"{rounded:,}m"


def format_summary(session: dict[str, Any]) -> str:
    """
    Format session data as Telegram message.

    Args:
        session: Session dict from SessionStorage

    Returns:
        Formatted message string
    """
    duration = format_duration(session.get("duration_seconds", 0))
    distance = format_distance(session.get("estimated_distance_m", 0.0))
    stroke_rate = round(session.get("stroke_rate_avg", 0.0))
    stroke_count = session.get("stroke_count", 0)

    lines = [
        "🏊 Swim Session Complete",
        "",
        f"Duration: {duration}",
        f"Est. Distance: ~{distance}",
        f"Avg Stroke Rate: {stroke_rate}/min",
        f"Total Strokes: {stroke_count:,}",
    ]

    return "\n".join(lines)
