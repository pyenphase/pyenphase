"""Model for the Envoy's CT Meters."""
from __future__ import annotations

from enum import StrEnum


class EnvoyPhaseMode(StrEnum):
    SPLIT = "split"
    THREE = "three"
    SINGLE = "single"


class EnvoyMeterType(StrEnum):
    PRODUCTION = "production"
    NETCONSUMPTION = "net-consumption"
    TOTALCONSUMPTION = "total-consumption"


class EnvoyMeterState(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class EnvoyMeteringStatus(StrEnum):
    NORMAL = "normal"
    NOTMETERING = "not-metering"
    CHECKWIRING = "check-wiring"


class EnvoyMeterStatusFlags(StrEnum):
    PODUCTIONIMBALANCE = "production-imbalance"
    NEGATIVEPRODUCTION = "negative-production"
    POWERONUNUSEDPHASE = "power-on-unused-phase"
    NEGATIVECONSUMPTION = "negative-total-consumption"


class EnvoyMeterKeys(StrEnum):
    EID = "eid"
    STATE = "state"
    TYPE = "measurementType"
    PHASEMODE = "phaseMode"
    PHASECOUNT = "phaseCount"
    METERINGSTATUS = "meteringStatus"
    FLAGS = "statusFlags"
