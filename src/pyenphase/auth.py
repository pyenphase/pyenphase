"""Envoy authentication methods."""

import json

import httpx

from .exceptions import EnvoyAuthenticationError


class EnvoyTokenAuth:
    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        cloud_username: str | None = None,
        cloud_password: str | None = None,
        envoy_serial: str | None = None,
        token: str | None = None,
    ) -> None:
        self.cloud_client = client or httpx.AsyncClient()
        self.cloud_username = cloud_username
        self.cloud_password = cloud_password
        self.envoy_serial = envoy_serial
        self._token = token

    async def setup(self) -> None:
        """Obtain the token for Envoy authentication."""
        # Login to Enlighten to obtain a session ID
        data = {
            "user[email]": self.cloud_username,
            "user[password]": self.cloud_password,
        }
        req = await self.cloud_client.post(
            "https://enlighten.enphaseenergy.com/login.json?", data=data
        )
        response = json.loads(req.text)

        # Obtain the token
        data = {
            "session_id": response["session_id"],
            "serial_num": self.envoy_serial,
            "username": self.cloud_username,
        }
        req = await self.cloud_client.post(
            "https://entrez.enphaseenrgy.com/tokens", json=data
        )
        self._token = req.text

        # If a token wasn't provided, fetch it from the cloud API
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

        # Verify we have adequate credentials
        if not self.token:
            raise EnvoyAuthenticationError(
                "Unable to obtain token for Envoy authentication."
            )

    @property
    def token(self) -> str:
        assert self._token is not None  # nosec
        return self._token

    @property
    def token_header(self) -> str | None:
        if not self._token:
            return None
        return f"Bearer {self._token}"


class EnvoyLegacyAuth:
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
