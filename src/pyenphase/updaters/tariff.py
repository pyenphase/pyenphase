import logging

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
        return discovered_features

    async def update(self, envoy_data: EnvoyData) -> None:
        raw = await self._json_request(URL_TARIFF)
        envoy_data.raw[URL_TARIFF] = raw

        envoy_data.tariff = EnvoyTariff.from_api(raw["tariff"])
