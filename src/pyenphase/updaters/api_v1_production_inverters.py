import logging
from typing import Any

from awesomeversion import AwesomeVersion

from ..const import URL_PRODUCTION_INVERTERS, SupportedFeatures
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS
from ..models.envoy import EnvoyData
from ..models.inverter import EnvoyInverter
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyApiV1ProductionInvertersUpdater(EnvoyUpdater):
    def should_probe(
        self, envoy_version: AwesomeVersion, discovered_features: SupportedFeatures
    ) -> bool:
        """Return True if this updater should be probed."""
        return SupportedFeatures.INVERTERS not in discovered_features

    async def probe(self) -> SupportedFeatures | None:
        """Probe the Envoy for this updater and return SupportedFeatures."""
        try:
            await self._json_probe_request(URL_PRODUCTION_INVERTERS)
        except ENDPOINT_PROBE_EXCEPTIONS as e:
            _LOGGER.debug(
                "Production endpoint not found at %s: %s", URL_PRODUCTION_INVERTERS, e
            )
            return None
        self._supported_features |= SupportedFeatures.INVERTERS
        return self._supported_features

    async def update(self, envoy_data: EnvoyData) -> None:
        """Update the Envoy for this updater."""
        inverters_data: list[dict[str, Any]] = await self._json_request(
            URL_PRODUCTION_INVERTERS
        )
        envoy_data.raw[URL_PRODUCTION_INVERTERS] = inverters_data
        envoy_data.inverters = {
            inverter["serialNumber"]: EnvoyInverter.from_v1_api(inverter)
            for inverter in inverters_data
        }
