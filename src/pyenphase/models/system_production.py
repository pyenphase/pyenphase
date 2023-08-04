"""Model for the Envoy's production data."""
# Data Source: URL_PRODUCTION

from typing import Any


class EnvoySystemProduction:
    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize."""
        self._data = data

    def __repr__(self) -> str:
        """Return a representation of the system production."""
        return (
            f"<EnvoySystemProduction: "
            f"watt_hours_lifetime={self.watt_hours_lifetime} "
            f"watt_hours_last_7_days={self.watt_hours_last_7_days} "
            f"watt_hours_today={self.watt_hours_today} "
            f"watts_now={self.watts_now}"
            ">"
        )

    @property
    def watt_hours_lifetime(self) -> int:
        """Return the lifetime production in watt hours."""
        return self._data["wattHoursLifetime"]

    @property
    def watt_hours_last_7_days(self) -> int:
        """Return the production in watt hours for the last 7 days."""
        return self._data["wattHoursSevenDays"]

    @property
    def watt_hours_today(self) -> int:
        """Return the production in watt hours for today."""
        return self._data["wattHoursToday"]

    @property
    def watts_now(self) -> int:
        """Return the current production in watts."""
        return self._data["wattsNow"]
