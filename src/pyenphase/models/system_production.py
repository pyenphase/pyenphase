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

    watt_hours_lifetime: int  #: Lifetime Energy produced
    watt_hours_last_7_days: (
        int  #: Energy produced in previous 7 days (not including today)
    )
    watt_hours_today: int  #: Energy produced since start of day
    watts_now: int  #: Current Power production

    @classmethod
    def from_v1_api(cls, data: dict[str, Any]) -> EnvoySystemProduction:
        """Initialize from the V1 API.

        :param data:  JSON reply from api/v1/production endpoint
        :return: Lifetime, last seven days, todays energy and current power for solar production
        """
        return cls(
            watt_hours_lifetime=data["wattHoursLifetime"],
            watt_hours_last_7_days=data["wattHoursSevenDays"],
            watt_hours_today=data["wattHoursToday"],
            watts_now=data["wattsNow"],
        )

    @classmethod
    def from_production(cls, data: dict[str, Any]) -> EnvoySystemProduction:
        """Initialize from the production API.

        :param data: JSON reply from /production endpoint
        :return: Lifetime, last seven days, todays energy and current power for solar production
        """
        all_production = data["production"]

        eim = find_dict_by_key(all_production, "eim")
        inverters = find_dict_by_key(all_production, "inverters")

        # This is backwards compatible with envoy_reader
        # envoy metered without configured CT has whLifetime and wNow in inverters
        # whLastSevenDays and whToday are incorrect for both so either can be used
        now_source = eim if eim["activeCount"] else inverters

        return cls(
            watt_hours_lifetime=int(round(now_source["whLifetime"])),
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

    @classmethod
    def from_production_phase(
        cls, data: dict[str, Any], phase: int
    ) -> EnvoySystemProduction | None:
        """Initialize from the production API phase data.

        :param data: JSON reply from /production endpoint
        :param phase: Index (0-2) in [lines] segment for which to return data
        :return: Lifetime, last seven days, todays energy and current power for production phase
        """
        all_production = data["production"]
        eim = find_dict_by_key(all_production, "eim")

        # if {production[type=eim]{Lines[]} or phase is missing return None
        phases = eim.get("lines")
        if not phases or phase >= len(phases):
            return None

        phase_data = phases[phase]
        return cls(
            watt_hours_lifetime=int(round(phase_data.get("whLifetime") or 0)),
            watt_hours_last_7_days=int(round(phase_data.get("whLastSevenDays") or 0)),
            watt_hours_today=int(round(phase_data.get("whToday") or 0)),
            watts_now=int(round(phase_data.get("wNow") or 0)),
        )
