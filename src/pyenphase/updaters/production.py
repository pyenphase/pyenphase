import logging
from typing import Any

from ..const import URL_PRODUCTION, URL_PRODUCTION_JSON, SupportedFeatures
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS, EnvoyAuthenticationRequired
from ..models.envoy import EnvoyData
from ..models.system_consumption import EnvoySystemConsumption
from ..models.system_production import EnvoySystemProduction
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyProductionUpdater(EnvoyUpdater):
    """Class to handle updates for production data."""

    end_point = URL_PRODUCTION
    allow_inverters_fallback = False

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe the Envoy for this endpoint and return SupportedFeatures."""
        discovered_total_consumption = (
            SupportedFeatures.TOTAL_CONSUMPTION in discovered_features
        )
        discovered_net_consumption = (
            SupportedFeatures.NET_CONSUMPTION in discovered_features
        )
        discovered_production = SupportedFeatures.PRODUCTION in discovered_features
        if (
            discovered_total_consumption
            and discovered_net_consumption
            and discovered_production
        ):
            # Already discovered from another updater
            return None

        try:
            production_json: dict[str, Any] = await self._json_probe_request(
                self.end_point
            )
        except ENDPOINT_PROBE_EXCEPTIONS as e:
            _LOGGER.debug("Production endpoint not found at %s: %s", self.end_point, e)
            return None
        except EnvoyAuthenticationRequired as e:
            # For URL_PRODUCTION some systems return 401 even if the user has access
            # to the endpoint, but for URL_PRODUCTION_JSON is the only way to check
            # if the user has access to the endpoint
            if self.end_point == URL_PRODUCTION:
                _LOGGER.debug(
                    "Skipping production endpoint as user does"
                    " not have access to %s: %s",
                    self.end_point,
                    e,
                )
                return None
            raise

        if not discovered_production:
            production: list[dict[str, str | float | int]] | None = production_json.get(
                "production"
            )
            if production:
                for type_ in production:
                    if type_["type"] == "eim" and type_["activeCount"]:
                        self._supported_features |= SupportedFeatures.METERING
                        self._supported_features |= SupportedFeatures.PRODUCTION
                        break
                    if (
                        self.allow_inverters_fallback
                        and type_["type"] == "inverters"
                        and type_["activeCount"]
                    ):
                        self._supported_features |= SupportedFeatures.PRODUCTION
                        break

        consumption: list[dict[str, str | float | int]] | None = production_json.get(
            "consumption"
        )
        if consumption:
            for meter in consumption:
                meter_type = meter["measurementType"]
                if not meter.get("activeCount"):
                    continue
                if (
                    not discovered_total_consumption
                    and meter_type == "total-consumption"
                ):
                    self._supported_features |= SupportedFeatures.TOTAL_CONSUMPTION
                if not discovered_net_consumption and meter_type == "net-consumption":
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


class EnvoyProductionJsonFallbackUpdater(EnvoyProductionJsonUpdater):
    """Class to handle updates for production data from the production.json endpoint.

    This class will accept the production endpoint even if activeCount is 0
    """

    allow_inverters_fallback = True
