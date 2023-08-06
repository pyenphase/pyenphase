import enum
import logging
from typing import Any

import httpx
import orjson
from awesomeversion import AwesomeVersion
from envoy_utils.envoy_utils import EnvoyUtils
from tenacity import retry, retry_if_exception_type, wait_random_exponential

from .auth import EnvoyAuth, EnvoyLegacyAuth, EnvoyTokenAuth
from .const import (
    URL_ENSEMBLE_INVENTORY,
    URL_PRODUCTION,
    URL_PRODUCTION_INVERTERS,
    URL_PRODUCTION_JSON,
    URL_PRODUCTION_V1,
)
from .exceptions import (
    ENDPOINT_PROBE_EXCEPTIONS,
    EnvoyAuthenticationRequired,
    EnvoyProbeFailed,
)
from .firmware import EnvoyFirmware, EnvoyFirmwareCheckError
from .models.envoy import EnvoyData
from .models.inverter import EnvoyInverter
from .models.system_consumption import EnvoySystemConsumption
from .models.system_production import EnvoySystemProduction
from .ssl import NO_VERIFY_SSL_CONTEXT

_LOGGER = logging.getLogger(__name__)

TIMEOUT = 20
LEGACY_ENVOY_VERSION = AwesomeVersion("3.9.0")
ENSEMBLE_MIN_VERSION = AwesomeVersion("5.0.0")
AUTH_TOKEN_MIN_VERSION = AwesomeVersion("7.0.0")
DEFAULT_HEADERS = {
    "Accept": "application/json",
}


class SupportedFeatures(enum.IntFlag):
    INVERTERS = 1
    METERING = 2
    TOTAL_CONSUMPTION = 4
    NET_CONSUMPTION = 8
    DRY_CONTACTS = 16
    ENCHARGE = 32
    ENPOWER = 64


class Envoy:
    """Class for communicating with an envoy."""

    def __init__(
        self,
        host: str,
        client: httpx.AsyncClient | None = None,
        timeout: float | None = None,
    ) -> None:
        """Initialize the Envoy class."""
        # We use our own httpx client session so we can disable SSL verification (Envoys use self-signed SSL certs)
        self._timeout = timeout or TIMEOUT
        self._client = client or httpx.AsyncClient(
            verify=NO_VERIFY_SSL_CONTEXT
        )  # nosec
        self.auth: EnvoyAuth | None = None
        self._host = host
        self._firmware = EnvoyFirmware(self._client, self._host)
        self._supported_features: SupportedFeatures = SupportedFeatures(0)
        self._production_endpoint: str | None = None
        self._consumption_endpoint: str | None = None
        self.data: EnvoyData | None = None

    @retry(
        retry=retry_if_exception_type(EnvoyFirmwareCheckError),
        wait=wait_random_exponential(multiplier=2, max=10),
    )
    async def setup(self) -> None:
        """Obtain the firmware version for later Envoy authentication."""
        await self._firmware.setup()

    async def authenticate(
        self,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
    ) -> None:
        """Authenticate to the Envoy based on firmware version."""
        if self._firmware.version < AUTH_TOKEN_MIN_VERSION:
            # Envoy firmware using old envoy/installer authentication
            _LOGGER.debug(
                "Authenticating to Envoy using envoy/installer authentication"
            )
            full_serial = self._firmware.serial
            if not username or username == "installer":
                username = "installer"
                password = EnvoyUtils.get_password(full_serial, username)
            elif username == "envoy" and not password:
                # The default password for the envoy user is the first 6 digits of the serial number
                assert full_serial is not None, "Serial must be set"  # nosec
                password = full_serial[:6]

            if username and password:
                self.auth = EnvoyLegacyAuth(self.host, username, password)

        else:
            # Envoy firmware using new token authentication
            _LOGGER.debug("Authenticating to Envoy using token authentication")
            if token or (username and password):
                # Always pass all the data to the token auth class, even if some of it is None
                # so that we can refresh the token if needed
                self.auth = EnvoyTokenAuth(
                    self.host,
                    cloud_username=username,
                    cloud_password=password,
                    envoy_serial=self._firmware.serial,
                    token=token,
                )

        if not self.auth:
            _LOGGER.error(
                "You must include username/password or token to authenticate to the Envoy."
            )
            raise EnvoyAuthenticationRequired("Could not setup authentication object.")

        await self.auth.setup(self._client)

    @retry(
        retry=retry_if_exception_type(
            (httpx.NetworkError, httpx.TimeoutException, httpx.RemoteProtocolError)
        ),
        wait=wait_random_exponential(multiplier=2, max=3),
    )
    async def request(self, endpoint: str) -> Any:
        """Make a request to the Envoy."""
        if self.auth is None:
            raise EnvoyAuthenticationRequired(
                "You must authenticate to the Envoy before making requests."
            )

        url = self.auth.get_endpoint_url(endpoint)
        response = await self._client.get(
            url,
            headers={**DEFAULT_HEADERS, **self.auth.headers},
            cookies=self.auth.cookies,
            follow_redirects=True,
            auth=self.auth.auth,
            timeout=self._timeout,
        )
        try:
            return orjson.loads(response.text)
        except orjson.JSONDecodeError as e:
            _LOGGER.debug(
                "Unable to decode response from Envoy endpoint %s: %s", url, e
            )
            raise

    @property
    def host(self) -> str:
        """Return the Envoy host."""
        return self._host

    @property
    def firmware(self) -> AwesomeVersion:
        """Return the Envoy firmware version."""
        return self._firmware.version

    @property
    def part_number(self) -> str | None:
        """Return the Envoy part number."""
        return self._firmware.part_number

    @property
    def serial_number(self) -> str | None:
        """Return the Envoy serial number."""
        return self._firmware.serial

    async def probe(self) -> None:
        """Probe for model and supported features."""
        for possible_endpoint in (URL_PRODUCTION, URL_PRODUCTION_JSON):
            try:
                production_json: dict[str, Any] = await self.request(possible_endpoint)
            except ENDPOINT_PROBE_EXCEPTIONS as e:
                _LOGGER.debug(
                    "Production endpoint not found at %s: %s", possible_endpoint, e
                )
                continue
            else:
                production: list[
                    dict[str, str | float | int]
                ] | None = production_json.get("production")
                if production:
                    for type_ in production:
                        if type_["type"] == "eim" and type_["activeCount"]:
                            self._supported_features |= SupportedFeatures.METERING
                            self._production_endpoint = possible_endpoint
                            break

                consumption: list[
                    dict[str, str | float | int]
                ] | None = production_json.get("consumption")
                if consumption:
                    for meter in consumption:
                        meter_type = meter["measurementType"]
                        if meter_type == "total-consumption":
                            self._supported_features |= (
                                SupportedFeatures.TOTAL_CONSUMPTION
                            )
                            if not self._consumption_endpoint:
                                self._consumption_endpoint = possible_endpoint
                        elif meter_type == "net-consumption":
                            self._supported_features |= (
                                SupportedFeatures.NET_CONSUMPTION
                            )
                            if not self._consumption_endpoint:
                                self._consumption_endpoint = possible_endpoint

                break

        if not self._production_endpoint:
            try:
                await self.request(URL_PRODUCTION_V1)
            except ENDPOINT_PROBE_EXCEPTIONS as e:
                _LOGGER.debug(
                    "Production endpoint not found at %s: %s", URL_PRODUCTION_V1, e
                )
            else:
                self._production_endpoint = URL_PRODUCTION_V1

        if not self._production_endpoint:
            raise EnvoyProbeFailed("Unable to determine production endpoint")

        try:
            await self.request(URL_PRODUCTION_INVERTERS)
        except ENDPOINT_PROBE_EXCEPTIONS as e:
            _LOGGER.debug("Inverters endpoint not found: %s", e)
        else:
            self._supported_features |= SupportedFeatures.INVERTERS

        # Check for various Ensemble support
        if self._firmware.version >= ENSEMBLE_MIN_VERSION:
            # The Ensemble Inventory endpoint will tell us if we have Enpower or Encharge support
            try:
                result = await self.request(URL_ENSEMBLE_INVENTORY)
            except ENDPOINT_PROBE_EXCEPTIONS as e:
                _LOGGER.debug("Ensemble Inventory endpoint not found: %s", e)
            else:
                if not result:
                    # Newer firmware with no Ensemble devices returns an empty list
                    _LOGGER.debug("No Ensemble devices found")
                    return

                for item in result:
                    if item["type"] == "ENPOWER":
                        self._supported_features |= SupportedFeatures.ENPOWER
                    if item["type"] == "ENCHARGE":
                        self._supported_features |= SupportedFeatures.ENCHARGE
        else:
            _LOGGER.debug("Firmware too old for Ensemble support")

    async def update(self) -> EnvoyData:
        """Update data."""
        if not self._production_endpoint:
            await self.probe()

        if not self._production_endpoint:
            raise EnvoyProbeFailed("Unable to determine production endpoint")

        production_endpoint = self._production_endpoint
        consumption_endpoint = self._consumption_endpoint
        supported_features = self._supported_features

        production_data = await self.request(production_endpoint)
        raw = {"production": production_data}
        if consumption_endpoint == production_endpoint:
            consumption_data = production_data
        elif consumption_endpoint:
            consumption_data = await self.request(consumption_endpoint)
            raw["consumption"] = consumption_data

        inverters: dict[str, EnvoyInverter] = {}

        if production_endpoint in (URL_PRODUCTION, URL_PRODUCTION_JSON):
            system_production = EnvoySystemProduction.from_production(production_data)
        else:
            # Production endpoint is URL_PRODUCTION_V1
            system_production = EnvoySystemProduction.from_v1_api(production_data)

        system_consumption: EnvoySystemConsumption | None = None
        if consumption_endpoint:
            system_consumption = EnvoySystemConsumption.from_production(
                consumption_data
            )

        if supported_features & SupportedFeatures.INVERTERS:
            inverters_data: list[dict[str, Any]] = await self.request(
                URL_PRODUCTION_INVERTERS
            )
            inverters = {
                inverter["serialNumber"]: EnvoyInverter.from_v1_api(inverter)
                for inverter in inverters_data
            }
            raw["inverters"] = inverters_data

        data = EnvoyData(
            system_production=system_production,
            system_consumption=system_consumption,
            inverters=inverters,
            # Raw data is exposed so we can __eq__ the data to see if
            # anything has changed and consumers of the library can
            # avoid dispatching data if nothing has changed.
            raw=raw,
        )
        self.data = data
        return data
