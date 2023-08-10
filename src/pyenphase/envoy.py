import logging
from collections.abc import Callable
from typing import Any

import httpx
import orjson
from awesomeversion import AwesomeVersion
from envoy_utils.envoy_utils import EnvoyUtils
from tenacity import retry, retry_if_exception_type, wait_random_exponential

from .auth import EnvoyAuth, EnvoyLegacyAuth, EnvoyTokenAuth
from .const import (
    AUTH_TOKEN_MIN_VERSION,
    LOCAL_TIMEOUT,
    URL_GRID_RELAY,
    SupportedFeatures,
)
from .exceptions import (
    EnvoyAuthenticationRequired,
    EnvoyFeatureNotAvailable,
    EnvoyProbeFailed,
)
from .firmware import EnvoyFirmware
from .json import json_loads
from .models.envoy import EnvoyData
from .ssl import NO_VERIFY_SSL_CONTEXT
from .updaters.api_v1_production import EnvoyApiV1ProductionUpdater
from .updaters.api_v1_production_inverters import EnvoyApiV1ProductionInvertersUpdater
from .updaters.base import EnvoyUpdater
from .updaters.ensemble import EnvoyEnembleUpdater
from .updaters.production import EnvoyProductionJsonUpdater, EnvoyProductionUpdater

_LOGGER = logging.getLogger(__name__)


DEFAULT_HEADERS = {
    "Accept": "application/json",
}

UPDATERS: list[type["EnvoyUpdater"]] = [
    EnvoyProductionUpdater,
    EnvoyProductionJsonUpdater,
    EnvoyApiV1ProductionUpdater,
    EnvoyApiV1ProductionInvertersUpdater,
    EnvoyEnembleUpdater,
]


def register_updater(updater: type[EnvoyUpdater]) -> Callable[[], None]:
    """Register an updater."""
    UPDATERS.append(updater)

    def _remove_updater() -> None:
        UPDATERS.remove(updater)

    return _remove_updater


def get_updaters() -> list[type[EnvoyUpdater]]:
    return UPDATERS


class Envoy:
    """Class for communicating with an envoy."""

    def __init__(
        self,
        host: str,
        client: httpx.AsyncClient | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> None:
        """Initialize the Envoy class."""
        # We use our own httpx client session so we can disable SSL verification (Envoys use self-signed SSL certs)
        self._timeout = timeout or LOCAL_TIMEOUT
        self._client = client or httpx.AsyncClient(
            verify=NO_VERIFY_SSL_CONTEXT
        )  # nosec
        self.auth: EnvoyAuth | None = None
        self._host = host
        self._firmware = EnvoyFirmware(self._client, self._host)
        self._supported_features: SupportedFeatures | None = None
        self._updaters: list[EnvoyUpdater] = []
        self.data: EnvoyData | None = None

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
    async def probe_request(self, endpoint: str) -> httpx.Response:
        """Make a probe request.

        Probe requests are not retried on bad JSON responses.
        """
        return await self._request(endpoint)

    @retry(
        retry=retry_if_exception_type(
            (
                httpx.NetworkError,
                httpx.TimeoutException,
                httpx.RemoteProtocolError,
                orjson.JSONDecodeError,
            )
        ),
        wait=wait_random_exponential(multiplier=2, max=3),
    )
    async def request(
        self, endpoint: str, data: dict[str, Any] | None = None
    ) -> httpx.Response:
        """Make a request to the Envoy.

        Request retries on bad JSON responses which the Envoy sometimes returns.
        """
        return await self._request(endpoint, data)

    async def _request(
        self, endpoint: str, data: dict[str, Any] | None = None
    ) -> httpx.Response:
        """Make a request to the Envoy."""
        if self.auth is None:
            raise EnvoyAuthenticationRequired(
                "You must authenticate to the Envoy before making requests."
            )

        url = self.auth.get_endpoint_url(endpoint)

        if data:
            _LOGGER.debug("Sending POST to %s with data %s", url, data)
            return await self._client.post(
                url,
                headers={**DEFAULT_HEADERS, **self.auth.headers},
                cookies=self.auth.cookies,
                follow_redirects=True,
                auth=self.auth.auth,
                timeout=self._timeout,
                data=orjson.dumps(data),
            )

        _LOGGER.debug("Requesting %s with timeout %s", url, self._timeout)
        return await self._client.get(
            url,
            headers={**DEFAULT_HEADERS, **self.auth.headers},
            cookies=self.auth.cookies,
            follow_redirects=True,
            auth=self.auth.auth,
            timeout=self._timeout,
        )

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

    @property
    def supported_features(self) -> SupportedFeatures:
        """Return the supported features."""
        assert self._supported_features is not None, "Call setup() first"  # nosec
        return self._supported_features

    async def probe(self) -> None:
        """Probe for model and supported features."""
        supported_features = SupportedFeatures(0)
        updaters: list[EnvoyUpdater] = []
        version = self._firmware.version
        for updater in get_updaters():
            klass = updater(version, self.probe_request, self.request)
            if updater_features := await klass.probe(supported_features):
                supported_features |= updater_features
                updaters.append(klass)

        if not supported_features & SupportedFeatures.PRODUCTION:
            raise EnvoyProbeFailed("Unable to determine production endpoint")

        self._updaters = updaters
        self._supported_features = supported_features

    async def update(self) -> EnvoyData:
        """Update data."""
        if not self._supported_features:
            await self.probe()

        data = EnvoyData()
        for updater in self._updaters:
            await updater.update(data)

        self.data = data
        return data

    async def _json_request(self, end_point: str, data: dict[str, Any] | None) -> Any:
        """Make a request to the Envoy and return the JSON response."""
        response = await self._request(end_point, data)
        return json_loads(end_point, response.content)

    async def go_on_grid(self) -> dict[str, Any]:
        """Make a request to the Envoy to go on grid."""
        if not self.supported_features & SupportedFeatures.ENPOWER:
            raise EnvoyFeatureNotAvailable(
                "This feature is not available on this Envoy."
            )
        return await self._json_request(URL_GRID_RELAY, {"mains_admin_state": "closed"})

    async def go_off_grid(self) -> dict[str, Any]:
        """Make a request to the Envoy to go off grid."""
        if not self.supported_features & SupportedFeatures.ENPOWER:
            raise EnvoyFeatureNotAvailable(
                "This feature is not available on this Envoy."
            )
        return await self._json_request(URL_GRID_RELAY, {"mains_admin_state": "open"})
