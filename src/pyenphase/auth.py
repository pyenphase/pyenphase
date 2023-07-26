"""Envoy authentication methods."""

import json
from abc import abstractmethod, abstractproperty

import httpx

from .exceptions import EnvoyAuthenticationError


class EnvoyAuth:
    """Base class for Envoy authentication."""

    def __init__(self, host: str) -> None:
        """Initialize the EnvoyAuth class."""
        pass

    @abstractmethod
    async def setup(self, client: httpx.AsyncClient) -> None:
        """Obtain the token for Envoy authentication."""

    @abstractproperty
    def token(self) -> str:
        """Return the Envoy token."""

    @abstractproperty
    def cookies(self) -> dict[str, str]:
        """Return the Envoy cookie."""


class EnvoyTokenAuth(EnvoyAuth):
    def __init__(
        self,
        host: str,
        cloud_username: str | None = None,
        cloud_password: str | None = None,
        envoy_serial: str | None = None,
        token: str | None = None,
    ) -> None:
        self.host = host
        self.cloud_username = cloud_username
        self.cloud_password = cloud_password
        self.envoy_serial = envoy_serial
        self._token = token

    async def setup(self, client: httpx.AsyncClient) -> None:
        """Obtain the token for Envoy authentication."""

        if not self._token:
            # Raise if we don't have cloud credentials
            if not self.cloud_username or not self.cloud_password:
                raise EnvoyAuthenticationError(
                    "Your firmware requires token authentication, but no cloud credentials were provided to obtain the token."
                )
            # Raise if we are missing the envoy serial number
            if not self.envoy_serial:
                raise EnvoyAuthenticationError(
                    "Your firmware requires token authentication, but no envoy serial number was provided to obtain the token."
                )

            # we require a new client that checks SSL certs
            self.cloud_client = httpx.AsyncClient()

            # Login to Enlighten to obtain a session ID
            data = {
                "user[email]": self.cloud_username,
                "user[password]": self.cloud_password,
            }
            req = await self.cloud_client.post(
                "https://enlighten.enphaseenergy.com/login/login.json?", data=data
            )
            if req.status_code != 200:
                raise EnvoyAuthenticationError(
                    "Unable to login to Enlighten to obtain session ID."
                )
            response = json.loads(req.text)
            self._is_consumer = response["is_consumer"]
            self._manager_token = response["manager_token"]

            # Obtain the token
            data = {
                "session_id": response["session_id"],
                "serial_num": self.envoy_serial,
                "username": self.cloud_username,
            }
            req = await self.cloud_client.post(
                "https://entrez.enphaseenergy.com/tokens", json=data
            )
            if req.status_code != 200:
                raise EnvoyAuthenticationError(
                    "Unable to obtain token for Envoy authentication."
                )
            self._token = req.text

        # Verify we have adequate credentials
        if not self.token:
            raise EnvoyAuthenticationError(
                "Unable to obtain token for Envoy authentication."
            )

        # Verify the token and obtain cookie with session ID necessary for some API calls
        req = await client.get(
            f"https://{self.host}/auth/check_jwt",
            headers={"Authorization": f"Bearer {self.token}"},
        )

        if req.status_code != 200:
            raise EnvoyAuthenticationError(
                "Unable to verify token for Envoy authentication."
            )

        self._cookies = req.cookies

    @property
    def token(self) -> str:
        assert self._token is not None  # nosec
        return self._token

    @property
    def manager_token(self) -> str:
        assert self._manager_token is not None  # nosec
        return self._manager_token

    @property
    def cookies(self) -> dict[str, str]:
        return self._cookies

    @property
    def is_consumer(self) -> bool:
        return self._is_consumer


class EnvoyLegacyAuth(EnvoyAuth):
    """Class for legacy Envoy authentication."""

    def __init__(self, host: str, username: str, password: str) -> None:
        self.host = host
        self.local_username = username
        self.local_password = password

    @property
    def local_auth(self) -> httpx.DigestAuth:
        """Digest authentication for local Envoy."""
        if not self.local_username or not self.local_password:
            return None
        return httpx.DigestAuth(self.local_username, self.local_password)

    async def setup(self, client: httpx.AsyncClient) -> None:
        """Setup auth"""
        # No setup required for legacy authentication
