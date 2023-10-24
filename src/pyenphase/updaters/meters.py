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

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe the Envoy meter setup and return multiphase support in SupportedFeatures."""
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
        # Set multiphase features so other providers/models can return phase data
        # can't get to envoy from here to store a phase_count so use DUAL and THREEPHASE features
        phase_count: int = 1
        for meter in meters_json:
            phase_count = (
                meter["phaseCount"]
                if meter["state"] == "enabled" and meter["phaseCount"] > phase_count
                else phase_count
            )

        if phase_count > 2:
            self._supported_features |= SupportedFeatures.THREEPHASE
        elif phase_count > 1:
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
