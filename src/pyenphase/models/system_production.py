"""Model for the Envoy's production data."""
# Data Source: URL_PRODUCTION
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def find_dict_by_key(all_production: list[dict[str, Any]], key: str) -> dict[str, Any]:
    """Find a dict by key."""
    for production in all_production:
        if production.get("type") == key:
            return production
    raise ValueError(f"{key} is missing")


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

        eim = find_dict_by_key(all_production, "eim")
        inverters = find_dict_by_key(all_production, "inverters")

        # This is backwards compatible with envoy_reader
        now_source = eim if eim["activeCount"] else inverters

        return cls(
            watt_hours_lifetime=int(
                round(eim.get("whLifetime") or inverters.get("whLifetime") or 0)
            ),
            watt_hours_last_7_days=int(
                round(
                    eim.get("whLastSevenDays") or inverters.get("whLastSevenDays") or 0
                )
            ),
            watt_hours_today=int(
                round(eim.get("whToday") or inverters.get("whToday") or 0)
            ),
            watts_now=int(round(now_source["wNow"])),
        )
