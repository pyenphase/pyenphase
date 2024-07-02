"""Model for the Encharge/IQ Battery."""

# Data Source: URL_ENSEMBLE_INVENTORY (primary) & URL_ENCHARGE_BATTERY

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EnvoyEnchargeAggregate:
    """Model for Encharge aggregate data."""

    available_energy: int
    backup_reserve: int
    state_of_charge: int
    reserve_state_of_charge: int
    configured_reserve_state_of_charge: int
    max_available_capacity: int

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> EnvoyEnchargeAggregate:
        """Initialize from the API."""
        return cls(
            available_energy=data["ENC_agg_avail_energy"],
            backup_reserve=data["ENC_agg_backup_energy"],
            state_of_charge=data["ENC_agg_soc"],
            reserve_state_of_charge=data["adjusted_backup_soc"],
            configured_reserve_state_of_charge=data["configured_backup_soc"],
            max_available_capacity=data["Enc_max_available_capacity"],
        )


@dataclass(slots=True)
class EnvoyEnchargePower:
    """Model for the Encharge/IQ battery power."""

    apparent_power_mva: int
    real_power_mw: int
    soc: int

    @classmethod
    def from_api(cls, power: dict[str, Any]) -> EnvoyEnchargePower:
        """Initialize from the API."""
        return cls(
            apparent_power_mva=power["apparent_power_mva"],
            real_power_mw=power["real_power_mw"],
            soc=power["soc"],
        )


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
    operating: bool | None
    part_number: str
    percent_full: int
    serial_number: str
    temperature: int
    temperature_unit: str
    zigbee_dongle_fw_version: str | None

    @classmethod
    def from_api(cls, inventory: dict[str, Any]) -> EnvoyEncharge:
        """Initialize from the API."""
        return cls(
            admin_state=inventory["admin_state"],
            admin_state_str=inventory["admin_state_str"],
            bmu_firmware_version=inventory["bmu_fw_version"],
            comm_level_2_4_ghz=inventory["comm_level_2_4_ghz"],
            comm_level_sub_ghz=inventory["comm_level_sub_ghz"],
            communicating=inventory["communicating"],
            dc_switch_off=inventory["dc_switch_off"],
            encharge_capacity=inventory["encharge_capacity"],
            encharge_revision=inventory["encharge_rev"],
            firmware_loaded_date=inventory["img_load_date"],
            firmware_version=inventory["img_pnum_running"],
            installed_date=inventory["installed"],
            last_report_date=inventory["last_rpt_date"],
            led_status=inventory["led_status"],
            max_cell_temp=inventory["maxCellTemp"],
            operating=inventory.get("operating"),  # Firmware 8+ does not have this key
            part_number=inventory["part_num"],
            percent_full=inventory["percentFull"],
            serial_number=inventory["serial_num"],
            temperature=inventory["temperature"],
            temperature_unit="C",
            zigbee_dongle_fw_version=inventory.get(
                "zigbee_dongle_fw_version"
            ),  # Firmware 8+ does not have this key
        )
