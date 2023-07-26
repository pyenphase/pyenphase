import httpx
from awesomeversion import AwesomeVersion
from lxml import etree  # nosec

from .exceptions import EnvoyFirmwareCheckError, EnvoyFirmwareFatalCheckError


class EnvoyFirmware:
    """Class for querying and determining the Envoy firmware version."""

    def __init__(self, _client: httpx.AsyncClient, host: str) -> None:
        self._client = _client
        self._host = host

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
                return

        else:
            # If we get a different status code, raise an exception
            raise EnvoyFirmwareCheckError(result.status_code, result.text)

    @property
    def version(self) -> AwesomeVersion:
        return self._firmware_version

    @property
    def serial(self) -> str:
        return self._serial_number
