"""Model for the Envoy's CT Meters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypedDict


class EnvoyPhaseMode(StrEnum):
    SPLIT = "split"
    THREE = "three"
    SINGLE = "single"


class CtType(StrEnum):
    PRODUCTION = "production"
    NET_CONSUMPTION = "net-consumption"
    TOTAL_CONSUMPTION = "total-consumption"
    STORAGE = "storage"


class CtState(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class CtMeterStatus(StrEnum):
    NORMAL = "normal"
    NOT_METERING = "not-metering"
    CHECK_WIRING = "check-wiring"


class CtStatusFlags(StrEnum):
    PODUCTION_IMBALANCE = "production-imbalance"
    NEGATIVE_PRODUCTION = "negative-production"
    POWER_ON_UNUSED_PHASE = "power-on-unused-phase"
    NEGATIVE_TOTAL_CONSUMPTION = "negative-total-consumption"


class CtMeterData(TypedDict):
    eid: str
    state: CtState
    measurementType: CtType
    phaseMode: EnvoyPhaseMode
    phaseCount: int
    meteringStatus: CtMeterStatus
    statusFlags: list[CtStatusFlags]


@dataclass(slots=True)
class EnvoyMeterData:
    """Model for the Envoy's CT meter data."""

    eid: str  #: CT meter identifier
    timestamp: int  #: Time of measurement
    energy_delivered: int  #: Lifetime Energy delivered through CT
    energy_received: int  #: Lifetime Energy received through CT
    active_power: int  #: Current power exchang through CT, positive is delivering, negative is receiving
    power_factor: float  #: Power factor reported for CT measurement
    voltage: float  #: Voltage on circuit, when multiphase sum of voltage of individual phases
    current: float  #: current measured by CT
    frequency: float  #: frequency measured by CT
    state: CtState | None  #: Actual State of CT
    measurement_type: CtType | None  #: Measurement type configured for CT
    metering_status: CtMeterStatus | None  #: CT Measurement status
    status_flags: list[CtStatusFlags] | None  #: CT status flags.

    @classmethod
    def from_api(
        cls, data: dict[str, Any], meter_status: CtMeterData
    ) -> EnvoyMeterData:
        """Return CT meter data from /ivp/meters and ivp/meters/reading json."""
        return cls(
            eid=data["eid"],
            timestamp=data["timestamp"],
            energy_delivered=int(round(data["actEnergyDlvd"])),
            energy_received=int(round(data["actEnergyRcvd"])),
            active_power=int(round(data["activePower"])),
            power_factor=data["pwrFactor"],
            voltage=data["voltage"],
            current=data["current"],
            frequency=data["freq"],
            state=meter_status["state"],
            measurement_type=meter_status["measurementType"],
            metering_status=meter_status["meteringStatus"],
            status_flags=meter_status["statusFlags"],
        )

    @classmethod
    def from_phase(
        cls, data: dict[str, Any], meter_status: CtMeterData, phase: int
    ) -> EnvoyMeterData | None:
        """Return CT meter phase data from /ivp/meters and ivp/meters/reading json."""
        if "channels" not in data:
            return None
        # phase data is in channels list
        channels = data["channels"]
        if len(channels) <= phase:
            return None

        return cls.from_api(channels[phase], meter_status)
