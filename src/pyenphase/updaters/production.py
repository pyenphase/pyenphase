"""Envoy production data updater"""

import logging
from typing import Any

from ..const import PHASENAMES, URL_PRODUCTION, URL_PRODUCTION_JSON, SupportedFeatures
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

        # obtain any registered production endpoints that replied back from the common list
        # when in allow_inverters_fallback mode we can use the first one that worked
        working_endpoints: list[str] = self._common_properties.production_fallback_list
        if (
            discovered_total_consumption
            and discovered_net_consumption
            and discovered_production
        ):
            # Already discovered from another updater
            return None

        # when active allow_inverters_fallback use first successful endpoint registered in the list
        if self.allow_inverters_fallback and working_endpoints:
            self.end_point = working_endpoints[0]

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

        active_phase_count = 0
        phase_count = self._common_properties.phase_count

        # if endpoint is not in the list of successful endpoints yet, add it.
        if (
            self.end_point not in working_endpoints
            and not self.allow_inverters_fallback
        ):
            working_endpoints.append(self.end_point)

        if not discovered_production:
            production: list[dict[str, Any]] | None = production_json.get("production")
            if production:
                for type_ in production:
                    if type_["type"] == "eim" and type_["activeCount"]:
                        self._supported_features |= SupportedFeatures.METERING
                        self._supported_features |= SupportedFeatures.PRODUCTION
                        if lines := type_.get("lines"):
                            active_phase_count = len(lines)
                        break
                    if (
                        self.allow_inverters_fallback
                        and type_["type"] == "inverters"
                        and type_["activeCount"]
                    ):
                        self._supported_features |= SupportedFeatures.PRODUCTION
                        break

        consumption: list[dict[str, Any]] | None = production_json.get("consumption")
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
                if lines := meter.get("lines"):
                    active_phase_count = len(lines)

        # register the updated fallback endpoints to the common list
        self._common_properties.production_fallback_list = working_endpoints
        self._common_properties.active_phase_count = active_phase_count
        if active_phase_count != phase_count and phase_count > 1:
            _LOGGER.debug(
                "Expected Production report Phase values not available, %s of %s",
                active_phase_count,
                phase_count,
            )
        return self._supported_features

    async def update(self, envoy_data: EnvoyData) -> None:
        """Update the Envoy for this endpoint."""
        production_data = await self._json_request(self.end_point)
        envoy_data.raw[self.end_point] = production_data

        # get phase count from Envoy common features
        phase_count = self._common_properties.phase_count

        if self._supported_features & SupportedFeatures.PRODUCTION:
            envoy_data.system_production = EnvoySystemProduction.from_production(
                production_data
            )
            # get production phase data if more then 1 phase is found
            phase_production: dict[str, EnvoySystemProduction | None] = {}
            for phase in range(phase_count if phase_count > 1 else 0):
                production: EnvoySystemProduction | None = (
                    EnvoySystemProduction.from_production_phase(production_data, phase)
                )
                # exclude None phases that are expected but not actually in production report
                if production:
                    phase_production[PHASENAMES[phase]] = production

            if len(phase_production) > 0:
                envoy_data.system_production_phases = phase_production

        if (
            self._supported_features & SupportedFeatures.NET_CONSUMPTION
            or self._supported_features & SupportedFeatures.TOTAL_CONSUMPTION
        ):
            envoy_data.system_consumption = EnvoySystemConsumption.from_production(
                production_data
            )

            # get consumption phase data if more then 1 phase is found
            phase_consumption: dict[str, EnvoySystemConsumption | None] = {}
            for phase in range(phase_count if phase_count > 1 else 0):
                consumption: EnvoySystemConsumption | None = (
                    EnvoySystemConsumption.from_production_phase(production_data, phase)
                )
                # exclude None phases that are expected but not actually in production report
                if consumption:
                    phase_consumption[PHASENAMES[phase]] = consumption

            if len(phase_consumption) > 0:
                envoy_data.system_consumption_phases = phase_consumption


class EnvoyProductionJsonUpdater(EnvoyProductionUpdater):
    """Class to handle updates for production data from the production.json endpoint."""

    end_point = URL_PRODUCTION_JSON


class EnvoyProductionJsonFallbackUpdater(EnvoyProductionJsonUpdater):
    """Class to handle updates for production data from the production.json endpoint.

    This class will accept the production endpoint even if activeCount is 0
    """

    allow_inverters_fallback = True
