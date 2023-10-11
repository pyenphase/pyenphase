import logging

from pyenphase.exceptions import ENDPOINT_PROBE_EXCEPTIONS

from ..const import URL_TARIFF, SupportedFeatures
from ..models.envoy import EnvoyData
from ..models.tariff import EnvoyTariff
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyTariffUpdater(EnvoyUpdater):
    """Class to handle updates for the Envoy tariff data."""

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        try:
            result = await self._json_probe_request(URL_TARIFF)
        except ENDPOINT_PROBE_EXCEPTIONS as e:
            _LOGGER.debug("Tariff endpoint not found: %s", e)
            return None
        else:
            if not result or "error" in result:
                _LOGGER.debug("No tariff data found")
                return None
            self._supported_features |= SupportedFeatures.TARIFF
        return self._supported_features

    async def update(self, envoy_data: EnvoyData) -> None:
        raw = await self._json_request(URL_TARIFF)
        envoy_data.raw[URL_TARIFF] = raw

        envoy_data.tariff = EnvoyTariff.from_api(raw["tariff"])
