import contextlib
import enum
import json
import logging
import ssl
from typing import Any

import httpx
import orjson
from awesomeversion import AwesomeVersion
from envoy_utils.envoy_utils import EnvoyUtils
from tenacity import retry, retry_if_exception_type, wait_random_exponential

from .auth import EnvoyAuth, EnvoyLegacyAuth, EnvoyTokenAuth
from .const import (
    URL_PRODUCTION,
    URL_PRODUCTION_INVERTERS,
    URL_PRODUCTION_JSON,
    URL_PRODUCTION_V1,
)
from .exceptions import EnvoyAuthenticationRequired, EnvoyProbeFailed
from .firmware import EnvoyFirmware, EnvoyFirmwareCheckError
from .models.envoy import EnvoyData
from .models.inverter import EnvoyInverter
from .models.system_production import EnvoySystemProduction

_LOGGER = logging.getLogger(__name__)

TIMEOUT = 20
LEGACY_ENVOY_VERSION = AwesomeVersion("3.9.0")
AUTH_TOKEN_MIN_VERSION = AwesomeVersion("7.0.0")
DEFAULT_HEADERS = {
    "Accept": "application/json",
}


def create_no_verify_ssl_context() -> ssl.SSLContext:
    """Return an SSL context that does not verify the server certificate.
    This is a copy of aiohttp's create_default_context() function, with the
    ssl verify turned off and old SSL versions enabled.

    https://github.com/aio-libs/aiohttp/blob/33953f110e97eecc707e1402daa8d543f38a189b/aiohttp/connector.py#L911
    """
    sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    sslcontext.check_hostname = False
    sslcontext.verify_mode = ssl.CERT_NONE
    # Allow all ciphers rather than only Python 3.10 default
    sslcontext.set_ciphers("DEFAULT")
    with contextlib.suppress(AttributeError):
        # This only works for OpenSSL >= 1.0.0
        sslcontext.options |= ssl.OP_NO_COMPRESSION
    sslcontext.set_default_verify_paths()
    return sslcontext


_NO_VERIFY_SSL_CONTEXT = create_no_verify_ssl_context()


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

    def __init__(self, host: str) -> None:
        """Initialize the Envoy class."""
        # We use our own httpx client session so we can disable SSL verification (Envoys use self-signed SSL certs)
        self._client = httpx.AsyncClient(
            verify=_NO_VERIFY_SSL_CONTEXT, timeout=TIMEOUT
        )  # nosec
        self.auth: EnvoyAuth | None = None
        self._host = host
        self._firmware = EnvoyFirmware(self._client, self._host)
        self._supported_features: SupportedFeatures = SupportedFeatures(0)
        self._production_endpoint: str | None = None

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
            if username is None:
                username = "installer"
                password = EnvoyUtils.get_password(full_serial, username)
            elif username == "envoy" and password is None:
                # The default password for the envoy user is the first 6 digits of the serial number
                password = full_serial[:6]

            if username and password:
                self.auth = EnvoyLegacyAuth(self.host, username, password)

        else:
            # Envoy firmware using new token authentication
            _LOGGER.debug("Authenticating to Envoy using token authentication")
            if token is not None:
                self.auth = EnvoyTokenAuth(self.host, token=token)
            elif (
                username is not None
                and password is not None
                and self._firmware.serial is not None
            ):
                self.auth = EnvoyTokenAuth(
                    self.host, username, password, self._firmware.serial
                )

        if not self.auth:
            _LOGGER.error(
                "You must include username/password or token to authenticate to the Envoy."
            )
            raise EnvoyAuthenticationRequired("Could not setup authentication object.")

        await self.auth.setup(self._client)

    @retry(
        retry=retry_if_exception_type((httpx.ReadError, httpx.RemoteProtocolError)),
        wait=wait_random_exponential(multiplier=2, max=3),
    )
    async def request(self, endpoint: str) -> Any:
        """Make a request to the Envoy."""
        if self.auth is None:
            raise EnvoyAuthenticationRequired(
                "You must authenticate to the Envoy before making requests."
            )

        response = await self._client.get(
            self.auth.get_endpoint_url(endpoint),
            headers={**DEFAULT_HEADERS, **self.auth.headers},
            cookies=self.auth.cookies,
            follow_redirects=True,
            auth=self.auth.auth,
        )
        return orjson.loads(response.text)

    @property
    def host(self) -> str:
        """Return the Envoy host."""
        return self._host

    @property
    def firmware(self) -> AwesomeVersion:
        """Return the Envoy firmware version."""
        return self._firmware.version

    @property
    def serial_number(self) -> str | None:
        """Return the Envoy serial number."""
        return self._firmware.serial

    async def probe(self) -> None:
        """Probe for model and supported features."""
        try:
            production_json: dict[str, Any] = await self.request(URL_PRODUCTION)
        except (json.JSONDecodeError, httpx.HTTPError) as e:
            _LOGGER.debug("Production endpoint not found at %s: %s", URL_PRODUCTION, e)
        else:
            production: list[dict[str, str | float | int]] | None = production_json.get(
                "production"
            )
            if production:
                for type_ in production:
                    if type_["type"] == "eim" and type_["activeCount"]:
                        self._supported_features |= SupportedFeatures.METERING
                        break
            consumption: list[
                dict[str, str | float | int]
            ] | None = production_json.get("consumption")
            if consumption:
                for meter in consumption:
                    meter_type = meter["measurementType"]
                    if meter_type == "total-consumption" and meter["activeCount"]:
                        self._supported_features |= SupportedFeatures.TOTAL_CONSUMPTION
                    elif meter_type == "net-consumption" and meter["activeCount"]:
                        self._supported_features |= SupportedFeatures.NET_CONSUMPTION
            self._production_endpoint = URL_PRODUCTION

        if not self._production_endpoint:
            for endpoint in (URL_PRODUCTION_V1, URL_PRODUCTION_JSON):
                try:
                    await self.request(endpoint)
                except (json.JSONDecodeError, httpx.HTTPError) as e:
                    _LOGGER.debug(
                        "Production endpoint not found at %s: %s", endpoint, e
                    )
                    continue
                self._production_endpoint = endpoint
                break

        try:
            await self.request(URL_PRODUCTION_INVERTERS)
        except (json.JSONDecodeError, httpx.HTTPError) as e:
            _LOGGER.debug("Inverters endpoint not found: %s", e)
        else:
            self._supported_features |= SupportedFeatures.INVERTERS

    async def update(self) -> EnvoyData:
        """Update data."""
        if not self._production_endpoint:
            await self.probe()

        if not self._production_endpoint:
            raise EnvoyProbeFailed("Unable to determine production endpoint")

        production_data = await self.request(self._production_endpoint)
        inverters: dict[str, EnvoyInverter] = {}
        raw = {
            "production": production_data,
        }

        if self._supported_features & SupportedFeatures.INVERTERS:
            inverters_data: list[dict[str, Any]] = await self.request(
                URL_PRODUCTION_INVERTERS
            )
            inverters = {
                inverter["serialNumber"]: EnvoyInverter(inverter)
                for inverter in inverters_data
            }
            raw["inverters"] = inverters_data

        return EnvoyData(
            system_production=EnvoySystemProduction(production_data),
            inverters=inverters,
            # Raw data is exposed so we can __eq__ the data to see if
            # anything has changed and consumers of the library can
            # avoid dispatching data if nothing has changed.
            raw=raw,
        )
