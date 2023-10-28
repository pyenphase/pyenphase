import logging
from typing import Any

from ..const import ENDPOINT_URL_METERS, ENDPOINT_URL_METERS_READINGS, SupportedFeatures
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS
from ..models.envoy import EnvoyData
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyMetersUpdater(EnvoyUpdater):
    """Class to handle updates for Envoy CT Meters."""

    end_point = ENDPOINT_URL_METERS
    data_end_point = ENDPOINT_URL_METERS_READINGS
    production_meter_eid = None
    consumption_meter_eid = None
    production_meter_type = None
    consumption_meter_type = None
    phase_mode = None
    phase_count = 1
    ct_Meters_count = 0

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe the Envoy meter setup and return multiphase support in SupportedFeatures."""
        # set defaults for common properties we will set, so these always have a value
        await self._add_common_property("ctMeters", self.ct_Meters_count)
        await self._add_common_property("phaseCount", self.phase_count)
        await self._add_common_property("phaseMode", self.phase_mode)
        await self._add_common_property("consumptionMeter", self.consumption_meter_type)

        try:
            meters_json: list[dict[str, Any]] | None = await self._json_probe_request(
                self.end_point
            )
        except ENDPOINT_PROBE_EXCEPTIONS as e:
            _LOGGER.debug("Meters endpoint not found at %s: %s", self.end_point, e)
            return None
        else:
            if not meters_json or "error" in meters_json:
                # Non metered Envoy return empty list
                _LOGGER.debug("No CT Meters found")
                return None

        # Store CT meter settings for use by updater
        for meter in meters_json:
            # remember eid to match readings in update
            if meter["measurementType"] in ["net-consumption", "total-consumption"]:
                self.consumption_meter_eid = meter["eid"]
                # remember what mode consumption meter is installed in, if any
                if meter["state"] == "enabled":
                    self.consumption_meter_type = meter["measurementType"]
            else:
                self.production_meter_eid = meter["eid"]
                # remember what mode production meter is installed in, if any
                if meter["state"] == "enabled":
                    self.production_meter_type = meter["measurementType"]

            # if meter is enabled add to found meters and set phase count
            if meter["state"] == "enabled":
                self.ct_Meters_count += 1
                self.phase_count = (
                    meter["phaseCount"]
                    if meter["phaseCount"] > self.phase_count
                    and meter["phaseMode"] != "split"
                    else self.phase_count
                )
                self.phase_mode = meter["phaseMode"]

        # report phaseCount and found CT Meters as envoy common property
        await self._add_common_property("phaseCount", self.phase_count)
        await self._add_common_property("ctMeters", self.ct_Meters_count)
        await self._add_common_property("phaseMode", self.phase_mode)
        await self._add_common_property("consumptionMeter", self.consumption_meter_type)

        # report DUAL or THREE PHASE feature for use by next updaters probe
        if self.phase_count > 2:
            self._supported_features |= SupportedFeatures.THREEPHASE
        elif self.phase_mode == "split":
            self._supported_features |= SupportedFeatures.DUALPHASE

        return self._supported_features

    async def update(self, envoy_data: EnvoyData) -> None:
        """Update the Envoy for the meters endpoints."""
        # endpoints ENDPOINT_URL_METERS and ENDPOINT_URL_METERS_READINGS deliver raw CT data
        # these are not required for multiphase data from production, just the probe is
        # ENDPOINT_URL_METERS_READINGS delivers net consumption and net production
        # from grid (energy_delivered) and to grid (energy_received) if ct type is net-consumpton
        # stub is here as update() is required, ready for use in future expansion in other PR
        pass
