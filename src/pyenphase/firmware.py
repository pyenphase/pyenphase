import httpx
from awesomeversion import AwesomeVersion
from lxml import etree  # nosec

from .exceptions import EnvoyFirmwareCheckError
from .ssl import NO_VERIFY_SSL_CONTEXT


class EnvoyFirmware:
    """Class for querying and determining the Envoy firmware version."""

    def __init__(self, host: str) -> None:
        self._client = httpx.AsyncClient(verify=NO_VERIFY_SSL_CONTEXT)  # nosec
        self._host = host

    async def setup(self) -> None:
        """Obtain the firmware version for Envoy authentication."""
        # <envoy>/info will return XML with the firmware version
        try:
            result = await self._client.get(f"{self._host}/info")
        except httpx.HTTPError:
            raise EnvoyFirmwareCheckError(500, "Unable to query firmware version")

        if result.status_code == 200:
            xml = etree.fromstring(result.content)  # nosec
            self.firmware_version = xml.findtext("package[@nameW='app']/version")

        # If we get a different status code, raise an exception
        raise EnvoyFirmwareCheckError(result.status_code, result.text)

    @property
    def requires_token_auth(self) -> bool:
        return AwesomeVersion(self.firmware_version) >= AwesomeVersion("7.0.0")

    @property
    def version(self) -> str:
        return self.firmware_version
