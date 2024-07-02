"""Model for the Envoy's consumption data."""

# Data Source: URL_PRODUCTION

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EnvoySystemConsumption:
    """Model for the Envoy's (total, house) consumption data."""

    watt_hours_lifetime: int  #: Lifetime Energy consumed (total-consumption, house)
    watt_hours_last_7_days: (
        int  #: Energy consumed in previous 7 days (not including today)
    )
    watt_hours_today: (
        int  #: Energy consumption since start of day (total-consumption, house)
    )
    watts_now: int  #: Current Power consumption (total-consumption, house)

    @classmethod
    def from_production(cls, data: dict[str, Any]) -> EnvoySystemConsumption:
        """Initialize from the production API.

        :param data: JSON reply from /production endpoint
        :return: Lifetime, last 7 days, todays energy and current power for total-consumption
        """
        consumption = data["consumption"][0]
        return cls(
            watt_hours_lifetime=int(round(consumption["whLifetime"])),
            watt_hours_last_7_days=int(round(consumption["whLastSevenDays"])),
            watt_hours_today=int(round(consumption["whToday"])),
            watts_now=int(round(consumption["wNow"])),
        )

    @classmethod
    def from_production_phase(
        cls, data: dict[str, Any], phase: int
    ) -> EnvoySystemConsumption | None:
        """Initialize from the production API phase data.

        :param data: JSON reply from /production endpoint
        :param phase: Index (0-2) in [lines] segment for which to return data
        :return: Lifetime, last 7 days, todays energy and current power for total-consumption phase
        """
        # get first consumtpion section which is the total-consumption one.
        consumption = data["consumption"][0]
        phases = consumption.get("lines")

        # Only return data if phase is present.
        if not phases or phase >= len(phases):
            return None

        phase_data = phases[phase]
        return cls(
            watt_hours_lifetime=int(round(phase_data["whLifetime"])),
            watt_hours_last_7_days=int(round(phase_data["whLastSevenDays"])),
            watt_hours_today=int(round(phase_data["whToday"])),
            watts_now=int(round(phase_data["wNow"])),
        )
