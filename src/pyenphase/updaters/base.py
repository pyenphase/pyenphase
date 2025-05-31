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
        """Initialize the Envoy endpoint."""
        self._envoy_version = envoy_version
        self._probe_request = probe_request
        self._request = request
        self._supported_features = SupportedFeatures(0)
        self._common_properties = common_properties

    async def _json_request(self, end_point: str) -> Any:
        """Make a request to the Envoy and return the JSON response."""
        response = await self._request(end_point)
        if not (200 <= response.status < 300):
            raise EnvoyHTTPStatusError(response.status, str(response.url))
        return json_loads(end_point, await response.read())

    async def _json_probe_request(self, end_point: str) -> Any:
        """Make a probe request to the Envoy and return the JSON response."""
        response = await self._probe_request(end_point)
        if not (200 <= response.status < 300):
            raise EnvoyHTTPStatusError(response.status, str(response.url))
        return json_loads(end_point, await response.read())

    @abstractmethod
    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe the Envoy for this updater and return SupportedFeatures."""

    @abstractmethod
    async def update(self, envoy_data: EnvoyData) -> None:
        """Update the Envoy for this updater."""
