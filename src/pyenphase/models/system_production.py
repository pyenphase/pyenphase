"""Model for the Envoy's production data."""
# Data Source: URL_PRODUCTION
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EnvoySystemProduction:
    """Model for the Envoy's production data."""

    watt_hours_lifetime: int
    watt_hours_last_7_days: int
    watt_hours_today: int
    watts_now: int

    @classmethod
    def from_v1_api(cls, data: dict[str, Any]) -> EnvoySystemProduction:
        """Initialize from the V1 API."""
        return cls(
            watt_hours_lifetime=data["wattHoursLifetime"],
            watt_hours_last_7_days=data["wattHoursSevenDays"],
            watt_hours_today=data["wattHoursToday"],
            watts_now=data["wattsNow"],
        )

    @classmethod
    def from_production(cls, data: dict[str, Any]) -> EnvoySystemProduction:
        """Initialize from the production API."""
        all_production = data["production"]

        eim = all_production[0]
        inverters = all_production[1]

        # This is backwards compatible with envoy_reader
        now_source = inverters if inverters["activeCount"] else eim

        return cls(
            watt_hours_lifetime=inverters["whLifetime"],
            watt_hours_last_7_days=inverters["whLastSevenDays"],
            watt_hours_today=inverters["whToday"],
            watts_now=now_source["wNow"],
        )
