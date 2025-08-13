"""Model for the Enphase C6 Combiner."""

# Data Source: URL_ENSEMBLE_INVENTORY

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EnvoyC6CC:
    """Model for the Enphase C6 Combiner."""

    admin_state: int
    admin_state_str: str
    firmware_loaded_date: int
    firmware_version: str
    installed_date: int
    last_report_date: int
    communicating: bool
    part_number: str
    serial_number: str
    dmir_version: str

    @classmethod
    def from_api(cls, inventory: dict[str, Any]) -> EnvoyC6CC | None:
        """Initialize from the API."""
        C6CC_REQUIRED_KEYS = [
            "admin_state",
            "admin_state_str",
            "communicating",
            "img_load_date",
            "installed",
            "last_rpt_date",
            "part_num",
            "serial_num",
            "dmir_version",
        ]
        missing_keys = [key for key in C6CC_REQUIRED_KEYS if key not in inventory]
        if missing_keys:
            return None
        return cls(
            admin_state=inventory["admin_state"],
            admin_state_str=inventory["admin_state_str"],
            communicating=inventory["communicating"],
            firmware_loaded_date=inventory["img_load_date"],
            firmware_version=inventory["fw_version"],
            installed_date=inventory["installed"],
            last_report_date=inventory["last_rpt_date"],
            part_number=inventory["part_num"],
            serial_number=inventory["serial_num"],
            dmir_version=inventory["dmir_version"],
        )
