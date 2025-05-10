"""pyenphase constant definitions"""

import enum

import httpx
from awesomeversion import AwesomeVersion

# Versions
LEGACY_ENVOY_VERSION = AwesomeVersion("3.9.0")
ENSEMBLE_MIN_VERSION = AwesomeVersion("5.0.0")
AUTH_TOKEN_MIN_VERSION = AwesomeVersion("7.0.0")
METERED_NOCT_FALLBACK_TO_INVERTERS = AwesomeVersion("8.2.4264")

# System Production
URL_PRODUCTION_INVERTERS = "/api/v1/production/inverters"
URL_PRODUCTION_V1 = "/api/v1/production"
URL_PRODUCTION_JSON = "/production.json?details=1"
URL_PRODUCTION = "/production"

# Authentication
URL_AUTH_CHECK_JWT = "/auth/check_jwt"

# Battery and Enpower Status
URL_DRY_CONTACT_STATUS = "/ivp/ensemble/dry_contacts"
URL_DRY_CONTACT_SETTINGS = "/ivp/ss/dry_contact_settings"
URL_ENSEMBLE_INVENTORY = "/ivp/ensemble/inventory"
URL_ENSEMBLE_STATUS = "/ivp/ensemble/status"
URL_ENSEMBLE_SECCTRL = "/ivp/ensemble/secctrl"
URL_ENCHARGE_BATTERY = "/ivp/ensemble/power"
URL_GRID_RELAY = "/ivp/ensemble/relay"
URL_POWER_EXPORT = "/uvp/ss/pel_settings"
URL_TARIFF = "/admin/lib/tariff"

# Generator Configuration
URL_GEN_CONFIG = "/ivp/ss/gen_config"
URL_GEN_MODE = "/ivp/ss/gen_mode"
URL_GEN_SCHEDULE = "/ivp/ss/gen_schedule"

# Meters data
ENDPOINT_URL_METERS = "/ivp/meters"
ENDPOINT_URL_METERS_READINGS = "/ivp/meters/readings"

# Interface configuration
ENDPOINT_URL_HOME = "/home"

LOCAL_TIMEOUT = httpx.Timeout(
    # The envoy can be slow to respond but fast to connect to we
    # need to set a long timeout for the read and a short timeout
    # for the connect
    timeout=10.0,
    read=45.0,
)

# Requests should no longer retry after max delay (sec) or times since first try
MAX_REQUEST_DELAY = 50
MAX_REQUEST_ATTEMPTS = 4


class SupportedFeatures(enum.IntFlag):
    """
    Features available from Envoy

    Each supported feature maps to a specific data set or information
    that can be provided by an Envoy. Depending on actual make, firmware
    and installed components an Envoy may provide 1 or more features.
    All Envoy should at least report solar production, marked as PRODUCTION.

    Class :any:`EnvoyUpdater` updaters will set these features flags
    during the :any:`Envoy.probe` phase. During data collection by
    :any:`Envoy.update` each updater with set features will be used to
    collect the specific data.

    .. code-block:: python

        from pyenphase.const import SupportedFeatures

        # set METERING flag
        features |= SupportedFeatures.METERING

        # test features
        if features.PRODUCTION in supported_features:
            pass

        if features & SupportedFeatures.DUALPHASE:
            pass
    """

    INVERTERS = 1  #: Envoy reports solar panel inverters
    METERING = 2  #: Envoy reports active production meter
    TOTAL_CONSUMPTION = 4  #: Envoy reports total consumption
    NET_CONSUMPTION = 8  #: Envoy reports net consumption
    ENCHARGE = 16  #: Envoy reports encharge data
    ENPOWER = 32  #: Envoy reports Enpower data
    PRODUCTION = 64  #: Envoy reports solar production data
    TARIFF = 128  #: Envoy reports tariff information
    DUALPHASE = 256  #: Envoy metered is configured in split phase mode
    THREEPHASE = 512  #: Envoy metered is configured in three phase mode
    CTMETERS = 1024  #: Envoy has enabled CT meter(s)
    GENERATOR = 2048  #: Envoy reports generator data
    ACB = 4096  #: Envoy reports ACB Battery data


class PhaseNames(enum.StrEnum):
    """Electricity grid phase names."""

    PHASE_1 = "L1"  #: first phase (1, A, ..)
    PHASE_2 = "L2"  #: second phase (2, B, ..)
    PHASE_3 = "L3"  #: third phase (3, C, ..)


#: list to access :any:`PhaseNames` by numerical index.
#:
#: .. code-block:: python
#:
#:     phase_count = 2
#:     for phase in range(phase_count):
#:         print(production[PHASENAMES[phase]])
#:
PHASENAMES: list[str] = list(PhaseNames)
