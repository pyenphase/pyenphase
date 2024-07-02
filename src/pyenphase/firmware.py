"""Envoy Firmware detection"""

import logging
import time

import httpx
from awesomeversion import AwesomeVersion
from lxml import etree  # nosec
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_random_exponential,
)

from .const import LOCAL_TIMEOUT, MAX_REQUEST_ATTEMPTS, MAX_REQUEST_DELAY
from .exceptions import EnvoyFirmwareCheckError, EnvoyFirmwareFatalCheckError

_LOGGER = logging.getLogger(__name__)


class EnvoyFirmware:
    """Class for querying and determining the Envoy firmware version."""

    __slots__ = (
        "_client",
        "_host",
        "_firmware_version",
        "_serial_number",
        "_part_number",
        "_url",
    )

    def __init__(
        self,
        _client: httpx.AsyncClient,
        host: str,
    ) -> None:
        """Initialize the Envoy firmware version."""
        self._client = _client
        self._host = host
        self._firmware_version: str | None = None
        self._serial_number: str | None = None
        self._part_number: str | None = None
        self._url: str = ""

    @retry(
        retry=retry_if_exception_type((httpx.NetworkError, httpx.RemoteProtocolError)),
        wait=wait_random_exponential(multiplier=2, max=5),
        stop=stop_after_delay(MAX_REQUEST_DELAY)
        | stop_after_attempt(MAX_REQUEST_ATTEMPTS),
        reraise=True,
    )
    async def _get_info(self) -> httpx.Response:
        """Obtain the firmware version for Envoy authentication."""
        self._url = f"https://{self._host}/info"
        _LOGGER.debug("Requesting %s with timeout %s", self._url, LOCAL_TIMEOUT)
        try:
            return await self._client.get(self._url, timeout=LOCAL_TIMEOUT)
        except (httpx.ConnectError, httpx.TimeoutException):
            # Firmware < 7.0.0 does not support HTTPS so we need to try HTTP
            # as a fallback, worse sometimes http will redirect to https://localhost
            # which is not helpful
            self._url = f"http://{self._host}/info"
            _LOGGER.debug("Retrying to %s with timeout %s", self._url, LOCAL_TIMEOUT)
            return await self._client.get(self._url, timeout=LOCAL_TIMEOUT)

    async def setup(self) -> None:
        """Obtain the firmware version for Envoy authentication."""
        # <envoy>/info will return XML with the firmware version
        debugon = _LOGGER.isEnabledFor(logging.DEBUG)
        if debugon:
            request_start = time.monotonic()
        try:
            result = await self._get_info()
        except httpx.TimeoutException:
            raise EnvoyFirmwareFatalCheckError(500, "Timeout connecting to Envoy")
        except httpx.ConnectError:
            raise EnvoyFirmwareFatalCheckError(500, "Unable to connect to Envoy")
        except httpx.HTTPError:
            raise EnvoyFirmwareCheckError(500, "Unable to query firmware version")

        if (status_code := result.status_code) == 200:
            if debugon:
                request_end = time.monotonic()
                content_type = result.headers.get("content-type")
                content = result.content
                _LOGGER.debug(
                    "Request reply in %s sec from %s status %s: %s %s",
                    round(request_end - request_start, 1),
                    self._url,
                    status_code,
                    content_type,
                    content,
                )
            xml = etree.fromstring(result.content)  # nosec
            if (device_tag := xml.find("device")) is not None:
                if (software_tag := device_tag.find("software")) is not None:
                    self._firmware_version = AwesomeVersion(
                        software_tag.text[1:]
                    )  # need to strip off the leading 'R' or 'D'
                if (sn_tag := device_tag.find("sn")) is not None:
                    self._serial_number = sn_tag.text
                if (pn_tag := device_tag.find("pn")) is not None:
                    self._part_number = pn_tag.text
                return

        else:
            # If we get a different status code, raise an exception
            raise EnvoyFirmwareCheckError(result.status_code, result.text)

    @property
    def version(self) -> AwesomeVersion:
        return self._firmware_version

    @property
    def serial(self) -> str | None:
        return self._serial_number

    @property
    def part_number(self) -> str | None:
        return self._part_number
