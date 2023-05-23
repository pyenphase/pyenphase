import contextlib
import ssl
from typing import Union

import httpx
from awesomeversion import AwesomeVersion

from .auth import EnvoyLegacyAuth, EnvoyTokenAuth
from .firmware import EnvoyFirmware


def create_no_verify_ssl_context() -> ssl.SSLContext:
    """Return an SSL context that does not verify the server certificate.
    This is a copy of aiohttp's create_default_context() function, with the
    ssl verify turned off and old SSL versions enabled.

    https://github.com/aio-libs/aiohttp/blob/33953f110e97eecc707e1402daa8d543f38a189b/aiohttp/connector.py#L911
    """
    sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    sslcontext.check_hostname = False
    sslcontext.verify_mode = ssl.CERT_NONE
    # Allow all ciphers rather than only Python 3.10 default
    sslcontext.set_ciphers("DEFAULT")
    with contextlib.suppress(AttributeError):
        # This only works for OpenSSL >= 1.0.0
        sslcontext.options |= ssl.OP_NO_COMPRESSION
    sslcontext.set_default_verify_paths()
    return sslcontext


_NO_VERIFY_SSL_CONTEXT = create_no_verify_ssl_context()


class Envoy:
    """Class for querying and determining the Envoy firmware version."""

    def __init__(self, host: str, auth: Union[EnvoyLegacyAuth, EnvoyTokenAuth]) -> None:
        """Initialize the Envoy class."""
        # We use our own httpx client session so we can disable SSL verification (Envoys use self-signed SSL certs)
        self._client = httpx.AsyncClient(verify=_NO_VERIFY_SSL_CONTEXT)  # nosec
        self.auth = auth
        self._host = host
        self._firmware = EnvoyFirmware(self._host)

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
        """Return the Envoy host."""
        return self._host

    @property
    def firmware(self) -> str:
        """Return the Envoy firmware version."""
        return self._firmware.firmware_version
