"""Model for the Encharge/IQ Battery."""

from typing import Any


class EnvoyEncharge:
    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize."""
        self._data = data

    @property
    def admin_state(self) -> int:
        """Return the current admin state."""
        return self._data["admin_state"]

    @property
    def admin_state_str(self) -> str:
        """Return the current admin state as a string."""
        return self._data["admin_state_str"]

    @property
    def bmu_firmware_version(self) -> str:
        """Return the BMU firmware version."""
        return self._data["bmu_fm_version"]

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
        """Return if the Encharge is communicating with the Envoy."""
        return self._data["communicating"]

    @property
    def dc_switch_off(self) -> bool:
        """Return if the DC switch is off."""
        return self._data["dc_switch_off"]

    @property
    def encharge_capacity(self) -> int:
        """Return the Encharge battery capacity."""
        return self._data["encharge_capacity"]

    @property
    def encharge_revision(self) -> int:
        """Return the Encharge hardware revision."""
        return self._data["encharge_revision"]

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
        """Return the date the Encharge was installed."""
        return self._data["installed"]

    @property
    def last_report_date(self) -> int:
        """Return the timestamp when the Encharge last sent a report."""
        return self._data["last_rpt_date"]

    @property
    def led_status(self) -> int:
        """Return the current LED status."""
        return self._data["led_status"]

    @property
    def max_cell_temp(self) -> int:
        """Return the maximum cell temperature."""
        # Encharge reports temperatures in Celsius
        return self._data["max_cell_temp"]

    @property
    def operating(self) -> bool:
        """Return if the Encharge is operating."""
        return self._data["operating"]

    @property
    def part_number(self) -> str:
        """Return the Encharge part number."""
        return self._data["part_num"]

    @property
    def percent_full(self) -> int:
        """Return the current battery charge level."""
        return self._data["percent_full"]

    @property
    def serial_number(self) -> str:
        """Return the Encharge serial number."""
        return self._data["serial_num"]

    @property
    def temperature(self) -> int:
        """Return the current battery temperature."""
        # Encharge reports temperatures in Celsius
        return self._data["temperature"]

    @property
    def temperature_unit(self) -> str:
        return "C"

    @property
    def zigbee_dongle_fw_version(self) -> str:
        """Return the Zigbee dongle firmware version."""
        return self._data["zigbee_dongle_fw_version"]
