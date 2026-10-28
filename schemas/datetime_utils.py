from datetime import datetime, timezone


def require_aware_datetime(value: datetime | None) -> datetime | None:
    """Reject zone-free instants and normalize valid values to UTC."""

    if value is None:
        return None

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("日時にはタイムゾーンを指定してください。")

    return value.astimezone(timezone.utc)
