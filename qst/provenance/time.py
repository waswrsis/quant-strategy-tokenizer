"""Timestamp normalization shared by QST 1.0 immutable records."""

from __future__ import annotations

from datetime import UTC, datetime


def normalize_utc(value: datetime) -> datetime:
    """Require timezone information and normalize a timestamp to UTC."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return value.astimezone(UTC)

