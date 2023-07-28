"""Model for the Enpower dry contact relays."""
# Data Source: URL_DRY_CONTACT_STATUS, URL_DRY_CONTACT_SETTINGS

from typing import Any


class EnvoyDryContact:
    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize."""
        self._data = data

    @property
    def id(self) -> str:
        """Return the relay ID."""
        return self._data["id"]

    @property
    def status(self) -> str:
        """Return the relay status (opened/closed)."""
        return self._data["status"]

    @property
    def type(self) -> str:
        """Return the relay type (NONE/PV/LOAD)."""
        return self._data["type"]

    @property
    def grid_action(self) -> str:
        """Return the relay action when on-grid (apply/shed/none)."""
        return self._data["grid_action"]

    @property
    def micro_grid_action(self) -> str:
        """Return the relay action when on batteries/micro-grid (apply/shed/none)."""
        return self._data["micro_grid_action"]

    @property
    def generator_action(self) -> str:
        """Return the relay action when on generator (apply/shed/none)."""
        return self._data["generator_action"]

    @property
    def override(self) -> bool:
        """Return the relay override."""
        return self._data["override"]

    @property
    def manual_override(self) -> bool:
        """Return the relay manual override."""
        return self._data["manual_override"]

    @property
    def load_name(self) -> str:
        """Return the friendly name assigned to the relay."""
        return self._data["load_name"]

    @property
    def mode(self) -> str:
        """Return the relay mode (manual/soc)."""
        return self._data["mode"]

    @property
    def soc_high(self) -> float:
        """Return the state of charge high limit."""
        return self._data["soc_high"]

    @property
    def soc_low(self) -> float:
        """Return the state of charge low limit."""
        return self._data["soc_low"]

    @property
    def pv_serial_numbers(self) -> list[str]:
        """Return the list of PV serial numbers assigned to the relay."""
        return self._data["pv_serial_numbers"]

    @property
    def priority(self) -> float:
        """Return the relay priority."""
        # Not listed in API docs but present in data
        return self._data["priority"]

    @property
    def essential_end_time(self) -> float:
        """Return the essential end time."""
        # Not listed in API docs but present in data
        return self._data["essential_end_time"]

    @property
    def essential_start_time(self) -> float:
        """Return the essential start time."""
        # Not listed in API docs but present in data
        return self._data["essential_start_time"]
