"""Model for the Enpower/IQ System Controller."""

# Data Source: URL_ENSEMBLE_INVENTORY
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EnvoyEnpower:
    """Model for the Enpower/IQ System Controller."""

    grid_mode: str
    admin_state: int
    admin_state_str: str
    comm_level_2_4_ghz: int
    comm_level_sub_ghz: int
    communicating: bool
    firmware_loaded_date: int
    firmware_version: str
    installed_date: int
    last_report_date: int
    mains_admin_state: str
    mains_oper_state: str
    operating: bool | None
    part_number: str
    serial_number: str
    temperature: int
    temperature_unit: str
    zigbee_dongle_fw_version: str | None

    @classmethod
    def from_api(
        cls,
        enpower: dict[str, Any],
    ) -> EnvoyEnpower:
        """Initialize from the API."""
        return cls(
            grid_mode=enpower["Enpwr_grid_mode"],
            admin_state=enpower["admin_state"],
            admin_state_str=enpower["admin_state_str"],
            comm_level_2_4_ghz=enpower["comm_level_2_4_ghz"],
            comm_level_sub_ghz=enpower["comm_level_sub_ghz"],
            communicating=enpower["communicating"],
            firmware_loaded_date=enpower["img_load_date"],
            firmware_version=enpower["img_pnum_running"],
            installed_date=enpower["installed"],
            last_report_date=enpower["last_rpt_date"],
            mains_admin_state=enpower["mains_admin_state"],
            mains_oper_state=enpower["mains_oper_state"],
            operating=enpower.get("operating"),  # Firmware 8+ does not have this field
            part_number=enpower["part_num"],
            serial_number=enpower["serial_num"],
            temperature=enpower["temperature"],
            temperature_unit="F",
            zigbee_dongle_fw_version=enpower.get(
                "zigbee_dongle_fw_version"
            ),  # Firmware 8+ does not have this field
        )
