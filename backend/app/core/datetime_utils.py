from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def resolve_timezone(tz_name: str | None) -> ZoneInfo:
    if not tz_name:
        return ZoneInfo("UTC")
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def today_for_timezone(tz_name: str | None) -> date:
    return datetime.now(resolve_timezone(tz_name)).date()
