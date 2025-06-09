import logging
from typing import Any

from ..const import URL_DEVICE_DATA, SupportedFeatures
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS, EnvoyAuthenticationRequired
from ..models.envoy import EnvoyData
from ..models.inverter import EnvoyInverter
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyDeviceDataInvertersUpdater(EnvoyUpdater):
    """Class to handle updates for inverter device data."""

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe the Envoy for this updater and return SupportedFeatures."""
        if SupportedFeatures.INVERTERS in discovered_features:
            # Already discovered from another updater
            return None

        try:
            inverters_data = await self._json_probe_request(URL_DEVICE_DATA)
        except ENDPOINT_PROBE_EXCEPTIONS as e:
            _LOGGER.debug(
                "Device data endpoint not found at %s: %s", URL_DEVICE_DATA, e
            )
            return None
        except EnvoyAuthenticationRequired as e:
            _LOGGER.debug(
                "Disabling inverters device data endpoint as user does"
                " not have access to %s: %s",
                URL_DEVICE_DATA,
                e,
            )
            return None

        # verify minimal data set to replace inverter production data is present
        try:
            _ = {
                inverter["sn"]: EnvoyInverter.from_device_data(inverter)
                for id, inverter in inverters_data.items()
                if id not in ("deviceCount", "deviceDataLimit")
                and inverter["devName"] == "pcu"
            }
        except KeyError as e:
            # if any inverter returned None there's something messed by json format, fall back to production
            _LOGGER.debug(
                "Disabling inverters device data endpoint "
                " as not all data fields are present %s: %s",
                URL_DEVICE_DATA,
                e,
            )
            return None

        self._supported_features |= (
            SupportedFeatures.INVERTERS | SupportedFeatures.DETAILED_INVERTERS
        )
        return self._supported_features

    async def update(self, envoy_data: EnvoyData) -> None:
        """Update the Envoy for this updater."""
        inverters_data: dict[str, Any] = await self._json_request(URL_DEVICE_DATA)
        envoy_data.raw[URL_DEVICE_DATA] = inverters_data
        envoy_data.inverters = {
            inverter["sn"]: EnvoyInverter.from_device_data(inverter)
            for id, inverter in inverters_data.items()
            if id not in ("deviceCount", "deviceDataLimit")
            and inverter["devName"] == "pcu"
        }
