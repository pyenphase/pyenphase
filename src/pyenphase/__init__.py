"""Python wrapper for Enphase Envoy API."""

from .auth import EnvoyTokenAuth
from .envoy import AUTH_TOKEN_MIN_VERSION, Envoy, register_updater
from .exceptions import (
    EnvoyAuthenticationError,
    EnvoyAuthenticationRequired,
    EnvoyClientClosedError,
    EnvoyCommunicationError,
    EnvoyError,
    EnvoyFeatureNotAvailable,
    EnvoyFirmwareCheckError,
    EnvoyFirmwareFatalCheckError,
    EnvoyHTTPStatusError,
    EnvoyPoorDataQuality,
    EnvoyProbeFailed,
)
from .models.acb import EnvoyACB, EnvoyACBPower, EnvoyBatteryAggregate
from .models.c6combiner import EnvoyC6CC
from .models.collar import EnvoyCollar
from .models.dry_contacts import EnvoyDryContactSettings, EnvoyDryContactStatus
from .models.encharge import EnvoyEncharge, EnvoyEnchargeAggregate, EnvoyEnchargePower
from .models.enpower import EnvoyEnpower
from .models.envoy import EnvoyData
from .models.generator import (
    EnvoyGenerator,
    EnvoyGeneratorConfig,
    EnvoyGeneratorMode,
    EnvoyGeneratorSchedule,
)
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
    "EnvoyClientClosedError",
    "EnvoyCommunicationError",
    "EnvoyFirmwareCheckError",
    "EnvoyFirmwareFatalCheckError",
    "EnvoyAuthenticationError",
    "EnvoyAuthenticationRequired",
    "EnvoyHTTPStatusError",
    "EnvoyProbeFailed",
    "EnvoyFeatureNotAvailable",
    "EnvoyPoorDataQuality",
    "EnvoyInverter",
    "EnvoySystemConsumption",
    "EnvoySystemProduction",
    "EnvoyEncharge",
    "EnvoyEnchargeAggregate",
    "EnvoyEnchargePower",
    "EnvoyEnpower",
    "EnvoyGenerator",
    "EnvoyGeneratorConfig",
    "EnvoyGeneratorMode",
    "EnvoyGeneratorSchedule",
    "EnvoyACB",
    "EnvoyACBPower",
    "EnvoyBatteryAggregate",
    "EnvoyDryContactSettings",
    "EnvoyDryContactStatus",
    "EnvoyCollar",
    "EnvoyC6CC",
    "EnvoyTariff",
)
