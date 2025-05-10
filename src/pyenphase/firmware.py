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
        "_firmware_version",
        "_host",
        "_metered",
        "_part_number",
        "_serial_number",
        "_url",
    )

    def __init__(
        self,
        _client: httpx.AsyncClient,
        host: str,
    ) -> None:
        """
        Class for querying and determining the Envoy firmware version.

        :param client: httpx Asyncclient not verifying SSL
            certificates, see :class:`pyenphase.ssl`.
        :param host: Envoy DNS name or IP address
        """
        self._client = _client
        self._host = host
        self._firmware_version: str | None = None
        self._serial_number: str | None = None
        self._part_number: str | None = None
        self._url: str = ""
        self._metered: bool = False

    @retry(
        retry=retry_if_exception_type((httpx.NetworkError, httpx.RemoteProtocolError)),
        wait=wait_random_exponential(multiplier=2, max=5),
        stop=stop_after_delay(MAX_REQUEST_DELAY)
        | stop_after_attempt(MAX_REQUEST_ATTEMPTS),
        reraise=True,
    )
    async def _get_info(self) -> httpx.Response:
        """
        Perform GET request to /info endpoint on envoy.

        Try GET request to https://<host>/info to read info endpoint.
        If connection error or timeout, retry on http://<host>/info.

        Will retry up to 4 times or 50 sec elapsed at next try, which
        ever comes first on network or remote protocol errors.
        HTTP status is not verified.

        :return: GET response as received from Envoy
        """
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
        """
        Obtain the firmware version, serial-number and part-number from Envoy.

        Read /info on Envoy, accessible without authentication.
        Store firmware version, serial-number and part-number properties
        from xml response.

        Reads first on HTTPS, if that fails on HTTP for firmware < 7.
        Will retry up to 4 times or 50 sec elapsed at next try, which
        ever comes first.

        .. code-block:: python

            client = httpx.AsyncClient(verify=create_no_verify_ssl_context())
            firmware = EnvoyFirmware(client,host)
            await firmware.setup()
            print(firmware.version)

        :raises EnvoyFirmwareFatalCheckError: if connection or timeout
            failure occurs
        :raises EnvoyFirmwareCheckError: on http errors or any HTTP
            status other then 200
        """
        # <envoy>/info will return XML with the firmware version
        debugon = _LOGGER.isEnabledFor(logging.DEBUG)
        if debugon:
            request_start = time.monotonic()
        try:
            result = await self._get_info()
        except httpx.TimeoutException as ex:
            raise EnvoyFirmwareFatalCheckError(
                500, "Timeout connecting to Envoy"
            ) from ex
        except httpx.ConnectError as ex:
            raise EnvoyFirmwareFatalCheckError(
                500, "Unable to connect to Envoy"
            ) from ex
        except httpx.HTTPError as ex:
            raise EnvoyFirmwareCheckError(
                500, "Unable to query firmware version"
            ) from ex

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
            xml = etree.fromstring(result.content)  # nosec  # noqa: S320
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
            raise EnvoyFirmwareCheckError(result.status_code, result.text)

    @property
    def version(self) -> AwesomeVersion:
        """
        Return firmware version as read from Envoy.

        :return: Envoy firmware version or None if
            :class:`pyenphase.firmware.EnvoyFirmware.setup` was not used
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
