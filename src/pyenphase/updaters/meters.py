"""Envoy CT Meter updater"""
import logging

from ..const import ENDPOINT_URL_METERS, ENDPOINT_URL_METERS_READINGS, SupportedFeatures
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS, EnvoyAuthenticationRequired
from ..models.envoy import EnvoyData
from ..models.meters import CtMeterData, CtState, CtType, EnvoyPhaseMode
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyMetersUpdater(EnvoyUpdater):
    """Class to handle updates for Envoy CT Meters."""

    end_point = ENDPOINT_URL_METERS  #: endpoint in envoy to read CT meter configuration
    data_end_point = (
        ENDPOINT_URL_METERS_READINGS  #: endpoint in Envoy to read CT meter data
    )
    production_meter_type: CtType | None = None  #: Production CT type
    consumption_meter_type: CtType | None = None  #: Consumpion CT type (net or total)
    phase_mode: EnvoyPhaseMode | None = (
        None  #: Phase mode configured (Single, Dual or Three)
    )
    phase_count: int = 0  #: Number of phases configured and measured in the Envoy
    ct_meters_count: int = (
        0  #: Number of installed current transformers (Envoy metered Only)
    )

    def _set_common_properties(self) -> None:
        """Set Envoy common properties we own and control"""
        self._common_properties.phase_count = self.phase_count
        self._common_properties.phase_mode = self.phase_mode
        self._common_properties.consumption_meter_type = self.consumption_meter_type
        self._common_properties.ct_meter_count = self.ct_meters_count

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe the Envoy meter setup and return multiphase support in SupportedFeatures.

        Get CT configuration info from ivp/meters in the Envoy and determine any multi-phase setup.
        Set Threephase or Dualphase supported feature if Envoy is in one of these setups.
        Set common property information in envoy data for phase_count, ct_meter_count, phase_mode
        and ct_consumption_meter type to default or found values. These 4 are owned by this updater.

        :param discovered_features: Features discovered by other updaters for this updater to skip
        :return: Updated discovered features list with features discovered by this updater added
        """
        # set defaults for common properties we own and will set
        self.phase_count = 1  # Default to 1 phase which is overall numbers only
        self.ct_meters_count = (
            0  # default no CT, are pnly available on Envoy metered if configured
        )
        self.phase_mode = (
            None  # Phase mode only if ct meters are installed and configured
        )
        self.consumption_meter_type = (
            None  # Type of consumption ct only known if installed.
        )

        # set the defaults in global common properties in case we exit early
        self._set_common_properties()

        try:
            meters_json: list[CtMeterData] | None = await self._json_probe_request(
                self.end_point
            )
        except ENDPOINT_PROBE_EXCEPTIONS as e:
            _LOGGER.debug("Meters endpoint not found at %s: %s", self.end_point, e)
            return None
        except EnvoyAuthenticationRequired as e:
            # For D3.18.10 (f0855e) systems return 401 even if the user has access
            # to the endpoint so we must skip it.
            _LOGGER.debug(
                "Skipping meters endpoint as user does" " not have access to %s: %s",
                self.end_point,
                e,
            )
            return None
        else:
            if not meters_json:
                # Non metered Envoy return empty list
                _LOGGER.debug("No CT Meters found")
                return None
        # Set multiphase features so other providers/models can return phase data
        self.phase_count = 1
        for meter in meters_json:
            if meter["state"] == CtState.ENABLED:
                # remember what mode meter is installed
                if meter["measurementType"] == CtType.PRODUCTION:
                    self.production_meter_type = meter["measurementType"]
                else:
                    self.consumption_meter_type = meter["measurementType"]
                self.ct_meters_count += 1
                self.phase_mode = meter["phaseMode"]
                self.phase_count = (
                    meter["phaseCount"]
                    if meter["phaseCount"] > self.phase_count
                    else self.phase_count
                )

        # report phase configuration in envoy common property
        self._set_common_properties()

        # report DUAL or THREE PHASE feature for use by next updaters probe
        if self.phase_count > 2:
            self._supported_features |= SupportedFeatures.THREEPHASE
        elif self.phase_count > 1:
            self._supported_features |= SupportedFeatures.DUALPHASE

        return self._supported_features

    async def update(self, envoy_data: EnvoyData) -> None:
        """Update the Envoy for the meters endpoints."""
        # endpoints ENDPOINT_URL_METERS and ENDPOINT_URL_METERS_READINGS deliver raw CT data
        # these are not required for multiphase data from production, just the probe is
        # ENDPOINT_URL_METERS_READINGS delivers net consumption and net production
        # from grid (energy_delivered) and to grid (energy_received) if ct type is net-consumpton
        # stub is here as update() is required, ready for use in future expansion in other PR
