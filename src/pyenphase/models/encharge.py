"""Model for the Encharge/IQ Battery."""
# Data Source: URL_ENSEMBLE_INVENTORY (primary) & URL_ENCHARGE_BATTERY

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EnvoyEncharge:
    """Model for the Encharge/IQ battery."""

    admin_state: int
    admin_state_str: str
    bmu_firmware_version: str
    comm_level_2_4_ghz: int
    comm_level_sub_ghz: int
    communicating: bool
    dc_switch_off: bool
    encharge_capacity: int
    encharge_revision: int
    firmware_loaded_date: int
    firmware_version: str
    installed_date: int
    last_report_date: int
    led_status: int
    max_cell_temp: int
    operating: bool
    part_number: str
    percent_full: int
    serial_number: str
    temperature: int
    temperature_unit: str
    zigbee_dongle_fw_version: str
    apparent_power_mva: int
    real_power_mw: int
    soc: int

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> EnvoyEncharge:
        """Initialize from the API."""
        return cls(
            admin_state=data["admin_state"],
            admin_state_str=data["admin_state_str"],
            bmu_firmware_version=data["bmu_fw_version"],
            comm_level_2_4_ghz=data["comm_level_2_4_ghz"],
            comm_level_sub_ghz=data["comm_level_sub_ghz"],
            communicating=data["communicating"],
            dc_switch_off=data["dc_switch_off"],
            encharge_capacity=data["encharge_capacity"],
            encharge_revision=data["encharge_rev"],
            firmware_loaded_date=data["img_load_date"],
            firmware_version=data["img_pnum_running"],
            installed_date=data["installed"],
            last_report_date=data["last_rpt_date"],
            led_status=data["led_status"],
            max_cell_temp=data["maxCellTemp"],
            operating=data["operating"],
            part_number=data["part_num"],
            percent_full=data["percentFull"],
            serial_number=data["serial_num"],
            temperature=data["temperature"],
            temperature_unit="C",
            zigbee_dongle_fw_version=data["zigbee_dongle_fw_version"],
            apparent_power_mva=data["power"]["apparent_power_mva"],
            real_power_mw=data["power"]["real_power_mw"],
            soc=data["power"]["soc"],
        )
