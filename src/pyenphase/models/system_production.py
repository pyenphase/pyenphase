"""Model for the Envoy's production data."""
# Data Source: URL_PRODUCTION

from typing import Any


class EnvoySystemProduction:
    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize."""
        self._data = data

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
