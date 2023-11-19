"""Model for the Envoy's CT Meters."""
from __future__ import annotations

from enum import StrEnum
from typing import TypedDict


class EnvoyPhaseMode(StrEnum):
    SPLIT = "split"
    THREE = "three"
    SINGLE = "single"


class CtType(StrEnum):
    PRODUCTION = "production"
    NET_CONSUMPTION = "net-consumption"
    TOTAL_CONSUMPTION = "total-consumption"


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
