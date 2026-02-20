"""
Time-based context features.
Adds temporal awareness: hour, day, business hours, time since last request.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass
class TimeContext:
    hour: int
    day_of_week: int  # 0=Monday, 6=Sunday
    is_business_hours: bool
    is_weekend: bool
    time_since_last_request: float  # seconds


class TimeFeatures:
    """Extracts time-based context features."""

    def __init__(self):
        self._last_request: Dict[str, float] = {}  # key -> timestamp

    def extract(self, key: str, timestamp: float = None) -> TimeContext:
        """
        Extract time features for a flow.

        Args:
            key: Identifier for the flow source (e.g. app_name or src_ip)
            timestamp: Unix timestamp (defaults to now)
        """
        ts = timestamp or time.time()
        dt = datetime.fromtimestamp(ts)

        # Time since last request from this source
        last = self._last_request.get(key, ts)
        time_since = ts - last
        self._last_request[key] = ts

        return TimeContext(
            hour=dt.hour,
            day_of_week=dt.weekday(),
            is_business_hours=self._is_business_hours(dt),
            is_weekend=dt.weekday() >= 5,
            time_since_last_request=time_since,
        )

    def _is_business_hours(self, dt: datetime) -> bool:
        """Check if timestamp falls within business hours (9AM-6PM, Mon-Fri)."""
        return dt.weekday() < 5 and 9 <= dt.hour < 18
