"""Envoy production data updater"""

import logging
from typing import Any

from ..const import (
    PHASENAMES,
    PRODUCTION_TOTAL_IS_NET_CONSUMPTION,
    URL_PRODUCTION,
    URL_PRODUCTION_JSON,
    SupportedFeatures,
)
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS, EnvoyAuthenticationRequired
from ..models.acb import EnvoyACBPower
from ..models.envoy import EnvoyData
from ..models.meters import CtType
from ..models.system_consumption import EnvoySystemConsumption
from ..models.system_production import EnvoySystemProduction
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


def get_active_phase_count(lines: list[dict[str, Any]]) -> int:
    """Determine how many phases are active."""
    # recent firmware version return always 3 phases with
    # inactive phase data all zero. Which results in wrong
    # value when using len(lines). Correct for all zero data
    return sum(1 for line in lines if any(line.values()))


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

        # check if prior updaters reported supporting ACB
        discovered_acb_storage = SupportedFeatures.ACB in discovered_features

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
            # to the endpoint. For URL_PRODUCTION_JSON some early non-metered V7 versions
            # return 401 when using aiohttp. Non-metered fallback to v1 production anyway.
            # if there's really no-auth the v1/production will catch it.
            if self.end_point in (URL_PRODUCTION, URL_PRODUCTION_JSON):
                _LOGGER.debug(
                    "Skipping production endpoint as user does"
                    " not have access to %s: %s",
                    self.end_point,
                    e,
                )
                return None
            _LOGGER.debug(  # pragma: no cover
                "Authentication required for %s, re-raising exception: %s",
                self.end_point,
                e,
            )
            raise  # pragma: no cover

        active_phase_count = 0
        phase_count = self._common_properties.phase_count

        # As of fw 5.3.5528 (and maybe earlier) metered envoy with CT intermittently
        # report bogus data in /production type=eim, recognizable by activeCount: 0
        # For metered Envoy with active CT, do NOT fallback to any of the
        #   EnvoyProductionUpdater
        #   EnvoyApiV1ProductionUpdater
        #   EnvoyProductionJsonFallbackUpdater
        # updaters, these report different values as the production segment.
        # Instead register this updater for production.
        has_production_ct = CtType.PRODUCTION in self._common_properties.meter_types

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
                    # fw 5.3.5528, if metered with CT do not fall back to other production updaters
                    if type_["type"] == "eim" and (
                        type_["activeCount"] or has_production_ct
                    ):
                        self._supported_features |= SupportedFeatures.METERING
                        self._supported_features |= SupportedFeatures.PRODUCTION
                        if lines := type_.get("lines"):
                            active_phase_count = max(
                                active_phase_count, get_active_phase_count(lines)
                            )
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
                # first test activecount >0 before trying measurementType
                if not meter.get("activeCount"):
                    continue
                meter_type = meter["measurementType"]
                if (
                    not discovered_total_consumption
                    and meter_type == "total-consumption"
                ):
                    self._supported_features |= SupportedFeatures.TOTAL_CONSUMPTION
                if not discovered_net_consumption and meter_type == "net-consumption":
                    self._supported_features |= SupportedFeatures.NET_CONSUMPTION
                if lines := meter.get("lines"):
                    active_phase_count = max(
                        active_phase_count, get_active_phase_count(lines)
                    )

        acb_storage: list[dict[str, Any]] | None = production_json.get("storage")
        # if storage segment is present and activeCount > 0 then signal as detected
        # verify presence of percentFull key to confirm a well configured envoy
        # we've seen activeCount > 0 without percentFull key, ignore ACB in that case
        # only report we support ACB if no prior updater did
        # only report first list element as that's where ACB data is
        if (
            acb_storage
            and not discovered_acb_storage
            and (acb_count := acb_storage[0].get("activeCount"))
            and "percentFull" in acb_storage[0]
        ):
            # signal we can provide ACB data
            self._supported_features |= SupportedFeatures.ACB
            # save acb batt count in common properties so Ensemble can report combined soc
            self._common_properties.acb_batteries_reported = acb_count

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
            # fw 5.3.5528, signal we have active CT
            has_production_ct = CtType.PRODUCTION in self._common_properties.meter_types
            envoy_data.system_production = EnvoySystemProduction.from_production(
                production_data,
                has_production_ct,
            )
            # get production phase data if more then 1 phase is found
            phase_production: dict[str, EnvoySystemProduction | None] = {}
            for phase in range(phase_count if phase_count > 1 else 0):
                production: EnvoySystemProduction | None = (
                    EnvoySystemProduction.from_production_phase(
                        production_data,
                        phase,
                        has_production_ct,
                    )
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
            envoy_data.system_net_consumption = EnvoySystemConsumption.from_production(
                production_data, consumption_segment=1
            )

            # get consumption phase data if more then 1 phase is found
            phase_consumption: dict[str, EnvoySystemConsumption | None] = {}
            phase_net_consumption: dict[str, EnvoySystemConsumption | None] = {}
            for phase in range(phase_count if phase_count > 1 else 0):
                consumption: EnvoySystemConsumption | None = (
                    EnvoySystemConsumption.from_production_phase(production_data, phase)
                )
                # exclude None phases that are expected but not actually in production report
                if consumption:
                    phase_consumption[PHASENAMES[phase]] = consumption

                if net_consumption := (
                    EnvoySystemConsumption.from_production_phase(
                        production_data, phase, consumption_segment=1
                    )
                ):
                    phase_net_consumption[PHASENAMES[phase]] = net_consumption

            if len(phase_consumption) > 0:
                envoy_data.system_consumption_phases = phase_consumption

            if len(phase_net_consumption) > 0:
                envoy_data.system_net_consumption_phases = phase_net_consumption

        if self._supported_features & SupportedFeatures.ACB:
            envoy_data.acb_power = EnvoyACBPower.from_production(production_data)

        # starting with fw 8.3.5433 total-consumption whLifetime and wNow are overwritten
        # by net-consumption values for metered envoy (with assumed) TOTAL-CONSUMPTION
        # CT installed. Repair by calculating TOTAL-CONSUMPTION as
        # NET-CONSUMPTION + PRODUCTION values.
        if (
            self._envoy_version >= PRODUCTION_TOTAL_IS_NET_CONSUMPTION
            and SupportedFeatures.METERING in self._supported_features
            and envoy_data.system_consumption is not None
            and envoy_data.system_net_consumption is not None
            and (
                envoy_data.system_consumption.watt_hours_lifetime
                == envoy_data.system_net_consumption.watt_hours_lifetime
            )
            and (
                envoy_data.system_consumption.watts_now
                == envoy_data.system_net_consumption.watts_now
            )
        ):
            if envoy_data.system_production is None:
                # as of 8.3.5528 envoy may return intermittently activeCount=0 in
                # production eim segment, this will result in system_production becoming None
                # this will prevent fixing the 8.3.5433 total-consumption = net-consumption
                # repair as eim production report is rejected; total-consumption cannot be repaired,
                # do not publish raw net-consumption values as total-consumption
                _LOGGER.debug(
                    "No reliable production data found, cannot correct consumption data, returning None."
                )
                envoy_data.system_consumption = None
                envoy_data.system_consumption_phases = None
            else:
                # Add production to net-consumption to get total-consumption
                # we're only here if net = tot consumption so we can use either
                envoy_data.system_consumption.watt_hours_lifetime += (
                    envoy_data.system_production.watt_hours_lifetime
                )
                envoy_data.system_consumption.watts_now += (
                    envoy_data.system_production.watts_now
                )

                # correct phases as well
                if (
                    phase_count > 1
                    and (sys_prod := envoy_data.system_production_phases) is not None
                    and (sys_cons := envoy_data.system_consumption_phases) is not None
                    and (sys_net_cons := envoy_data.system_net_consumption_phases)
                    is not None
                ):
                    for phase_name in set(sys_prod) & set(sys_cons) & set(sys_net_cons):
                        if (
                            (cons := sys_cons[phase_name]) is not None
                            and (net_cons := sys_net_cons[phase_name]) is not None
                            and (prod := sys_prod[phase_name]) is not None
                            and (
                                cons.watt_hours_lifetime == net_cons.watt_hours_lifetime
                            )
                            and (cons.watts_now == net_cons.watts_now)
                        ):
                            # Add production to net-consumption to get total-consumption
                            cons.watt_hours_lifetime += prod.watt_hours_lifetime
                            cons.watts_now += prod.watts_now


class EnvoyProductionJsonUpdater(EnvoyProductionUpdater):
    """Class to handle updates for production data from the production.json endpoint."""

    end_point = URL_PRODUCTION_JSON


class EnvoyProductionJsonFallbackUpdater(EnvoyProductionJsonUpdater):
    """
    Class to handle updates for production data from the production.json endpoint.

    This class will accept the production endpoint even if activeCount is 0
    """

    allow_inverters_fallback = True
