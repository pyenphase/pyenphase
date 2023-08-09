import logging
from typing import Any

from ..const import URL_PRODUCTION, URL_PRODUCTION_JSON, SupportedFeatures
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS
from ..models.envoy import EnvoyData
from ..models.system_consumption import EnvoySystemConsumption
from ..models.system_production import EnvoySystemProduction
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyProductionUpdater(EnvoyUpdater):
    """Class to handle updates for production data."""

    end_point = URL_PRODUCTION

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe the Envoy for this endpoint and return SupportedFeatures."""
        if (
            SupportedFeatures.TOTAL_CONSUMPTION in discovered_features
            or SupportedFeatures.NET_CONSUMPTION in discovered_features
        ) and SupportedFeatures.PRODUCTION in discovered_features:
            # Already discovered from another updater
            return None

        try:
            production_json: dict[str, Any] = await self._json_probe_request(
                self.end_point
            )
        except ENDPOINT_PROBE_EXCEPTIONS as e:
            _LOGGER.debug("Production endpoint not found at %s: %s", self.end_point, e)
            return None

        production: list[dict[str, str | float | int]] | None = production_json.get(
            "production"
        )
        if production:
            for type_ in production:
                if type_["type"] == "eim" and type_["activeCount"]:
                    self._supported_features |= SupportedFeatures.METERING
                    self._supported_features |= SupportedFeatures.PRODUCTION
                    break

        consumption: list[dict[str, str | float | int]] | None = production_json.get(
            "consumption"
        )
        if consumption:
            for meter in consumption:
                meter_type = meter["measurementType"]
                if meter_type == "total-consumption":
                    self._supported_features |= SupportedFeatures.TOTAL_CONSUMPTION
                elif meter_type == "net-consumption":
                    self._supported_features |= SupportedFeatures.NET_CONSUMPTION

        return self._supported_features

    async def update(self, envoy_data: EnvoyData) -> None:
        """Update the Envoy for this endpoint."""
        production_data = await self._json_request(self.end_point)
        envoy_data.raw[self.end_point] = production_data
        if self._supported_features & SupportedFeatures.PRODUCTION:
            envoy_data.system_production = EnvoySystemProduction.from_production(
                production_data
            )
        if (
            self._supported_features & SupportedFeatures.NET_CONSUMPTION
            or self._supported_features & SupportedFeatures.TOTAL_CONSUMPTION
        ):
            envoy_data.system_consumption = EnvoySystemConsumption.from_production(
                production_data
            )


class EnvoyProductionJsonUpdater(EnvoyProductionUpdater):
    """Class to handle updates for production data from the production.json endpoint."""

    end_point = URL_PRODUCTION_JSON
