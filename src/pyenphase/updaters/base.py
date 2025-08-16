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
        Base class for Envoy updaters.

        Updaters should implement a subclass of EnvoyUpdater.

        .. code-block:: python

            class EnvoyXyzUpdater(EnvoyUpdater):

        :param envoy_version: firmware version Envoy is running
        :param probe_request: callable specified by
            :any:`Envoy` to send probe request to the Envoy
            during :any:`Envoy.probe`
        :param request: callable specified by :any:`Envoy` to
            send request to the Envoy during :any:`Envoy.update`
        :param common_properties: properties to share between
            probe and update or between updaters
        """
        self._envoy_version = envoy_version
        self._probe_request = probe_request
        self._request = request
        self._supported_features = SupportedFeatures(0)
        self._common_properties = common_properties

    async def _json_request(self, end_point: str) -> Any:
        """
        Make a request to the Envoy and return the JSON response.

        Updaters should use this to collect data during :any:`update` method.

        .. code-block:: python

            xyz_json: dict[str, Any] = await self._json_request(
                "/xyz/endpoint"
            )

        :param end_point: Envoy endpoint to request. See :any:`Envoy.request`
        :raises EnvoyHTTPStatusError: If http status not in 2xx range
        :raises Also See: :any:`Envoy.request`
        :return: JSON content from response
        """
        response = await self._request(end_point)
        if not (200 <= response.status < 300):
            raise EnvoyHTTPStatusError(response.status, str(response.url))
        return json_loads(end_point, await response.read())

    async def _json_probe_request(self, end_point: str) -> Any:
        """
        Make a probe request to the Envoy and return the JSON response.

        Updaters should use this to collect data during :any:`probe` method.

        .. code-block:: python

            xyz_json: dict[str, Any] = await self._json_probe_request(
                "/xyz/endpoint"
            )

        :param end_point: Envoy endpoint to request. See :any:`Envoy.probe`
        :raises EnvoyHTTPStatusError: If http status not in 2xx range
        :raises Also See: :any:`Envoy.probe_request`
        :return: JSON content from response
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
        Probe the Envoy for this updater and return SupportedFeatures.

        Updater must implement a probe method to report which features it supports.
        Probe method of each registered updater is called by :any:'Envoy.probe'.
        Intent of probe is to determine if this updater should be used
        to obtain the data in its scope from the Envoy. If the Envoy
        model does not provide the data the method should return None.

        If the Envoy model does provide the data in scope, the method should
        return a supported features mask for which it can provide data.
        Any supported feature that is already included in the passed
        discovered_features parameter should NOT be included in the result
        as these are already provided by another updater and this updater
        should back off from providing that feature data.

        .. code-block:: python

            async def probe(
                    self, discovered_features: SupportedFeatures
                ) -> SupportedFeatures | None:
                    \"\"\"Probe the Envoy for this endpoint and return SupportedFeatures.\"\"\"
                    pass

        :param discovered_features: Mask of already discovered SupportedFeatures
        :return: Mask of SupportedFeatures to be added to already discovered
            features (and not yet in discovered_features).
        """

    @abstractmethod
    async def update(self, envoy_data: EnvoyData) -> None:
        """
        Get data from the Envoy and store in EnvoyData.

        Updater must implement an update method to add/update data in
        :any:`EnvoyData`. Update method of each registered updater is
        called by :any:`Envoy.update`.

        The update method is expected to obtain the required data from
        the envoy, map it to the internal data model and store the data.

        .. code-block:: python

            async def update(self, envoy_data: EnvoyData) -> None:
                \"\"\"Get data from the Envoy and store in EnvoyData.\"\"\"
                pass

        :param envoy_data: Envoy data model to store collected data in
        """
