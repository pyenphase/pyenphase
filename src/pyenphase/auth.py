"""Envoy authentication methods."""

from abc import abstractmethod, abstractproperty
from typing import Any, cast

import aiohttp
import jwt
import orjson
from tenacity import retry, retry_if_exception_type, wait_random_exponential

from .const import LOCAL_TIMEOUT, URL_AUTH_CHECK_JWT
from .exceptions import EnvoyAuthenticationError, EnvoyAuthenticationRequired
from .ssl import SSL_CONTEXT


class EnvoyAuth:
    """Base class for local Envoy authentication."""

    def __init__(self, host: str) -> None:
        """
        Initializes the base class for local Envoy authentication.

        Args:
            host: The DNS name or IP address of the local Envoy device.

        """

    @abstractmethod
    async def setup(self, client: aiohttp.ClientSession) -> None:
        """
        Performs token-based authentication setup with a local Envoy device.

        Obtains and validates a JWT token for Envoy firmware version 7.0 or newer using the provided aiohttp client session. Raises EnvoyAuthenticationError if authentication fails.
        """

    @abstractproperty
    def cookies(self) -> dict[str, str]:
        """
        Returns the cookies used for authentication with the Envoy device.

        Returns:
            A dictionary of cookie names and values.

        """

    @abstractproperty
    def auth(self) -> aiohttp.DigestAuthMiddleware | None:
        """
        Returns the Digest authentication middleware for Envoy devices using firmware earlier than 7.0.

        If username or password is missing, returns None.
        """

    @abstractproperty
    def headers(self) -> dict[str, str]:
        """Return the auth headers for Envoy communication."""

    @abstractmethod
    def get_endpoint_url(self, endpoint: str) -> str:
        """
        Return the URL for the endpoint.

        :param endpoint: Envoy Endpoint to access, start with leading /

        :return: formatted full URL string
        """


class EnvoyTokenAuth(EnvoyAuth):
    """Class to authenticate with Envoy using Tokens."""

    # autodoc docstring is supplied from __init__

    JSON_LOGIN_URL = "https://enlighten.enphaseenergy.com/login/login.json?"
    TOKEN_URL = "https://entrez.enphaseenergy.com/tokens"  # nosec

    def __init__(
        self,
        host: str,
        cloud_username: str | None = None,
        cloud_password: str | None = None,
        envoy_serial: str | None = None,
        token: str | None = None,
    ) -> None:
        """
        Initializes EnvoyTokenAuth for token-based authentication with an Envoy device.

        Args:
            host: The local Envoy DNS name or IP address.
            cloud_username: Enlighten Cloud username, required to obtain a new token if not provided.
            cloud_password: Enlighten Cloud password, required to obtain a new token if not provided.
            envoy_serial: Envoy serial number, required to obtain a new token if not provided.
            token: Optional JWT token for authentication. If not provided, a token will be obtained from the Enlighten Cloud using the provided credentials.

        Use this class for Envoy firmware version 7.x and newer.

        """
        self.host = host
        self.cloud_username = cloud_username
        self.cloud_password = cloud_password
        self.envoy_serial = envoy_serial
        self._token = token
        self._is_consumer: bool = False
        self._manager_token: str = ""
        self._cookies: dict[str, str] = {}

    async def setup(self, client: aiohttp.ClientSession) -> None:
        """
        Initializes token-based authentication with a local Envoy device.

        If a token is not already provided, obtains one from the Enlighten Cloud using the configured credentials and Envoy serial number. Validates the token with the local Envoy device. The acquired token is available via the `token` property but is not persisted; callers should store it if needed across restarts.

        Args:
            client: An aiohttp ClientSession used for communication with the local Envoy.

        Raises:
            EnvoyAuthenticationError: If authentication fails or a token cannot be obtained.

        """
        if not self._token:
            self._token = await self._obtain_token()

        # Verify we have adequate credentials
        if not self._token:
            raise EnvoyAuthenticationError(
                "Unable to obtain token for Envoy authentication."
            )

        await self._check_jwt(client)

    @retry(
        retry=retry_if_exception_type(aiohttp.ClientError),
        wait=wait_random_exponential(multiplier=2, max=3),
    )
    async def _check_jwt(self, client: aiohttp.ClientSession) -> None:
        """
        Validates the current JWT token with the local Envoy device.

        Sends a request to the Envoy's authentication endpoint using the provided client session and stores cookies if the token is valid. Raises EnvoyAuthenticationError if verification fails.
        """
        async with client.get(
            f"https://{self.host}{URL_AUTH_CHECK_JWT}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=LOCAL_TIMEOUT,
        ) as resp:
            if resp.status == 200:
                self._cookies = {k: v.value for k, v in resp.cookies.items()}
                return

        raise EnvoyAuthenticationError(
            "Unable to verify token for Envoy authentication."
        )

    async def _obtain_token(self) -> str:
        """
        Obtains a JWT token for Envoy authentication using Enlighten cloud credentials.

        Raises:
            EnvoyAuthenticationError: If cloud credentials or Envoy serial are missing, login fails, token retrieval fails, or response decoding fails.

        Returns:
            The JWT token as a string.

        """
        # Raise if we don't have cloud credentials
        if not self.cloud_username or not self.cloud_password:
            raise EnvoyAuthenticationError(
                "Your firmware requires token authentication, "
                " but no cloud credentials were provided to obtain the token."
            )
        # Raise if we are missing the envoy serial number
        if not self.envoy_serial:
            raise EnvoyAuthenticationError(
                "Your firmware requires token authentication, "
                "but no envoy serial number was provided to obtain the token."
            )
        # We require a new client that checks SSL certs
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=SSL_CONTEXT), timeout=timeout
        ) as cloud_client:
            # Login to Enlighten to obtain a session ID
            response = await self._post_json_with_cloud_client(
                cloud_client,
                self.JSON_LOGIN_URL,
                data={
                    "user[email]": self.cloud_username,
                    "user[password]": self.cloud_password,
                },
            )
            if response.status != 200:
                text = await response.text()
                raise EnvoyAuthenticationError(
                    "Unable to login to Enlighten to obtain session ID from "
                    f"{self.JSON_LOGIN_URL}: "
                    f"{response.status}: {text}"
                )
            try:
                response_json = orjson.loads(await response.text())
            except orjson.JSONDecodeError as err:
                text = await response.text()
                raise EnvoyAuthenticationError(
                    "Unable to decode response from Enlighten: "
                    f"{response.status}: {text}"
                ) from err

            self._is_consumer = response_json["is_consumer"]
            self._manager_token = response_json["manager_token"]

            # Obtain the token
            response = await self._post_json_with_cloud_client(
                cloud_client,
                self.TOKEN_URL,
                json={
                    "session_id": response_json["session_id"],
                    "serial_num": self.envoy_serial,
                    "username": self.cloud_username,
                },
            )
            if response.status != 200:
                text = await response.text()
                raise EnvoyAuthenticationError(
                    "Unable to obtain token for Envoy authentication from "
                    f"{self.TOKEN_URL}: "
                    f"{response.status}: {text}"
                )
            return await response.text()

    async def refresh(self) -> None:
        """
        Obtains a new authentication token from the Enlighten cloud and updates the current token.

        Call this method to renew the Envoy JWT token using the configured cloud credentials and Envoy serial number. The refreshed token is available via the `token` property. The token is not persisted; callers should store it externally if needed across restarts.
        """
        self._token = await self._obtain_token()

    @property
    def expire_timestamp(self) -> int:
        """
        Return the expiration time for the token.

        Owner useraccount type tokens are valid for a year
        while installer tokens are only valid for 12 hours.

        :return: epoch expiration time
        """
        jwt_payload = jwt.decode(self.token, options={"verify_signature": False})
        return cast(int, jwt_payload["exp"])

    @property
    def token_type(self) -> str:
        """
        Returns the Enphase user type associated with the current JWT token.

        The user type is typically 'owner' or 'installer', indicating the level of access granted by the token.

        Raises:
            EnvoyAuthenticationRequired: If authentication has not been performed and no token is available.

        Returns:
            The user type string, either 'owner' or 'installer'.

        """
        if not self._token:
            raise EnvoyAuthenticationRequired(
                "You must authenticate to the Envoy before inspecting token."
            )
        jwt_payload = jwt.decode(self.token, options={"verify_signature": False})
        return jwt_payload["enphaseUser"]

    @retry(
        retry=retry_if_exception_type(aiohttp.ClientError),
        wait=wait_random_exponential(multiplier=2, max=3),
    )
    async def _post_json_with_cloud_client(
        self,
        cloud_client: aiohttp.ClientSession,
        url: str,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> aiohttp.ClientResponse:
        """
        Sends a POST request to the specified URL using the provided cloud client session.

        Either JSON or form data can be sent in the request body, depending on the arguments provided.

        Args:
            url: The target URL for the POST request.
            data: Optional form data to include in the request body.
            json: Optional JSON data to include in the request body.

        Returns:
            The aiohttp.ClientResponse object resulting from the POST request.

        """
        return await cloud_client.post(url, json=json, data=data)

    @property
    def token(self) -> str:
        """
        Return token used with the Envoy.

        Returns the current token, either the original specified token,
        or the token obtained from the Enlighten cloud if not specified
        or the refreshed token at expiration.

        Will assert if no token was ever specified or obtained.

        :return: jwt token string
        """
        assert self._token is not None  # nosec
        return self._token

    @property
    def manager_token(self) -> str:
        """
        Return manager token returned in enligthen login json.

        This property is only available if a token has been requested
        from the Enlighten cloud. This is only the case if no token
        was specified, or a token refresh was requested. If a valid
        token with a future expiration time was specified this method
        will assert.

        :return: token string
        """
        assert self._manager_token is not None  # nosec
        return self._manager_token

    @property
    def cookies(self) -> dict[str, str]:
        """
        Return cookies returned during setup of the envoy.

        Cookies received from the local Envoy during setup and local
        jwt check are stored in the class, this method returns these.

        :return: cookies dict
        """
        return self._cookies

    @property
    def is_consumer(self) -> bool:
        """
        Return is_consumer state returned in enligthen login json

        This property is only available if a token has been requested
        from the Enlighten cloud. This is only the case if no token
        was specified, or a token refresh was requested. If a valid
        token with a future expiration time was specified no login was
        attempted and this method will return the default false.
        If an installer account was used it will return false as well.

        :return: true if enlighten login was performed and
            used credentials are for consumer account, otherwise false
        """
        return self._is_consumer

    @property
    def auth(self) -> None:
        """
        Digest authentication for local Envoy.

        Not used with token authentication. Placeholder
        for EnvoyAuth abstractproperty

        :return: None
        """
        return None

    @property
    def headers(self) -> dict[str, str]:
        """
        Return the authentication headers for Envoy communication.

        Token authorization with Envoy requires an Authorization header
        in Bearer format with token.

        :return: token authorization header
        """
        return {"Authorization": f"Bearer {self.token}"}

    def get_endpoint_url(self, endpoint: str) -> str:
        """
        Return the URL for the endpoint.

        :param endpoint: Envoy Endpoint to access, start with leading /

        :return: formatted https URL string
        """
        return f"https://{self.host}{endpoint}"


class EnvoyLegacyAuth(EnvoyAuth):
    """Class to authenticate with legacy Envoy using digest."""

    def __init__(self, host: str, username: str, password: str) -> None:
        """
        Initializes legacy digest authentication for Envoy devices running firmware before 7.0.

        Args:
            host: The local Envoy DNS name or IP address.
            username: Username for Envoy access.
            password: Password for Envoy access.

        """
        self.host = host
        self.local_username = username
        self.local_password = password
        self._auth_middleware: aiohttp.DigestAuthMiddleware | None = None

    @property
    def auth(self) -> aiohttp.DigestAuthMiddleware | None:
        """
        Returns a DigestAuthMiddleware instance for local Envoy digest authentication.

        If the username or password is missing, returns None.
        """
        if not self.local_username or not self.local_password:
            return None
        if self._auth_middleware is None:
            self._auth_middleware = aiohttp.DigestAuthMiddleware(
                self.local_username, self.local_password
            )
        return self._auth_middleware

    async def setup(self, client: aiohttp.ClientSession) -> None:
        """
        No-op setup for legacy digest authentication.

        This method is required by the EnvoyAuth interface but performs no action, as digest authentication does not require setup.
        """
        # No setup required for legacy authentication

    @property
    def headers(self) -> dict[str, str]:
        """
        Return the headers needed for Envoy authentication.

        DigestAuth does not use authorization header. Placeholder
        for EnvoyAuth abstractproperty.

        :return: empty dict
        """
        return {}

    def get_endpoint_url(self, endpoint: str) -> str:
        """
        Return the URL for the endpoint.

        :param endpoint: Envoy Endpoint to access, start with leading /

        :return: formatted http URL string
        """
        return f"http://{self.host}{endpoint}"

    @property
    def cookies(self) -> dict[str, str]:
        """
        Return cookies returned during setup of the envoy.

        DigestAuth does not use cookies. Placeholder
        for EnvoyAuth abstractproperty.

        :return: empty dict
        """
        return {}
