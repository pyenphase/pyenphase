import contextlib
import logging
import ssl
from typing import Any

import httpx
from awesomeversion import AwesomeVersion
from envoy_utils.envoy_utils import EnvoyUtils
from tenacity import retry, retry_if_exception_type, wait_random_exponential

from .auth import EnvoyAuth, EnvoyLegacyAuth, EnvoyTokenAuth
from .exceptions import EnvoyAuthenticationRequired
from .firmware import EnvoyFirmware, EnvoyFirmwareCheckError

_LOGGER = logging.getLogger(__name__)

TIMEOUT = 15
LEGACY_ENVOY_VERSION = AwesomeVersion("3.9.0")
AUTH_TOKEN_MIN_VERSION = AwesomeVersion("7.0.0")


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

    def __init__(self, host: str) -> None:
        """Initialize the Envoy class."""
        # We use our own httpx client session so we can disable SSL verification (Envoys use self-signed SSL certs)
        self._client = httpx.AsyncClient(
            verify=_NO_VERIFY_SSL_CONTEXT, timeout=TIMEOUT
        )  # nosec
        self.auth: EnvoyAuth | None = None
        self._host = host
        self._firmware = EnvoyFirmware(self._client, self._host)

    @retry(
        retry=retry_if_exception_type(EnvoyFirmwareCheckError),
        wait=wait_random_exponential(multiplier=2, max=10),
    )
    async def setup(self) -> None:
        """Obtain the firmware version for later Envoy authentication."""
        await self._firmware.setup()

    async def authenticate(
        self,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
    ) -> None:
        """Authenticate to the Envoy based on firmware version."""
        if self._firmware.version < LEGACY_ENVOY_VERSION:
            # Legacy Envoy firmware
            _LOGGER.debug("Authenticating to Envoy using legacy authentication")

        if LEGACY_ENVOY_VERSION <= self._firmware.version < AUTH_TOKEN_MIN_VERSION:
            # Envoy firmware using old envoy/installer authentication
            _LOGGER.debug(
                "Authenticating to Envoy using envoy/installer authentication"
            )
            full_serial = self._firmware.serial
            if username is None:
                username = "installer"
                password = EnvoyUtils.get_password(full_serial, username)
            elif username == "envoy" and password is None:
                # The default password for the envoy user is the first 6 digits of the serial number
                password = full_serial[:6]

            if username and password:
                self.auth = EnvoyLegacyAuth(self.host, username, password)

        if self._firmware.version >= AUTH_TOKEN_MIN_VERSION:
            # Envoy firmware using new token authentication
            _LOGGER.debug("Authenticating to Envoy using token authentication")
            if token is not None:
                self.auth = EnvoyTokenAuth(self.host, token=token)
            elif (
                username is not None
                and password is not None
                and self._firmware.serial is not None
            ):
                self.auth = EnvoyTokenAuth(
                    self.host, username, password, self._firmware.serial
                )

        if self.auth is not None:
            await self.auth.setup(self._client)
        else:
            _LOGGER.error(
                "You must include username/password or token to authenticate to the Envoy."
            )
            raise EnvoyAuthenticationRequired("Could not setup authentication object.")

    async def request(self, endpoint: str) -> dict[str, Any]:
        """Make a request to the Envoy."""
        if self.auth is None:
            raise EnvoyAuthenticationRequired(
                "You must authenticate to the Envoy before making requests."
            )

        r = await self._client.get(
            f"https://{self._host}{endpoint}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.auth.token}",
            },
            cookies=self.auth.cookies,
        )
        return r.json()

    @property
    def host(self) -> str:
        """Return the Envoy host."""
        return self._host

    @property
    def firmware(self) -> str:
        """Return the Envoy firmware version."""
        return self._firmware.version
