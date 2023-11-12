import logging
from typing import Any

from ..const import ENDPOINT_URL_METERS, ENDPOINT_URL_METERS_READINGS, SupportedFeatures
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS
from ..models.envoy import EnvoyData
from ..models.meters import (
    EnvoyMeterKeys,
    EnvoyMeterState,
    EnvoyMeterType,
    EnvoyPhaseMode,
)
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyMetersUpdater(EnvoyUpdater):
    """Class to handle updates for Envoy CT Meters."""

    end_point = ENDPOINT_URL_METERS
    data_end_point = ENDPOINT_URL_METERS_READINGS
    production_meter_eid = None
    consumption_meter_eid = None
    production_meter_type: EnvoyMeterType | None = None
    consumption_meter_type: EnvoyMeterType | None = None
    phase_mode: EnvoyPhaseMode | None = None
    phase_count = 1
    ct_Meters_count = 0

    def _set_my_common_properties(self) -> None:
        """Set common properties we own and control"""
        self._common_properties.phase_count = self.phase_count
        self._common_properties.phase_mode = self.phase_mode
        self._common_properties.consumption_meter_type = self.consumption_meter_type
        self._common_properties.ct_meter_count = self.ct_Meters_count

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe the Envoy meter setup and return multiphase support in SupportedFeatures."""
        # set defaults for common properties we will set
        self.phase_count = 1
        self.ct_meter_count = 0
        self.phase_mode = None
        self.consumption_meter_type = None

        # set the defaults in global common properties in case we exit early
        self._set_my_common_properties()

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
            if meter[EnvoyMeterKeys.TYPE] in [
                EnvoyMeterType.NETCONSUMPTION,
                EnvoyMeterType.TOTALCONSUMPTION,
            ]:
                # store eid (even if disabled) for use in update
                self.consumption_meter_eid = meter[EnvoyMeterKeys.EID]
                # remember what mode consumption meter is installed in, if enabled
                if meter[EnvoyMeterKeys.STATE] == EnvoyMeterState.ENABLED:
                    self.consumption_meter_type = meter[EnvoyMeterKeys.TYPE]
            else:
                # store eid (even if disabled) for use in update
                self.production_meter_eid = meter[EnvoyMeterKeys.EID]
                # remember what mode production meter is installed in, if enabled
                if meter[EnvoyMeterKeys.STATE] == EnvoyMeterState.ENABLED:
                    self.production_meter_type = meter[EnvoyMeterKeys.TYPE]

            # if meter is enabled add to found meters and set phase count
            if meter[EnvoyMeterKeys.STATE] == EnvoyMeterState.ENABLED:
                self.ct_Meters_count += 1
                self.phase_count = (
                    meter[EnvoyMeterKeys.PHASECOUNT]
                    if meter[EnvoyMeterKeys.PHASECOUNT] > self.phase_count
                    and meter[EnvoyMeterKeys.PHASEMODE] != EnvoyPhaseMode.SPLIT
                    else self.phase_count
                )
                self.phase_mode = meter[EnvoyMeterKeys.PHASEMODE]

        # report phaseCount and found CT Meters as envoy common property
        self._set_my_common_properties()

        # report DUAL or THREE PHASE feature for use by next updaters probe
        if self.phase_count > 2:
            self._supported_features |= SupportedFeatures.THREEPHASE
        elif self.phase_mode == EnvoyPhaseMode.SPLIT:
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
