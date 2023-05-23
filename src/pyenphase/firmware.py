import httpx
from awesomeversion import AwesomeVersion
from lxml import etree

from .exceptions import EnvoyFirmwareCheckError


class EnvoyFirmware:
    """Class for querying and determining the Envoy firmware version."""

    async def __init__(self, host) -> str:
        self._client = httpx.AsyncClient(verify=False)
        self._host = host

        # <envoy>/info will return XML with the firmware version
        try:
            result = await self._client.get(f"{self.host}/info")
        except httpx.HTTPError:
            raise EnvoyFirmwareCheckError("Unable to query firmware version")

        if result.status_code == 200:
            xml = etree.fromstring(result.content)
            self.firmware_version = xml.findtext("package[@nameW='app']/version")

        # If we get a different status code, raise an exception
        raise EnvoyFirmwareCheckError(result.status_code, result.text)

    @property
    def requires_token_auth(self) -> bool:
        return AwesomeVersion(self.firmware_version) >= AwesomeVersion("7.0.0")

    @property
    def version(self) -> str:
        return self.firmware_version
