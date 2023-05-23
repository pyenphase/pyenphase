import asyncio
import json

import httpx

from .exceptions import EnvoyAuthenticationError
from .firmware import EnvoyFirmware

"""Envoy authentication methods."""


class EnvoyTokenAuth:
    def __init__(
        self,
        client,
        cloud_username=None,
        cloud_password=None,
        envoy_serial=None,
        token=None,
    ):
        self.cloud_client = client or httpx.AsyncClient()
        self.cloud_username = cloud_username
        self.cloud_password = cloud_password
        self.envoy_serial = envoy_serial
        self._token = token

        async def fetch_token(self):
            # Login to Enlighten to obtain a session ID
            data = {"user[email]": cloud_username, "user[password]": cloud_password}
            req = await self.cloud_client.post(
                "https://enlighten.enphaseenergy.com/login.json?", data=data
            )
            response = json.loads(req.text)

            # Obtain the token
            data = {
                "session_id": response["session_id"],
                "serial_num": envoy_serial,
                "username": cloud_username,
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

            asyncio.run(fetch_token(self))

        # Verify we have adequate credentials
        if not self.token:
            raise EnvoyAuthenticationError(
                "Unable to obtain token for Envoy authentication."
            )

    @property
    def token(self) -> str:
        return self._token

    @property
    def token_header(self) -> str:
        if not self._token:
            return None
        return f"Bearer {self._token}"


class EnvoyLegacyAuth:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

    @property
    def local_auth(self) -> httpx.DigestAuth:
        if not self.local_username or not self.local_password:
            return None
        return httpx.DigestAuth(self.local_username, self.local_password)
