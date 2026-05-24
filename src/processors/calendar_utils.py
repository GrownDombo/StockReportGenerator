from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def get_previous_business_day(tz_name: str = "Asia/Seoul") -> datetime:
    """현재 시점 기준 직전 영업일(주말 보정)을 반환합니다."""
    now = datetime.now(ZoneInfo(tz_name))
    day = now.date() - timedelta(days=1)

    while day.weekday() >= 5:  # 5: 토, 6: 일
        day -= timedelta(days=1)

    return datetime(day.year, day.month, day.day, tzinfo=ZoneInfo(tz_name))
