from typing import Union

import httpx
from awesomeversion import AwesomeVersion

from .auth import EnvoyLegacyAuth, EnvoyTokenAuth
from .firmware import EnvoyFirmware


class Envoy:
    def __init__(self, host: str, auth: Union[EnvoyLegacyAuth, EnvoyTokenAuth]) -> None:
        # We use our own httpx client session so we can disable SSL verification (Envoys use self-signed SSL certs)
        self.client = httpx.AsyncClient(verify=False)
        self.auth = auth
        self.host = host
        self.firmware = EnvoyFirmware(self._client, self._host)

        if AwesomeVersion(self._firmware.firmware_version) < AwesomeVersion("3.9.0"):
            # Legacy Envoy firmware
            pass

        if (
            AwesomeVersion("3.9.0")
            <= AwesomeVersion(self._firmware.firmware_version)
            < AwesomeVersion("7.0.0")
        ):
            # Envoy firmware using old envoy/installer authentication
            pass

        if AwesomeVersion(self._firmware.firmware_version) >= AwesomeVersion("7.0.0"):
            # Envoy firmware using new token authentication
            pass

    @property
    def host(self) -> str:
        return self._host

    @property
    def firmware(self) -> str:
        return self._firmware.firmware_version
