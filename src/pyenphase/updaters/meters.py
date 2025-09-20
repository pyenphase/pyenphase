"""Envoy CT Meter updater"""

import logging
from typing import Any

from ..const import (
    ENDPOINT_URL_METERS,
    ENDPOINT_URL_METERS_READINGS,
    PHASENAMES,
    SupportedFeatures,
)
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS, EnvoyAuthenticationRequired
from ..models.envoy import EnvoyData
from ..models.meters import CtMeterData, CtState, CtType, EnvoyMeterData, EnvoyPhaseMode
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyMetersUpdater(EnvoyUpdater):
    """Class to handle updates for Envoy CT Meters."""

    end_point = ENDPOINT_URL_METERS  #: endpoint in envoy to read CT meter configuration
    data_end_point = (
        ENDPOINT_URL_METERS_READINGS  #: endpoint in Envoy to read CT meter data
    )
    meter_types: list[str]  #: CT types found
    phase_mode: EnvoyPhaseMode | None = (
        None  #: Phase mode configured (Single, Dual or Three)
    )
    phase_count: int = 0  #: Number of phases configured and measured in the Envoy
    ct_meters_count: int = (
        0  #: Number of installed current transformers (Envoy metered Only)
    )
    meter_eids: dict[str, str]  #: CT identifiers

    def _set_common_properties(self) -> None:
        """Set Envoy common properties we own and control"""
        self._common_properties.phase_count = self.phase_count
        self._common_properties.phase_mode = self.phase_mode
        self._common_properties.meter_types = self.meter_types
        self._common_properties.ct_meter_count = self.ct_meters_count

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """
        Probe the Envoy meter setup and return CT and multiphase details in SupportedFeatures.

        Get CT configuration info from ivp/meters in the Envoy and determine any multi-phase setup.
        Set :any:SupportedFeatures.CTMETERS if CT are found and enabled.
        Set Threephase or Dualphase supported feature if Envoy is in one of these setups.

        Set common properties (phase_count, ct_meter_count, phase_mode, meter_types)
        to default or discovered values. These are owned by this updater.

        :param discovered_features: Features discovered by other updaters for this updater to skip
        :return: features discovered by this updater
        """
        if SupportedFeatures.CTMETERS in discovered_features:
            # Already discovered from another updater
            return None

        # set defaults for common properties we own and will set
        self.phase_count = 1  # Default to 1 phase which is overall numbers only
        self.ct_meters_count = (
            0  # default no CT, are only available on Envoy metered if configured
        )
        self.phase_mode = (
            None  # Phase mode only if ct meters are installed and configured
        )
        # track found ct meter measurement types
        self.meter_types = []

        # set the defaults in global common properties in case we exit early
        self._set_common_properties()

        # set local defaults not shared in common properties
        self.meter_eids = {}

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
                "Skipping meters endpoint as user does not have access to %s: %s",
                self.end_point,
                e,
            )
            return None
        else:
            # The endpoint can return valid json on error
            # in the form of {"error": "message"}
            if not meters_json or "error" in meters_json:
                # Non metered Envoy return empty list
                _LOGGER.debug("No CT Meters found")
                return None
        # Set multiphase features so other providers/models can return phase data
        self.phase_count = 1
        for meter in meters_json:
            if meter["state"] == CtState.ENABLED:
                # remember what meter is installed
                self.meter_types.append(meter_type := meter["measurementType"])
                # save meter identifier for link between /ivp/meters and /ivp/meters/readings
                self.meter_eids[meter["eid"]] = meter_type

                self.ct_meters_count += 1
                self.phase_mode = meter["phaseMode"]
                self.phase_count = max(self.phase_count, meter["phaseCount"])

        # report phase configuration in envoy common property
        self._set_common_properties()

        # report DUAL or THREE PHASE feature for use by next updaters probe
        if self.phase_count > 2:
            self._supported_features |= SupportedFeatures.THREEPHASE
        elif self.phase_count > 1:
            self._supported_features |= SupportedFeatures.DUALPHASE

        # Signal CTMETERS feature back so update will get used if we found ctmeters
        if self.ct_meters_count > 0:
            self._supported_features |= SupportedFeatures.CTMETERS

        return self._supported_features

    async def update(self, envoy_data: EnvoyData) -> None:
        """
        Update the Envoy data from the meters endpoints.

        Get CT configuration from ivp/meters and CT readings from ivp/meters/readings.
        Store data as EnvoyMeterData in ctmeters if any meter is found enabled during probe.
        If more then 1 phase is active, store phase data in ctmeters_phases. Match data
        in ivp/meters and ivp/meters/reading using the eid field in both datasets.

        For backward compatibility ctmeter_production, ctmeter_consumption and ct_meter_storage
        are still se and point to their entries in ctmeters[CtType].

        :param envoy_data: EnvoyData structure to store data to
        """
        # get the meter status and readings from the envoy
        meters_status: list[CtMeterData] = await self._json_request(self.end_point)
        meters_readings: list[dict[str, Any]] = await self._json_request(
            self.data_end_point
        )

        envoy_data.raw[self.end_point] = meters_status
        envoy_data.raw[self.data_end_point] = meters_readings

        phase_range = self.phase_count if self.phase_count > 1 else 0

        # no longer assume 2 lists are the same order and size. Size differs in fw 8.3.5025
        status_by_eid = {ct["eid"]: ct for ct in meters_status}
        for meter in meters_readings:
            eid = meter["eid"]

            if not (ct_status := status_by_eid.get(eid)):
                # fw 8.3.5025 also has a 3rd entry for storage ct even if not configured
                # and it has all zeros values. Ignore data if eid not in meter status
                continue

            # match meter identifier to one found during probe to identify production or consumption
            if eid in self.meter_eids:
                # if meter was enabled (eid known) store ctmeter data
                envoy_data.ctmeters[meter_type := self.meter_eids[eid]] = (
                    EnvoyMeterData.from_api(meter, ct_status)
                )
                # if more then 1 phase configured store ctmeter phase data
                if phase_data := _meter_data_for_phases(phase_range, meter, ct_status):
                    envoy_data.ctmeters_phases[meter_type] = phase_data

                # Next part if for backward compatibility
                # May plan to remove in some future breaking change version
                if meter_type == CtType.PRODUCTION:
                    envoy_data.ctmeter_production = envoy_data.ctmeters[meter_type]
                    if phase_data:
                        envoy_data.ctmeter_production_phases = (
                            envoy_data.ctmeters_phases[meter_type]
                        )
                elif meter_type in (
                    CtType.NET_CONSUMPTION,
                    CtType.TOTAL_CONSUMPTION,
                ):
                    envoy_data.ctmeter_consumption = envoy_data.ctmeters[meter_type]
                    if phase_data:
                        envoy_data.ctmeter_consumption_phases = (
                            envoy_data.ctmeters_phases[meter_type]
                        )
                elif meter_type == CtType.STORAGE:
                    envoy_data.ctmeter_storage = envoy_data.ctmeters[meter_type]
                    if phase_data:
                        envoy_data.ctmeter_storage_phases = envoy_data.ctmeters_phases[
                            meter_type
                        ]
                # End of backward compatibility


def _meter_data_for_phases(
    phase_range: int, meter: dict[str, Any], ct_data: CtMeterData
) -> dict[str, EnvoyMeterData]:
    """Build a dictionary of phase data for multi-phase setups."""
    meter_data_by_phase: dict[str, EnvoyMeterData] = {
        PHASENAMES[phase_idx]: data
        for phase_idx in range(phase_range)
        if (data := EnvoyMeterData.from_phase(meter, ct_data, phase_idx))
    }
    return meter_data_by_phase
