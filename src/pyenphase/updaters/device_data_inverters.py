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

    inverter_count: int = 0

    def _filter_inverters(self, inverters_data: dict[str, Any]) -> dict[str, Any]:
        """Filter and return only PCU inverter devices."""
        return {
            inverter["sn"]: inverter
            for id, inverter in inverters_data.items()
            if id not in ("deviceCount", "deviceDataLimit")
            and inverter["devName"] == "pcu"
            and inverter["active"]
        }

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
        # make sure deviceCount did not reach deviceDataLimit,
        # if more inverters are actually installed they will not be included
        # if so fall back to inverter production page
        try:
            if inverters_data["deviceCount"] >= inverters_data["deviceDataLimit"]:
                _LOGGER.debug(
                    "Disabling inverters device data endpoint "
                    " as deviceCount reached  deviceDataLimit %s: %s - %s",
                    URL_DEVICE_DATA,
                    inverters_data["deviceCount"],
                    inverters_data["deviceDataLimit"],
                )
                return None
        except KeyError as e:
            # if doesn't have these keys, fall back to inverter production
            _LOGGER.debug(
                "Disabling inverters device data endpoint "
                " as not all data fields are present %s: %s",
                URL_DEVICE_DATA,
                e,
            )
            return None

        # verify minimal data set to replace inverter production data is present
        try:
            filtered_inverters = self._filter_inverters(inverters_data)
            if not filtered_inverters:
                _LOGGER.debug(
                    "Disabling inverters device data endpoint "
                    "as no active PCU devices were found %s",
                    URL_DEVICE_DATA,
                )
                return None
            inverters = {
                sn: EnvoyInverter.from_device_data(inverter)
                for sn, inverter in filtered_inverters.items()
            }
            # remember number of inverters found
            self.inverter_count = len(inverters)

        except (KeyError, IndexError) as e:
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
        """
        Update the Envoy for this updater.

        If we're here then probe confirmed to use device_data.
        We don't want to raise on Key or Index errors and break
        overall update. Instead skip any invalid formatted inverter
        (pcu) data and only return data for inverters with the minimum
        required fields of sn, watts now, watts max and lastReported endData
        """
        inverters_data: dict[str, Any] = await self._json_request(URL_DEVICE_DATA)
        envoy_data.raw[URL_DEVICE_DATA] = inverters_data
        inverters: dict[str, EnvoyInverter] = {}
        for id, device in inverters_data.items():
            # we need to catch KeyErrors returned by _filter_inverters
            # for an individual inverter and continue with next one.
            # Let _filter_inverters process one device at the time.
            try:
                filtered_inverters = self._filter_inverters({id: device})
            except (KeyError, IndexError) as e:
                _LOGGER.debug(
                    "Skipping inverter device %s this cycle: incomplete device data (%s)",
                    id,
                    e,
                )
                continue
            # this will have 1 inverters at best if device was pcu
            for sn, inverter in filtered_inverters.items():
                try:
                    inverters[sn] = EnvoyInverter.from_device_data(inverter)
                    # keep track of found inverters
                except (KeyError, IndexError) as e:  # noqa: PERF203
                    _LOGGER.debug(
                        "Skipping inverter %s this cycle: incomplete device data (%s)",
                        sn,
                        e,
                    )

        present_count = len(inverters)
        # issue one time warning if no data at all is valid
        if present_count == 0 and self.inverter_count > 0:
            self.warning_issued = True
            _LOGGER.warning(
                "All inverters have incomplete device data, no data reported. (Further warnings suppressed until inverter data is restored)",
            )
        # issue warning if number drops
        elif present_count < self.inverter_count:
            _LOGGER.warning(
                "Number of fully reported inverters in device data dropped from %s to %s.",
                self.inverter_count,
                present_count,
            )
        # debug log on restored count
        elif present_count > self.inverter_count:
            _LOGGER.debug(
                "Number of fully reported inverters in device data increased from %s to %s.",
                self.inverter_count,
                present_count,
            )
        # remember current count
        self.inverter_count = present_count

        envoy_data.inverters = inverters
