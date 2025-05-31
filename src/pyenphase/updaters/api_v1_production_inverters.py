import logging
from typing import Any

from ..const import URL_DEVICE_DATA, URL_PRODUCTION_INVERTERS, SupportedFeatures
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS, EnvoyAuthenticationRequired
from ..models.envoy import EnvoyData
from ..models.inverter import EnvoyInverter
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyApiV1ProductionInvertersUpdater(EnvoyUpdater):
    """Class to handle updates for inverter production data."""

    _preferred_endpoint = URL_PRODUCTION_INVERTERS

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe the Envoy for this updater and return SupportedFeatures."""
        for endpoint in (
            URL_DEVICE_DATA,
            URL_PRODUCTION_INVERTERS,
        ):
            try:
                await self._json_probe_request(endpoint)
                self._preferred_endpoint = endpoint
                self._supported_features |= SupportedFeatures.INVERTERS
                return self._supported_features
            except ENDPOINT_PROBE_EXCEPTIONS as e:
                _LOGGER.debug("Production endpoint not found at %s: %s", endpoint, e)
            except EnvoyAuthenticationRequired as e:
                _LOGGER.debug(
                    "Disabling inverters production endpoint as user does"
                    " not have access to %s: %s",
                    endpoint,
                    e,
                )

    async def update(self, envoy_data: EnvoyData) -> None:
        """Update the Envoy for this updater."""
        inverters_data: list[dict[str, Any]] | dict[str, Any] = (
            await self._json_request(self._preferred_endpoint)
        )
        envoy_data.raw[self._preferred_endpoint] = inverters_data
        if self._preferred_endpoint == URL_PRODUCTION_INVERTERS:
            envoy_data.inverters = {
                inverter["serialNumber"]: EnvoyInverter.from_v1_api(inverter)
                for inverter in inverters_data
            }
        if self._preferred_endpoint == URL_DEVICE_DATA:
            envoy_data.inverters = {
                inverter["sn"]: EnvoyInverter.from_device_data(inverter)
                for id, inverter in inverters_data.items()
                if id not in ("deviceCount", "deviceDataLimit")
                and inverter["devName"] == "pcu"
            }
