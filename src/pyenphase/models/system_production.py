"""Model for the Envoy's production data."""
# Data Source: URL_PRODUCTION

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EnvoySystemProduction:
    """Model for the Envoy's production data."""

    watt_hours_lifetime: int
    watt_hours_last_7_days: int
    watt_hours_today: int
    watts_now: int

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize."""
        self.watt_hours_lifetime = data["wattHoursLifetime"]
        self.watt_hours_last_7_days = data["wattHoursSevenDays"]
        self.watt_hours_today = data["wattHoursToday"]
        self.watts_now = data["wattsNow"]
