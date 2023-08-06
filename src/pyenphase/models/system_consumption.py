"""Model for the Envoy's consumption data."""
# Data Source: URL_PRODUCTION

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EnvoySystemConsumption:
    """Model for the Envoy's consumption data."""

    watt_hours_lifetime: int
    watt_hours_last_7_days: int
    watt_hours_today: int
    watts_now: int

    @classmethod
    def from_production(cls, data: dict[str, Any]) -> EnvoySystemConsumption:
        """Initialize from the production API."""
        consumption = data["consumption"][0]
        return cls(
            watt_hours_lifetime=int(round(consumption["whLifetime"])),
            watt_hours_last_7_days=int(round(consumption["whLastSevenDays"])),
            watt_hours_today=int(round(consumption["whToday"])),
            watts_now=int(round(consumption["wNow"])),
        )
