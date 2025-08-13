"""Model for the IQ Meter Collar."""

# Data Source: URL_ENSEMBLE_INVENTORY

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Required keys for IQ Meter Collar inventories
COLLAR_REQUIRED_KEYS: frozenset[str] = frozenset(
    {
        "admin_state",
        "admin_state_str",
        "communicating",
        "img_load_date",
        "img_pnum_running",
        "installed",
        "last_rpt_date",
        "part_num",
        "serial_num",
        "temperature",
        "mid_state",
        "grid_state",
        "control_error",
        "collar_state",
    }
)


@dataclass(slots=True)
class EnvoyCollar:
    """Model for the Enphase IQ Meter Collar."""

    admin_state: int
    admin_state_str: str
    firmware_loaded_date: int
    firmware_version: str
    installed_date: int
    last_report_date: int
    communicating: bool
    mid_state: str
    grid_state: str
    part_number: str
    serial_number: str
    temperature: int
    temperature_unit: str
    control_error: int
    collar_state: str

    @classmethod
    def from_api(cls, inventory: dict[str, Any]) -> EnvoyCollar | None:
        """Initialize from the API."""
        missing_keys = list(COLLAR_REQUIRED_KEYS - set(inventory))
        if missing_keys:
            return None
        return cls(
            admin_state=inventory["admin_state"],
            admin_state_str=inventory["admin_state_str"],
            communicating=inventory["communicating"],
            firmware_loaded_date=inventory["img_load_date"],
            firmware_version=inventory["img_pnum_running"],
            installed_date=inventory["installed"],
            last_report_date=inventory["last_rpt_date"],
            part_number=inventory["part_num"],
            serial_number=inventory["serial_num"],
            temperature=inventory["temperature"],
            temperature_unit="C",
            mid_state=inventory["mid_state"],
            grid_state=inventory["grid_state"],
            control_error=inventory["control_error"],
            collar_state=inventory["collar_state"],
        )
