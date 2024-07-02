"""Model for the Enpower dry contact relays."""

# Data Source: URL_DRY_CONTACT_SETTINGS (primary) & URL_DRY_CONTACT_STATUS

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class DryContactStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class DryContactAction(StrEnum):
    APPLY = "apply"
    SHED = "shed"
    SCHEDULE = "schedule"
    NONE = "none"


class DryContactType(StrEnum):
    NONE = "NONE"
    PV = "PV"
    LOAD = "LOAD"


class DryContactMode(StrEnum):
    MANUAL = "manual"
    STATE_OF_CHARGE = "soc"


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
            status=DryContactStatus(relay["status"]),
        )


@dataclass(slots=True)
class EnvoyDryContactSettings:
    """Model for the Enpower dry contact relay settings."""

    id: str
    black_start: float | None
    essential_end_time: float | None
    essential_start_time: float | None
    generator_action: DryContactAction
    grid_action: DryContactAction
    load_name: str
    manual_override: bool | None
    micro_grid_action: DryContactAction
    mode: DryContactMode
    override: bool
    priority: float | None
    pv_serial_nb: list[Any]
    soc_high: float
    soc_low: float
    type: DryContactType

    @classmethod
    def from_api(cls, relay: dict[str, Any]) -> EnvoyDryContactSettings:
        """Initialize from the API."""
        return cls(
            id=relay["id"],
            black_start=relay.get("black_s_start"),
            essential_end_time=relay.get("essential_end_time"),
            essential_start_time=relay.get("essential_start_time"),
            generator_action=DryContactAction(relay["gen_action"]),
            grid_action=DryContactAction(relay["grid_action"]),
            load_name=relay["load_name"],
            manual_override=(
                relay["manual_override"] == "true"
                if relay.get("manual_override")
                else None
            ),
            micro_grid_action=DryContactAction(relay["micro_grid_action"]),
            mode=DryContactMode(relay["mode"]),
            override=relay["override"] == "true",
            priority=relay.get("priority"),
            pv_serial_nb=relay["pv_serial_nb"],
            soc_high=relay["soc_high"],
            soc_low=relay["soc_low"],
            type=DryContactType(relay["type"]),
        )

    def to_api(self) -> dict[str, Any]:
        """Convert to API format."""
        retval = {
            "id": self.id,
            "gen_action": self.generator_action,
            "grid_action": self.grid_action,
            "load_name": self.load_name,
            # boolean values must be passed to the API as a lowercase string
            "manual_override": str(self.manual_override).lower(),
            "micro_grid_action": self.micro_grid_action,
            "mode": self.mode,
            "override": str(self.override).lower(),
            "pv_serial_nb": self.pv_serial_nb,
            "soc_high": self.soc_high,
            "soc_low": self.soc_low,
            "type": self.type,
        }

        if self.black_start is not None:
            retval["black_s_start"] = self.black_start
        if self.essential_start_time is not None:
            retval["essential_start_time"] = self.essential_start_time
        if self.essential_end_time is not None:
            retval["essential_end_time"] = self.essential_end_time
        if self.priority is not None:
            retval["priority"] = self.priority
        if self.manual_override is not None:
            retval["manual_override"] = self.manual_override

        return retval
