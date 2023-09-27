import enum

import httpx
from awesomeversion import AwesomeVersion

# Versions
LEGACY_ENVOY_VERSION = AwesomeVersion("3.9.0")
ENSEMBLE_MIN_VERSION = AwesomeVersion("5.0.0")
AUTH_TOKEN_MIN_VERSION = AwesomeVersion("7.0.0")

# System Production
URL_PRODUCTION_INVERTERS = "/api/v1/production/inverters"
URL_PRODUCTION_V1 = "/api/v1/production"
URL_PRODUCTION_JSON = "/production.json"
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


LOCAL_TIMEOUT = httpx.Timeout(
    # The envoy can be slow to respond but fast to connect to we
    # need to set a long timeout for the read and a short timeout
    # for the connect
    timeout=10.0,
    read=60.0,
)


class SupportedFeatures(enum.IntFlag):
    INVERTERS = 1
    METERING = 2
    TOTAL_CONSUMPTION = 4
    NET_CONSUMPTION = 8
    ENCHARGE = 16
    ENPOWER = 32
    PRODUCTION = 64
    TARIFF = 128
