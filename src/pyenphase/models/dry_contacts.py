"""Model for the Enpower dry contact relays."""
# Data Source: URL_DRY_CONTACT_SETTINGS (primary) & URL_DRY_CONTACT_STATUS

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EnvoyDryContactStatus:
    """Model for the Enpower dry contact relay status."""

    id: str
    status: str

    @classmethod
    def from_api(cls, relay: dict[str, Any]) -> EnvoyDryContactStatus:
        """Initialize from the API."""
        return cls(
            id=relay["id"],
            status=relay["status"],
        )


@dataclass(slots=True)
class EnvoyDryContactSettings:
    """Model for the Enpower dry contact relay settings."""

    id: str
    black_start: float
    essential_end_time: float
    essential_start_time: float
    generator_action: str
    grid_action: str
    load_name: str
    manual_override: bool
    micro_grid_action: str
    mode: str
    override: bool
    priority: float
    pv_serial_nb: list[Any]
    soc_high: float
    soc_low: float
    type: str

    @classmethod
    def from_api(cls, relay: dict[str, Any]) -> EnvoyDryContactSettings:
        """Initialize from the API."""
        return cls(
            id=relay["id"],
            black_start=relay["black_s_start"],
            essential_end_time=relay["essential_end_time"],
            essential_start_time=relay["essential_start_time"],
            generator_action=relay["gen_action"],
            grid_action=relay["grid_action"],
            load_name=relay["load_name"],
            manual_override=relay["manual_override"] == "true",
            micro_grid_action=relay["micro_grid_action"],
            mode=relay["mode"],
            override=relay["override"] == "true",
            priority=relay["priority"],
            pv_serial_nb=relay["pv_serial_nb"],
            soc_high=relay["soc_high"],
            soc_low=relay["soc_low"],
            type=relay["type"],
        )
