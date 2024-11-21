"""Python wrapper for Enphase Envoy API."""

from .auth import EnvoyTokenAuth
from .envoy import AUTH_TOKEN_MIN_VERSION, Envoy, register_updater
from .exceptions import (
    EnvoyAuthenticationError,
    EnvoyAuthenticationRequired,
    EnvoyCommunicationError,
    EnvoyError,
    EnvoyFirmwareCheckError,
    EnvoyFirmwareFatalCheckError,
    EnvoyProbeFailed,
)
from .models.acb import EnvoyACBPower, EnvoyBatteryAggregate
from .models.dry_contacts import EnvoyDryContactSettings, EnvoyDryContactStatus
from .models.encharge import EnvoyEncharge, EnvoyEnchargeAggregate, EnvoyEnchargePower
from .models.enpower import EnvoyEnpower
from .models.envoy import EnvoyData
from .models.inverter import EnvoyInverter
from .models.system_consumption import EnvoySystemConsumption
from .models.system_production import EnvoySystemProduction
from .models.tariff import EnvoyTariff

__all__ = (
    AUTH_TOKEN_MIN_VERSION,
    "register_updater",
    "Envoy",
    "EnvoyData",
    "EnvoyTokenAuth",
    "EnvoyError",
    "EnvoyCommunicationError",
    "EnvoyFirmwareCheckError",
    "EnvoyFirmwareFatalCheckError",
    "EnvoyAuthenticationError",
    "EnvoyAuthenticationRequired",
    "EnvoyProbeFailed",
    "EnvoyInverter",
    "EnvoySystemConsumption",
    "EnvoySystemProduction",
    "EnvoyEncharge",
    "EnvoyEnchargeAggregate",
    "EnvoyEnchargePower",
    "EnvoyEnpower",
    "EnvoyACBPower",
    "EnvoyBatteryAggregate",
    "EnvoyDryContactSettings",
    "EnvoyDryContactStatus",
    "EnvoyTariff",
)
