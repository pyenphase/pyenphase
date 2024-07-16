import logging
from typing import Any

from ..const import ENSEMBLE_MIN_VERSION, URL_GEN_CONFIG, SupportedFeatures
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS
from ..models.envoy import EnvoyData
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyGeneratorUpdater(EnvoyUpdater):
    """Class to handle updates for Generator information."""

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe the Envoy for this updater and return SupportedFeatures."""
        if self._envoy_version < ENSEMBLE_MIN_VERSION:
            _LOGGER.debug("Firmware too old for Ensemble support")
            return None

        # If there's no Enpower smart switch, we can skip the generator probe
        if SupportedFeatures.ENPOWER not in discovered_features:
            return None

        # Check for generator support
        try:
            result = await self._json_probe_request(URL_GEN_CONFIG)
        except ENDPOINT_PROBE_EXCEPTIONS as e:
            _LOGGER.debug("Generator config endpoint not found: %s", e)
        else:
            if not result or "error" in result or "err" in result:
                # Newer firmware with no generator configured returns an empty dict
                _LOGGER.debug("No generator found")
                return None

            self._supported_features |= SupportedFeatures.GENERATOR

        return self._supported_features

    async def update(self, envoy_data: EnvoyData) -> None:
        """Update the generator data if supported."""
        generator_config_data: list[dict[str, Any]] = await self._json_request(
            URL_GEN_CONFIG
        )
        envoy_data.raw[URL_GEN_CONFIG] = generator_config_data
