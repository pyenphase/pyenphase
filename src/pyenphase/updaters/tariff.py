import logging

from ..const import URL_TARIFF, SupportedFeatures
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS, EnvoyAuthenticationRequired
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
        except EnvoyAuthenticationRequired as e:
            # For some systems (Firmware: 3.9.36) return 401 for
            # this endpoint even if the user is authenticated.
            _LOGGER.debug(
                "Skipping tariff endpoint as user does" " not have access to %s: %s",
                URL_TARIFF,
                e,
            )
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
