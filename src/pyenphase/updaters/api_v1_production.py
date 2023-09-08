import logging
from typing import Any

from ..const import URL_PRODUCTION_V1, SupportedFeatures
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS
from ..models.envoy import EnvoyData
from ..models.system_production import EnvoySystemProduction
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyApiV1ProductionUpdater(EnvoyUpdater):
    """Class to handle updates for production data."""

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe the Envoy for this updater and return SupportedFeatures."""
        if SupportedFeatures.PRODUCTION in discovered_features:
            # Already discovered from another updater
            return None

        try:
            response: dict[str, Any] = await self._json_probe_request(URL_PRODUCTION_V1)
        except ENDPOINT_PROBE_EXCEPTIONS as e:
            _LOGGER.debug(
                "Production endpoint not found at %s: %s", URL_PRODUCTION_V1, e
            )
            return None
        if all(value == 0 for value in response.values()):
            _LOGGER.debug(
                "Detected broken production endpoint bug at %s: %s",
                URL_PRODUCTION_V1,
                response,
            )
            return None

        self._supported_features |= SupportedFeatures.PRODUCTION
        return self._supported_features

    async def update(self, envoy_data: EnvoyData) -> None:
        """Update the Envoy for this updater."""
        production_data = await self._json_request(URL_PRODUCTION_V1)
        envoy_data.raw[URL_PRODUCTION_V1] = production_data
        envoy_data.system_production = EnvoySystemProduction.from_v1_api(
            production_data
        )
