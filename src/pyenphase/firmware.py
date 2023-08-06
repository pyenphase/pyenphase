import httpx
from awesomeversion import AwesomeVersion
from lxml import etree  # nosec

from .exceptions import EnvoyFirmwareCheckError, EnvoyFirmwareFatalCheckError


class EnvoyFirmware:
    """Class for querying and determining the Envoy firmware version."""

    __slots__ = (
        "_client",
        "_host",
        "_firmware_version",
        "_serial_number",
        "_part_number",
    )

    def __init__(self, _client: httpx.AsyncClient, host: str) -> None:
        """Initialize the Envoy firmware version."""
        self._client = _client
        self._host = host
        self._firmware_version: str | None = None
        self._serial_number: str | None = None
        self._part_number: str | None = None

    async def setup(self) -> None:
        """Obtain the firmware version for Envoy authentication."""
        # <envoy>/info will return XML with the firmware version
        try:
            result = await self._client.get(f"http://{self._host}/info")
        except httpx.ConnectError:
            raise EnvoyFirmwareFatalCheckError(500, "Unable to connect to Envoy")
        except httpx.HTTPError:
            raise EnvoyFirmwareCheckError(500, "Unable to query firmware version")

        if result.status_code == 200:
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
