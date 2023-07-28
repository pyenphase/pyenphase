"""Model for the Enpower/IQ System Controller."""

# Data Source: URL_ENSEMBLE_INVENTORY

from typing import Any


class EnvoyEnpower:
    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize."""
        self._data = data

    @property
    def grid_mode(self) -> str:
        """Return the current grid mode."""
        return self._data["Enpwr_grid_mode"]

    @property
    def admin_state(self) -> int:
        """Return the current admin state."""
        return self._data["admin_state"]

    @property
    def admin_state_str(self) -> str:
        """Return the current admin state as a string."""
        return self._data["admin_state_str"]

    @property
    def comm_level_2_4_ghz(self) -> int:
        """Return the current 2.4GHz communication level."""
        return self._data["comm_level_2_4_ghz"]

    @property
    def comm_level_sub_ghz(self) -> int:
        """Return the current sub-GHz communication level."""
        return self._data["comm_level_sub_ghz"]

    @property
    def communicating(self) -> bool:
        """Return if the Enpower is communicating with the Envoy."""
        return self._data["communicating"]

    @property
    def firmware_loaded_date(self) -> int:
        """Return the date the firmware image was loaded."""
        return self._data["img_load_date"]

    @property
    def firmware_version(self) -> str:
        """Return the running firmware image version."""
        return self._data["img_pnum_running"]

    @property
    def installed_date(self) -> int:
        """Return the date the Enpower was installed."""
        return self._data["installed"]

    @property
    def last_report_date(self) -> int:
        """Return the timestamp when the Enpower last sent a report."""
        return self._data["last_rpt_date"]

    @property
    def mains_admin_state(self) -> int:
        """Return the current mains admin state."""
        return self._data["mains_admin_state"]

    @property
    def mains_oper_state(self) -> int:
        """Return the current mains operating state."""
        return self._data["mains_oper_state"]

    @property
    def operating(self) -> bool:
        """Return if the Enpower is operating."""
        return self._data["operating"]

    @property
    def part_number(self) -> str:
        """Return the part number."""
        return self._data["part_num"]

    @property
    def serial_number(self) -> str:
        """Return the serial number."""
        return self._data["serial_num"]

    @property
    def temperature(self) -> int:
        """Return the current temperature."""
        # Enpower temperature is returned in Fahrenheit
        return self._data["temperature"]

    @property
    def temperature_unit(self) -> str:
        return "F"

    @property
    def zigbee_dongle_fw_version(self) -> str:
        """Return the Zigbee dongle firmware version."""
        return self._data["zigbee_dongle_fw_version"]
