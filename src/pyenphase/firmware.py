"""Envoy Firmware detection"""

import asyncio
import logging
import time

import aiohttp
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
        "_firmware_version",
        "_host",
        "_metered",
        "_part_number",
        "_serial_number",
        "_url",
    )

    def __init__(
        self,
        _client: aiohttp.ClientSession,
        host: str,
    ) -> None:
        """
        Initializes an EnvoyFirmware instance for querying firmware and device information.

        Args:
            _client: An aiohttp ClientSession for making HTTP requests.
            host: The DNS name or IP address of the Envoy device.

        """
        self._client = _client
        self._host = host
        self._firmware_version: str | None = None
        self._serial_number: str | None = None
        self._part_number: str | None = None
        self._url: str = ""
        self._metered: bool = False

    @retry(
        retry=retry_if_exception_type(aiohttp.ClientError),
        wait=wait_random_exponential(multiplier=2, max=5),
        stop=stop_after_delay(MAX_REQUEST_DELAY)
        | stop_after_attempt(MAX_REQUEST_ATTEMPTS),
        reraise=True,
    )
    async def _get_info(self) -> tuple[int, bytes]:
        """
        Fetches the Envoy device's /info endpoint over HTTPS, falling back to HTTP if needed.

        Attempts to retrieve device information by sending a GET request to the /info endpoint using HTTPS. If a connection error or timeout occurs, retries the request using HTTP. Retries are performed on network or protocol errors, up to 4 times or 50 seconds total. The HTTP status code is not validated.

        Returns:
            A tuple containing the HTTP status code and the response content as bytes.

        """
        self._url = f"https://{self._host}/info"
        _LOGGER.debug("Requesting %s with timeout %s", self._url, LOCAL_TIMEOUT)
        try:
            resp = await self._client.get(self._url, timeout=LOCAL_TIMEOUT)
            return resp.status, await resp.read()
        except (aiohttp.ClientConnectorError, asyncio.TimeoutError):
            # Firmware < 7.0.0 does not support HTTPS so we need to try HTTP
            # as a fallback, worse sometimes http will redirect to https://localhost
            # which is not helpful
            self._url = f"http://{self._host}/info"
            _LOGGER.debug("Retrying to %s with timeout %s", self._url, LOCAL_TIMEOUT)
            resp = await self._client.get(self._url, timeout=LOCAL_TIMEOUT)
            return resp.status, await resp.read()

    async def setup(self) -> None:
        """
        Fetches and stores the firmware version, serial number, part number, and metered flag from the Envoy device.

        Attempts to retrieve and parse the `/info` endpoint over HTTPS, falling back to HTTP if necessary. Extracts device information from the XML response and updates internal properties. Retries on network errors up to four times or 50 seconds total.

        Raises:
            EnvoyFirmwareFatalCheckError: If a connection or timeout failure occurs.
            EnvoyFirmwareCheckError: If an HTTP error occurs or the response status is not 200.

        """
        # <envoy>/info will return XML with the firmware version
        debugon = _LOGGER.isEnabledFor(logging.DEBUG)
        if debugon:
            request_start = time.monotonic()
        try:
            status_code, content = await self._get_info()
        except asyncio.TimeoutError as ex:
            raise EnvoyFirmwareFatalCheckError(
                500, "Timeout connecting to Envoy"
            ) from ex
        except aiohttp.ClientConnectorError as ex:
            raise EnvoyFirmwareFatalCheckError(
                500, "Unable to connect to Envoy"
            ) from ex
        except aiohttp.ClientError as ex:
            raise EnvoyFirmwareCheckError(
                500, "Unable to query firmware version"
            ) from ex

        if status_code == 200:
            if debugon:
                request_end = time.monotonic()
                _LOGGER.debug(
                    "Request reply in %s sec from %s status %s",
                    round(request_end - request_start, 1),
                    self._url,
                    status_code,
                )
            xml = etree.fromstring(content)  # nosec  # noqa: S320
            if (device_tag := xml.find("device")) is not None:
                if (software_tag := device_tag.find("software")) is not None:
                    self._firmware_version = AwesomeVersion(
                        software_tag.text[1:]
                    )  # need to strip off the leading 'R' or 'D'
                if (sn_tag := device_tag.find("sn")) is not None:
                    self._serial_number = sn_tag.text
                if (pn_tag := device_tag.find("pn")) is not None:
                    self._part_number = pn_tag.text
                if (imeter_tag := device_tag.find("imeter")) is not None:
                    self._metered = imeter_tag.text == "true"
                return

        else:
            # If we get a different status code, raise an exception
            raise EnvoyFirmwareCheckError(status_code, content.decode())

    @property
    def version(self) -> AwesomeVersion:
        """
        Returns the firmware version retrieved from the Envoy device.

        Returns:
            The firmware version as an AwesomeVersion object, or None if not yet set by calling setup().

        """
        return self._firmware_version

    @property
    def serial(self) -> str | None:
        """
        Return serial number as read from Envoy.

        :return: Envoy serial number or None if
            :class:`pyenphase.firmware.EnvoyFirmware.setup` was not used
        """
        return self._serial_number

    @property
    def part_number(self) -> str | None:
        """
        Return part number as read from Envoy.

        :return: Envoy part number or None if
            :class:`pyenphase.firmware.EnvoyFirmware.setup` was not used
        """
        return self._part_number

    @property
    def is_metered(self) -> bool:
        """
        Return imetered setting as read from Envoy.

        :return: Envoy info imetered setting. Only True if read and set in info

        """
        return self._metered
