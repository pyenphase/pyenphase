from abc import abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp
from awesomeversion import AwesomeVersion

from ..const import SupportedFeatures
from ..exceptions import EnvoyHTTPStatusError
from ..json import json_loads
from ..models.common import CommonProperties
from ..models.envoy import EnvoyData


class EnvoyUpdater:
    """Base class for Envoy updaters."""

    def __init__(
        self,
        envoy_version: AwesomeVersion,
        probe_request: Callable[[str], Awaitable[aiohttp.ClientResponse]],
        request: Callable[[str], Awaitable[aiohttp.ClientResponse]],
        common_properties: CommonProperties,
    ) -> None:
        """
        Initializes the EnvoyUpdater with version information, request callables, and common properties.

        Args:
                envoy_version: The version of the Envoy device.
                probe_request: Asynchronous callable for sending probe requests to the Envoy.
                request: Asynchronous callable for sending general requests to the Envoy.
                common_properties: Shared properties relevant to the Envoy device.

        """
        self._envoy_version = envoy_version
        self._probe_request = probe_request
        self._request = request
        self._supported_features = SupportedFeatures(0)
        self._common_properties = common_properties

    async def _json_request(self, end_point: str) -> Any:
        """
        Sends an asynchronous request to the Envoy device and returns the parsed JSON response.

        Raises:
            EnvoyHTTPStatusError: If the HTTP response status is not in the 200–299 range.

        """
        response = await self._request(end_point)
        if not (200 <= response.status < 300):
            raise EnvoyHTTPStatusError(response.status, str(response.url))
        return json_loads(end_point, await response.read())

    async def _json_probe_request(self, end_point: str) -> Any:
        """
        Sends a probe request to the Envoy device and returns the parsed JSON response.

        Raises:
            EnvoyHTTPStatusError: If the HTTP response status is not in the 200–299 range.

        Returns:
            The parsed JSON content from the Envoy device's response.

        """
        response = await self._probe_request(end_point)
        if not (200 <= response.status < 300):
            raise EnvoyHTTPStatusError(response.status, str(response.url))
        return json_loads(end_point, await response.read())

    @abstractmethod
    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """
        Probes the Envoy device to determine supported features for this updater.

        Args:
            discovered_features: Features already identified on the Envoy device.

        Returns:
            An updated SupportedFeatures object if new features are detected, or None if no changes are found.

        """

    @abstractmethod
    async def update(self, envoy_data: EnvoyData) -> None:
        """Update the Envoy for this updater."""
