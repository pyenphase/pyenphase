"""Enphase Envoy class"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import replace
from functools import cached_property, partial
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import aiohttp
import orjson
from awesomeversion import AwesomeVersion
from envoy_utils.envoy_utils import EnvoyUtils
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_random_exponential,
)

from pyenphase.models.dry_contacts import DryContactStatus
from pyenphase.models.home import EnvoyInterfaceInformation

from .auth import EnvoyAuth, EnvoyLegacyAuth, EnvoyTokenAuth
from .const import (
    AUTH_TOKEN_MIN_VERSION,
    ENDPOINT_URL_HOME,
    LOCAL_TIMEOUT,
    MAX_REQUEST_ATTEMPTS,
    MAX_REQUEST_DELAY,
    URL_DRY_CONTACT_SETTINGS,
    URL_DRY_CONTACT_STATUS,
    URL_GRID_RELAY,
    URL_TARIFF,
    SupportedFeatures,
)
from .exceptions import (
    EnvoyAuthenticationRequired,
    EnvoyCommunicationError,
    EnvoyError,
    EnvoyFeatureNotAvailable,
    EnvoyHTTPStatusError,
    EnvoyPoorDataQuality,
    EnvoyProbeFailed,
)
from .firmware import EnvoyFirmware
from .json import json_loads
from .models.common import CommonProperties
from .models.envoy import EnvoyData
from .models.meters import CtType, EnvoyPhaseMode
from .models.tariff import EnvoyStorageMode
from .ssl import NO_VERIFY_SSL_CONTEXT
from .updaters.api_v1_production import EnvoyApiV1ProductionUpdater
from .updaters.api_v1_production_inverters import EnvoyApiV1ProductionInvertersUpdater
from .updaters.base import EnvoyUpdater
from .updaters.ensemble import EnvoyEnembleUpdater
from .updaters.generator import EnvoyGeneratorUpdater
from .updaters.meters import EnvoyMetersUpdater
from .updaters.production import (
    EnvoyProductionJsonFallbackUpdater,
    EnvoyProductionJsonUpdater,
    EnvoyProductionUpdater,
)
from .updaters.tariff import EnvoyTariffUpdater

_LOGGER = logging.getLogger(__name__)


DEFAULT_HEADERS = {
    "Accept": "application/json",
}

UPDATERS: list[type["EnvoyUpdater"]] = [
    EnvoyMetersUpdater,
    EnvoyProductionJsonUpdater,
    EnvoyProductionUpdater,
    EnvoyApiV1ProductionUpdater,
    EnvoyProductionJsonFallbackUpdater,
    EnvoyApiV1ProductionInvertersUpdater,
    EnvoyEnembleUpdater,
    EnvoyTariffUpdater,
    EnvoyGeneratorUpdater,
]  #: Ordered list of standard updaters for Envoy data collection


def register_updater(updater: type[EnvoyUpdater]) -> Callable[[], None]:
    """
    Register an updater in the updaters list.

    Registers a callable updater at the end of the updaters list. Probe
    method of the registered updater will be called during Envoy.probe().

    Use the returned callable to remove the registered updater again.

    After registering or removing an updater, use Envoy.probe() to make
    the change effective.

    :param updater: callable of (sub-) class EnvoyUpdater
    :return: callable to remove the updater from the registration list
    """
    UPDATERS.append(updater)

    def _remove_updater() -> None:
        """Callable to remove a prior registered updater."""
        UPDATERS.remove(updater)

    return _remove_updater


def get_updaters() -> list[type[EnvoyUpdater]]:
    """
    Return list of registered updaters.

    Returns current list of registered updaters. Changes
    to the list will not be in effect until
    Envoy.probe() is used.

    :return: list of callable updaters
    """
    return UPDATERS


class Envoy:
    """Class for communicating with an envoy."""

    def __init__(
        self,
        host: str,
        client: aiohttp.ClientSession | None = None,
        timeout: float | aiohttp.ClientTimeout | None = None,
    ) -> None:
        """
        Initializes an Envoy communication instance for interacting with an Enphase Envoy device.
        
        Sets up asynchronous HTTP communication, disables SSL verification for self-signed certificates, and prepares internal state for authentication, firmware handling, feature detection, and data collection. Supports both legacy and modern Envoy firmware versions.
        
        Args:
            host: DNS name or IP address of the Envoy device.
            client: Optional aiohttp ClientSession with SSL verification disabled. If not provided, a new session is created.
            timeout: Optional aiohttp ClientTimeout or float for request timeouts. Defaults to 10 seconds connect and 45 seconds read timeout.
        """
        # We use our own aiohttp client session so we can disable SSL verification (Envoys use self-signed SSL certs)
        self._timeout = timeout or LOCAL_TIMEOUT
        connector = aiohttp.TCPConnector(ssl=NO_VERIFY_SSL_CONTEXT)
        self._client = client or aiohttp.ClientSession(connector=connector)  # nosec
        self.auth: EnvoyAuth | None = None
        self._host = host
        self._firmware = EnvoyFirmware(self._client, self._host)
        self._supported_features: SupportedFeatures | None = None
        self._updaters: list[EnvoyUpdater] = []
        self._endpoint_cache: dict[str, aiohttp.ClientResponse] = {}
        self.data: EnvoyData | None = None
        self._common_properties: CommonProperties = CommonProperties()
        self._interface_settings: EnvoyInterfaceInformation | None = None

    async def setup(self) -> None:
        """
        Initiate Envoy communication by obtaining firmware version.

        Read /info on Envoy, accessible without authentication.
        Instantiates EnvoyFirmware class object. Required to
        decide what authentication to use for sub-sequent Envoy
        communication. Use this method as first step after class instantiation

        Will retry up to 4 times or 50 sec elapsed at next try, which
        ever comes first.

        :raises EnvoyFirmwareFatalCheckError: if connection or timeout
            failure occurs
        :raises EnvoyFirmwareCheckError: on http errors or any HTTP
            status other then 200
        """
        await self._firmware.setup()
        # force refetch of interface data next time requested
        self._interface_settings = None

    async def authenticate(
        self,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
    ) -> None:
        """
        Authenticate to the Envoy based on firmware version.

        If firmware version retrieved in Envoy.setup is < 7 then create DigestAuth using
        passed username and password. Use 'envoy' or 'installer' username and blank password.

        If Firmware is >= 7 create JWT Token based authorization. If token is passed, use
        it for authorization. If no token is passed, username and password should be
        Enlighten Cloud credentials to obtain a token. Validate the token with the local Envoy.

        :param username: Enligthen Cloud username or local Envoy username, defaults to None
        :param password: Enligthen Cloud password or local Envoy password, defaults to None
        :param token: Token to use with authentication, defaults to None
        :raises EnvoyAuthenticationRequired: Authentication failed with the local Envoy,
            provided token is expired or no token could be obtained from Enlighten cloud
            due to error or missing parameters.
        """
        if self._firmware.version < AUTH_TOKEN_MIN_VERSION:
            # Envoy firmware using old envoy/installer authentication
            _LOGGER.debug(
                "FW: %s, Authenticating to Envoy using envoy/installer authentication",
                self._firmware.version,
            )
            full_serial = self._firmware.serial
            if not username or username == "installer":
                username = "installer"
                password = EnvoyUtils.get_password(full_serial, username)
            elif username == "envoy" and not password:
                # The default password for the envoy user is the last 6 digits of the serial number
                assert full_serial is not None, "Serial must be set"  # nosec
                password = full_serial[-6:]

            if username and password:
                self.auth = EnvoyLegacyAuth(self.host, username, password)

        else:
            # Envoy firmware using new token authentication
            _LOGGER.debug(
                "FW: %s, Authenticating to Envoy using token authentication",
                self._firmware.version,
            )
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
            (
                aiohttp.ClientError,
                asyncio.TimeoutError,
            )
        ),
        wait=wait_random_exponential(multiplier=2, max=5),
        stop=stop_after_delay(MAX_REQUEST_DELAY)
        | stop_after_attempt(MAX_REQUEST_ATTEMPTS),
        reraise=True,
    )
    async def probe_request(self, endpoint: str) -> aiohttp.ClientResponse:
        """
        Sends a single GET request to the specified Envoy endpoint for feature probing.
        
        Intended for initial feature discovery by updaters; does not retry on network errors or timeouts. Raises EnvoyAuthenticationRequired if authentication is missing or if the response status is 401 or 404.
        
        Args:
            endpoint: The Envoy API endpoint to probe, starting with a leading slash.
        
        Returns:
            The aiohttp.ClientResponse object from the Envoy.
        """
        return await self._request(endpoint)

    @retry(
        retry=retry_if_exception_type(
            (
                aiohttp.ClientError,
                asyncio.TimeoutError,
            )
        ),
        wait=wait_random_exponential(multiplier=2, max=5),
        stop=stop_after_delay(MAX_REQUEST_DELAY)
        | stop_after_attempt(MAX_REQUEST_ATTEMPTS),
        reraise=True,
    )
    async def request(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        method: str | None = None,
    ) -> aiohttp.ClientResponse:
        """
        Sends a GET or POST request to the Envoy device and returns the HTTP response.
        
        Retries on network errors, timeouts, protocol errors, or invalid JSON responses, up to 4 attempts or 50 seconds total. Raises an authentication error if authentication is missing or the device returns HTTP 401 or 404.
        
        Args:
            endpoint: The Envoy endpoint path, starting with a leading slash.
            data: Optional dictionary to send as the request body. If provided, a POST request is made unless a different method is specified.
            method: Optional HTTP method to use. Defaults to GET if no data is provided, or POST if data is present.
        
        Returns:
            The aiohttp.ClientResponse object from the Envoy device.
        
        Raises:
            EnvoyAuthenticationRequired: If authentication is missing or the device returns HTTP 401 or 404.
            Exception: If all retry attempts fail due to communication errors.
        """
        return await self._request(endpoint, data, method)

    async def _request(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        method: str | None = None,
    ) -> aiohttp.ClientResponse:
        """
        Performs an authenticated HTTP request to the Envoy device and returns the response.
        
        If data is provided, sends a POST (or specified method) request with the data as a JSON payload; otherwise, sends a GET request. Raises an exception if authentication is missing or fails.
        
        Args:
            endpoint: The Envoy API endpoint to access, starting with a leading slash.
            data: Optional dictionary to send as a JSON payload.
            method: Optional HTTP method to use when sending data; defaults to POST.
        
        Raises:
            EnvoyAuthenticationRequired: If authentication has not been performed or if the Envoy returns a 401 or 403 status.
        
        Returns:
            The aiohttp.ClientResponse object from the Envoy.
        """
        if self.auth is None:
            raise EnvoyAuthenticationRequired(
                "You must authenticate to the Envoy before making requests."
            )

        url = self.auth.get_endpoint_url(endpoint)
        debugon = _LOGGER.isEnabledFor(logging.DEBUG)
        if debugon:
            request_start = time.monotonic()

        # Set up middleware if we have digest auth
        middlewares = (self.auth.auth,) if self.auth.auth else None

        if data:
            if debugon:
                _LOGGER.debug(
                    "Sending POST to %s with data %s", url, orjson.dumps(data)
                )
            response = await self._client.request(
                method if method else "POST",
                url,
                headers={**DEFAULT_HEADERS, **self.auth.headers},
                timeout=self._timeout,
                data=orjson.dumps(data),
                middlewares=middlewares,
            )
        else:
            _LOGGER.debug("Requesting %s with timeout %s", url, self._timeout)
            response = await self._client.get(
                url,
                headers={**DEFAULT_HEADERS, **self.auth.headers},
                timeout=self._timeout,
                middlewares=middlewares,
            )

        status_code = response.status
        if status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
            raise EnvoyAuthenticationRequired(
                f"Authentication failed for {url} with status {status_code}, "
                "please check your username/password or token."
            )

        # Read the content to cache it
        content = await response.read()
        # show all responses centrally when in debug
        if debugon:
            request_end = time.monotonic()
            content_type = response.headers.get("content-type")
            _LOGGER.debug(
                "Request reply in %s sec from %s status %s: %s %s",
                round(request_end - request_start, 1),
                url,
                status_code,
                content_type,
                content,  # Use the actual content bytes
            )

        return response

    async def interface_settings(self) -> EnvoyInterfaceInformation | None:
        """
        Returns Envoy active interface information.

        Returned data includes interface mac, interface type, software
        build date, configured timezone and DHCP settings

        This data is sourced from the /home endpoint which is a slower
        responding endpoint with some potential overhead on the Envoy.
        For this reason, as well as the fact that the data is static,
        it will only be fetched one time when called first time and
        cached internally. Subsequent calls will be fulfilled from the cache.
        A call to envoy.setup() will invalidate the cached data and
        result in a one-time read from Envoy upon next call.

        :return: Interface details or None if error

        """
        if not self._interface_settings:
            try:
                home_json = await self._json_request(
                    end_point=ENDPOINT_URL_HOME, data=None
                )
                self._interface_settings = EnvoyInterfaceInformation.from_api(home_json)
            except EnvoyError as exc:
                _LOGGER.debug("Failure getting interface information %s", exc)
        return self._interface_settings

    @property
    def host(self) -> str:
        """Return the Envoy host specified at initialization."""
        return self._host

    @property
    def firmware(self) -> AwesomeVersion:
        """Return the Envoy firmware version as read from the Envoy."""
        return self._firmware.version

    @property
    def part_number(self) -> str | None:
        """Return the Envoy part number as read from the Envoy."""
        return self._firmware.part_number

    @property
    def serial_number(self) -> str | None:
        """Return the Envoy serial number as read from the Envoy."""
        return self._firmware.serial

    @property
    def is_metered(self) -> bool:
        """Return the Envoy imetered info as read from the Envoy."""
        return self._firmware.is_metered

    @property
    def supported_features(self) -> SupportedFeatures:
        """Return the mask of Envoy supported features as established during Probe."""
        assert self._supported_features is not None, "Call setup() first"  # nosec
        return self._supported_features

    @property
    def phase_count(self) -> int:
        """Return the number of configured phases for CT meters as read from the Envoy."""
        assert self._common_properties is not None, "Call setup() first"  # nosec
        return self._common_properties.phase_count

    @property
    def active_phase_count(self) -> int:
        """Return the number of actual reported phases in Envoy production/consumption report."""
        assert self._common_properties is not None, "Call setup() first"  # nosec
        return self._common_properties.active_phase_count

    @property
    def ct_meter_count(self) -> int:
        """Return the number of configured current transformers (CT) as read from the Envoy"""
        assert self._common_properties is not None, "Call setup() first"  # nosec
        return self._common_properties.ct_meter_count

    @property
    def consumption_meter_type(self) -> CtType | None:
        """
        Return the type of consumption ct meter installed (total
        or net-consumption or None) as read from the Envoy.
        """
        assert self._common_properties is not None, "Call setup() first"  # nosec
        return self._common_properties.consumption_meter_type

    @property
    def production_meter_type(self) -> CtType | None:
        """
        Return the type of production ct meter installed
        (Production or None) as read from the Envoy.
        """
        assert self._common_properties is not None, "Call setup() first"  # nosec
        return self._common_properties.production_meter_type

    @property
    def storage_meter_type(self) -> CtType | None:
        """Return the type of storage ct meter installed (Storage or None) as read from the Envoy."""
        assert self._common_properties is not None, "Call setup() first"  # nosec
        return self._common_properties.storage_meter_type

    @property
    def phase_mode(self) -> EnvoyPhaseMode | None:
        """Return the phase mode configured for the CT meters (single, split or three) as read from the Envoy."""
        assert self._common_properties is not None, "Call setup() first"  # nosec
        return self._common_properties.phase_mode

    @property
    def acb_count(self) -> int:
        """Return the number of reported ACB batteries in Production storage report section."""
        assert self._common_properties is not None, "Call setup() first"  # nosec
        return self._common_properties.acb_batteries_reported

    @cached_property
    def envoy_model(self) -> str:
        """
        Returns a string describing the Envoy model and its detected features.
        
        The description includes the number of phases, phase mode, and the presence and types of consumption, production, and storage CT meters, if available.
        """
        model = "Envoy"

        # if CT and more then 1 phase add phase count to model
        ct_count = self.ct_meter_count
        phase_count = self.phase_count
        if phase_count > 1 or ct_count > 0:
            model = f"{model}, phases: {phase_count}"

            # Add phase mode to model
            phase_mode = self.phase_mode
            model = f"{model}, phase mode: {phase_mode}"

        # if consumption CT type is known add to model
        if ct_consumption_meter := self.consumption_meter_type:
            model = f"{model}, {ct_consumption_meter} CT"

        # if production CT is found add to model.
        if ct_production_meter := self.production_meter_type:
            model = f"{model}, {ct_production_meter} CT"

        # if storage CT is found add to model.
        if ct_storage_meter := self.storage_meter_type:
            model = f"{model}, {ct_storage_meter} CT"

        return model

    async def _make_cached_request(
        self,
        request_func: Callable[[str], Awaitable[aiohttp.ClientResponse]],
        endpoint: str,
    ) -> aiohttp.ClientResponse:
        """
        Returns a cached response for the specified endpoint if available; otherwise, performs the request using the provided function, caches the response if successful, and returns it.
        
        Args:
            request_func: An asynchronous function that performs the request for the given endpoint.
            endpoint: The endpoint string to request and cache.
        
        Returns:
            The aiohttp.ClientResponse object for the requested endpoint, either from cache or from a new request.
        """
        if cached_response := self._endpoint_cache.get(endpoint):
            return cached_response
        response = await request_func(endpoint)
        if response.status == 200:
            self._endpoint_cache[endpoint] = response
        return response

    async def probe(self) -> None:
        """
        Probe for Envoy model and supported features.

        For each updater in the list of updaters returned by get_updaters,
        execute the probe() method. Build and store a list of updaters to use,
        containing updaters for which the probe() method does return at least 1
        supported feature. Store the map of all returned supported features.

        An updaters probe method should determine if the data for the specific
        updater scope is available or not. If so, the updaters update() method will
        be used during data collection.

        Probe should be used only once, after setup and authorization at the start of
        the communication. The update() method will call probe if not done prior.

        :raises EnvoyProbeFailed: if no solar production data can be found on the Envoy.
            Solar production data is available in all Envoy models.
        """
        supported_features = SupportedFeatures(0)
        updaters: list[EnvoyUpdater] = []
        version = self._firmware.version
        metered = self.is_metered
        self._endpoint_cache.clear()
        cached_probe = partial(self._make_cached_request, self.probe_request)
        cached_request = partial(self._make_cached_request, self.request)
        self._common_properties.reset_probe_properties(is_metered=metered)

        for updater in get_updaters():
            klass = updater(
                version, cached_probe, cached_request, self._common_properties
            )
            if updater_features := await klass.probe(supported_features):
                supported_features |= updater_features
                updaters.append(klass)

        if not supported_features & SupportedFeatures.PRODUCTION:
            raise EnvoyProbeFailed("Unable to determine production endpoint")

        self._updaters = updaters
        self._supported_features = supported_features

    def _validate_update(self, data: EnvoyData) -> None:
        """
        Perform some overall validation checks and raise for issues.

        Envoy data returned can be impacted by the state of the Envoy. This
        validates searches for known cases and rules the data as invalid.
        INtention is to avoid false data reported and have it rather signalled
        as poor quality.

        - Envoy firmware v3 starts communicating before all data is established
            and sends zero values for solar production during first minutes
            after startup. Signal poor data quality as long as all values are 0.

        :param data: Envoy data
        :raises EnvoyPoorDataQuality: data was deemed invalid based on specific quality tests
        """
        if self._firmware.version.major == "3" and data.system_production:
            # FW R3.x will return status 200 with all zeros right after startup
            # where never versions return status 503 to signal not ready yet
            # raise error to avoid inserting zero's in historical series.
            production = data.system_production
            if (
                production.watts_now
                + production.watt_hours_today
                + production.watt_hours_last_7_days
                + production.watt_hours_lifetime
            ) == 0:
                raise EnvoyPoorDataQuality(
                    "Data rejected on rule: "
                    f"FW 3.x production all zero at startup ({self._firmware.version})."
                )

    async def update(self) -> EnvoyData:
        """
        Collects and returns current data from the Envoy device using all active updaters.
        
        If probing for supported features has not been performed, it is executed first. Each updater gathers data for its scope and updates the Envoy data set. Endpoint responses are cached during the update cycle to avoid duplicate requests.
        
        Raises:
            EnvoyCommunicationError: If a network or communication error occurs.
            EnvoyHTTPStatusError: If the HTTP response status is not 2xx.
        
        Returns:
            EnvoyData: The collected data from the Envoy device.
        """
        # Some of the updaters user the same endpoint
        # so we cache the 200 responses for each update
        # cycle to not make duplicate requests
        self._endpoint_cache.clear()
        if not self._supported_features:
            await self.probe()

        data = EnvoyData()
        for updater in self._updaters:
            try:
                await updater.update(data)
            except aiohttp.ClientError as err:
                raise EnvoyCommunicationError(f"aiohttp ClientError {err!s}") from err
            except asyncio.TimeoutError as err:
                raise EnvoyCommunicationError(f"Timeout {err!s}") from err

        self._validate_update(data)
        self.data = data
        return data

    async def _json_request(
        self, end_point: str, data: dict[str, Any] | None, method: str | None = None
    ) -> Any:
        """
        Sends a request to the Envoy device and returns the parsed JSON response.
        
        Args:
            end_point: The Envoy endpoint to access, starting with a leading slash.
            data: Optional dictionary to send as the request body.
            method: HTTP method to use; defaults to POST if data is provided.
        
        Raises:
            EnvoyCommunicationError: If a network or communication error occurs.
            EnvoyHTTPStatusError: If the HTTP response status is not 2xx.
        
        Returns:
            The response content parsed as JSON.
        """
        try:
            response = await self._request(end_point, data, method)
        except aiohttp.ClientError as err:
            raise EnvoyCommunicationError(f"aiohttp ClientError {err!s}") from err
        except asyncio.TimeoutError as err:
            raise EnvoyCommunicationError(f"Timeout {err!s}") from err
        if not (200 <= response.status < 300):
            raise EnvoyHTTPStatusError(response.status, str(response.url))

        return json_loads(end_point, await response.read())

    async def go_on_grid(self) -> dict[str, Any]:
        """
        Sends a command to the Envoy to connect to the electrical grid.
        
        Raises:
            EnvoyFeatureNotAvailable: If the ENPOWER feature is not supported by the Envoy.
            EnvoyCommunicationError: If a network or communication error occurs.
            EnvoyHTTPStatusError: If the HTTP response status is not successful.
        
        Returns:
            The JSON response from the Envoy after attempting to close the grid relay.
        """
        if not self.supported_features & SupportedFeatures.ENPOWER:
            raise EnvoyFeatureNotAvailable(
                "This feature is not available on this Envoy."
            )
        return await self._json_request(URL_GRID_RELAY, {"mains_admin_state": "closed"})

    async def go_off_grid(self) -> dict[str, Any]:
        """
        Requests the Envoy device to disconnect from the electrical grid.
        
        Sends a POST request to the grid relay endpoint to open the mains relay, requiring the ENPOWER feature.
        
        Raises:
            EnvoyFeatureNotAvailable: If the ENPOWER feature is not supported by the Envoy.
            EnvoyCommunicationError: If a network or communication error occurs.
            EnvoyHTTPStatusError: If the HTTP response status is not successful.
        
        Returns:
            The JSON response from the Envoy device.
        """
        if not self.supported_features & SupportedFeatures.ENPOWER:
            raise EnvoyFeatureNotAvailable(
                "This feature is not available on this Envoy."
            )
        return await self._json_request(URL_GRID_RELAY, {"mains_admin_state": "open"})

    async def update_dry_contact(self, new_data: dict[str, Any]) -> dict[str, Any]:
        """
        Updates the settings for a specified Enpower dry contact relay.
        
        Merges the provided settings with the current relay configuration and sends the complete configuration to the Envoy device. The `new_data` dictionary must include the relay's "id" key to identify which relay to update. Only the specified settings are changed; all other settings remain as previously configured.
        
        Args:
            new_data: Dictionary containing the settings to update for the dry contact relay. Must include the "id" key.
        
        Raises:
            EnvoyFeatureNotAvailable: If the ENPOWER feature is not supported by the Envoy.
            EnvoyCommunicationError: If a network or communication error occurs.
            EnvoyHTTPStatusError: If the HTTP response status is not successful.
            ValueError: If called before any data has been retrieved from the Envoy, or if "id" is missing from `new_data`.
        
        Returns:
            The updated dry contact settings as returned by the Envoy.
        """
        # All settings for the relay must be sent in the POST or it may crash the Envoy

        if not self.supported_features & SupportedFeatures.ENPOWER:
            raise EnvoyFeatureNotAvailable(
                "This feature is not available on this Envoy."
            )

        if not (id_ := new_data.get("id")):
            raise ValueError("You must specify the dry contact ID in the data object.")
        # Get the current settings for the relay from EnvoyData and merge with the new settings
        if not (current_data := self.data):
            raise ValueError(
                "Tried to set dry contact settings before the Envoy was queried."
            )
        current_model = current_data.dry_contact_settings[id_]
        new_model = replace(current_model, **new_data)

        return await self._json_request(
            URL_DRY_CONTACT_SETTINGS, {"dry_contacts": new_model.to_api()}
        )

    async def open_dry_contact(self, id: str) -> dict[str, Any]:
        """
        Opens the specified dry contact relay on the Envoy device.
        
        Sends a request to open the dry contact relay with the given ID and updates the internal status to reflect the change before the device reports it.
        
        Args:
            id: The identifier of the dry contact relay to open.
        
        Raises:
            EnvoyFeatureNotAvailable: If the Envoy does not support the ENPOWER feature.
            EnvoyCommunicationError: If a network or communication error occurs.
            EnvoyHTTPStatusError: If the HTTP response status is not successful.
        
        Returns:
            The JSON response from the Envoy device.
        """
        if not self.supported_features & SupportedFeatures.ENPOWER:
            raise EnvoyFeatureNotAvailable(
                "This feature is not available on this Envoy."
            )

        result = await self._json_request(
            URL_DRY_CONTACT_STATUS, {"dry_contacts": {"id": id, "status": "open"}}
        )
        # The Envoy takes a few seconds before it will reflect the new state of the relay
        # so we preemptively update it
        if TYPE_CHECKING:
            assert self.data is not None  # nosec
        self.data.dry_contact_status[id].status = DryContactStatus.OPEN
        return result

    async def close_dry_contact(self, id: str) -> dict[str, Any]:
        """
        Closes the specified dry contact relay on the Envoy device.
        
        Sends a POST request to set the dry contact relay with the given ID to "closed" status. Updates the internal dry contact status immediately after the request.
        
        Args:
            id: The relay ID of the dry contact to close.
        
        Raises:
            EnvoyFeatureNotAvailable: If the ENPOWER feature is not supported by the Envoy.
            EnvoyCommunicationError: If a network or communication error occurs.
            EnvoyHTTPStatusError: If the HTTP response status is not successful.
        
        Returns:
            The JSON response from the Envoy device.
        """
        if not self.supported_features & SupportedFeatures.ENPOWER:
            raise EnvoyFeatureNotAvailable(
                "This feature is not available on this Envoy."
            )

        result = await self._json_request(
            URL_DRY_CONTACT_STATUS, {"dry_contacts": {"id": id, "status": "closed"}}
        )
        # The Envoy takes a few seconds before it will reflect the new state of the relay
        # so we preemptively update it
        if TYPE_CHECKING:
            assert self.data is not None  # nosec
        self.data.dry_contact_status[id].status = DryContactStatus.CLOSED
        return result

    async def enable_charge_from_grid(self) -> dict[str, Any]:
        """
        Enables charging from the grid for Encharge batteries by updating the tariff settings.
        
        Raises:
            EnvoyFeatureNotAvailable: If Encharge/IQ batteries or tariff data are not available.
            EnvoyCommunicationError: If a network or communication error occurs.
            EnvoyHTTPStatusError: If the HTTP response status is not 2xx.
            ValueError: If called before any data has been retrieved from the Envoy.
        
        Returns:
            The JSON response from the Envoy after updating the tariff settings.
        """
        self._verify_tariff_storage_or_raise()
        if TYPE_CHECKING:
            assert self.data is not None  # nosec
            assert self.data.tariff is not None  # nosec
            assert self.data.tariff.storage_settings is not None  # nosec
        self.data.tariff.storage_settings.charge_from_grid = True
        return await self._json_request(
            URL_TARIFF, {"tariff": self.data.tariff.to_api()}, method="PUT"
        )

    async def disable_charge_from_grid(self) -> dict[str, Any]:
        """
        Disables charging from the grid for Encharge batteries by updating the tariff storage settings.
        
        Raises:
            EnvoyFeatureNotAvailable: If Encharge/IQ batteries or tariff data are not available.
            EnvoyCommunicationError: If a network or communication error occurs.
            EnvoyHTTPStatusError: If the HTTP response status is not 2xx.
            ValueError: If called before any data has been retrieved from the Envoy.
        
        Returns:
            The JSON response from the Envoy after updating the tariff settings.
        """
        self._verify_tariff_storage_or_raise()
        if TYPE_CHECKING:
            assert self.data is not None  # nosec
            assert self.data.tariff is not None  # nosec
            assert self.data.tariff.storage_settings is not None  # nosec
        self.data.tariff.storage_settings.charge_from_grid = False
        return await self._json_request(
            URL_TARIFF, {"tariff": self.data.tariff.to_api()}, method="PUT"
        )

    async def set_storage_mode(self, mode: EnvoyStorageMode) -> dict[str, Any]:
        """
        Sets the storage mode for Encharge batteries on the Envoy device.
        
        Updates the internal tariff data with the specified storage mode and sends the new configuration to the Envoy. Requires Encharge or IQ batteries and tariff data to be available.
        
        Args:
            mode: The desired storage mode as an EnvoyStorageMode.
        
        Returns:
            The JSON response from the Envoy after updating the storage mode.
        
        Raises:
            EnvoyFeatureNotAvailable: If Encharge/IQ batteries or tariff data are not available.
            EnvoyCommunicationError: If a network or communication error occurs.
            EnvoyHTTPStatusError: If the HTTP response status is not 2xx.
            ValueError: If called before any data has been requested from the Envoy.
            TypeError: If the mode is not of type EnvoyStorageMode.
        """
        self._verify_tariff_storage_or_raise()
        if TYPE_CHECKING:
            assert self.data is not None  # nosec
            assert self.data.tariff is not None  # nosec
            assert self.data.tariff.storage_settings is not None  # nosec
        if type(mode) is not EnvoyStorageMode:
            raise TypeError("Mode must be of type EnvoyStorageMode")
        self.data.tariff.storage_settings.mode = mode
        return await self._json_request(
            URL_TARIFF, {"tariff": self.data.tariff.to_api()}, method="PUT"
        )

    async def set_reserve_soc(self, value: int) -> dict[str, Any]:
        """
        Sets the reserve state of charge (SOC) for Encharge batteries.
        
        Updates the reserved SOC value in the internal tariff data and sends the updated configuration to the Envoy device.
        
        Args:
            value: The desired reserve SOC percentage to set.
        
        Raises:
            EnvoyFeatureNotAvailable: If Encharge/IQ batteries or tariff data are not available.
            EnvoyCommunicationError: If a network or communication error occurs.
            EnvoyHTTPStatusError: If the Envoy returns a non-2xx HTTP status.
            ValueError: If called before tariff data has been retrieved.
        
        Returns:
            The JSON response from the Envoy after updating the reserve SOC.
        """
        self._verify_tariff_storage_or_raise()
        if TYPE_CHECKING:
            assert self.data is not None  # nosec
            assert self.data.tariff is not None  # nosec
            assert self.data.tariff.storage_settings is not None  # nosec
        self.data.tariff.storage_settings.reserved_soc = round(float(value), 1)
        return await self._json_request(
            URL_TARIFF, {"tariff": self.data.tariff.to_api()}, method="PUT"
        )

    def _verify_tariff_storage_or_raise(self) -> None:
        """
        Verify Encharge or IQ batteries and tariff data are available in Envoy

        :raises EnvoyFeatureNotAvailable: If no Encharge or IQ batteries are available
        :raises EnvoyFeatureNotAvailable: If no TARIFF data is available in Envoy
        :raises ValueError: If update was attempted before first data was requested from Envoy
        """
        if not self.supported_features & SupportedFeatures.ENCHARGE:
            raise EnvoyFeatureNotAvailable(
                "This feature requires Enphase Encharge or IQ Batteries."
            )
        if not self.supported_features & SupportedFeatures.TARIFF:
            raise EnvoyFeatureNotAvailable(
                "This feature is not available on this Envoy."
            )
        if not self.data:
            raise ValueError("Tried access envoy data before Envoy was queried.")
        if TYPE_CHECKING:
            assert self.data is not None  # nosec
        if not self.data.tariff:
            raise ValueError(
                "Tried to configure charge from grid before the Envoy was queried."
            )
        if TYPE_CHECKING:
            assert self.data.tariff is not None  # nosec
        if not self.data.tariff.storage_settings:
            raise EnvoyFeatureNotAvailable(
                "This feature requires Enphase Encharge or IQ Batteries."
            )
