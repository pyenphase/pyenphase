import logging
from typing import Any

from ..const import URL_DEVICE_DATA, SupportedFeatures
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS, EnvoyAuthenticationRequired
from ..models.envoy import EnvoyData
from ..models.inverter import EnvoyInverter
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)

RESIGNAL_INTERVAL = 60


class EnvoyDeviceDataInvertersUpdater(EnvoyUpdater):
    """Class to handle updates for inverter device data."""

    probed_inverters: set[str]
    verified_inverters: set[str]
    resignal: int

    def _filter_inverters(self, inverters_data: dict[str, Any]) -> dict[str, Any]:
        """Filter and return only PCU inverter devices."""
        return {
            inverter["sn"]: inverter
            for _id, inverter in inverters_data.items()
            if isinstance(inverter, dict)
            and inverter.get("devName") == "pcu"
            and inverter.get("active")
            and "sn" in inverter
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
                    "as deviceCount reached deviceDataLimit %s: %s - %s",
                    URL_DEVICE_DATA,
                    inverters_data["deviceCount"],
                    inverters_data["deviceDataLimit"],
                )
                return None
        except (KeyError, TypeError) as e:
            # if doesn't have these keys, fall back to inverter production
            _LOGGER.debug(
                "Disabling inverters device data endpoint "
                "as not all data fields are present %s: %s",
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

        except (KeyError, IndexError) as e:
            # if any inverter returned None there's something messed by json format, fall back to production
            _LOGGER.debug(
                "Disabling inverters device data endpoint "
                "as keys are missing or format issues %s: %s",
                URL_DEVICE_DATA,
                e,
            )
            return None

        except (TypeError, AttributeError, ValueError) as e:
            # if any inverter returned messed json format, fall back to production
            _LOGGER.warning(
                "Disabling inverters device data endpoint "
                "because of data format issues %s: %s",
                URL_DEVICE_DATA,
                e,
            )
            return None

        # remember number of inverters found
        self.probed_inverters = set(inverters)
        self.verified_inverters = set(inverters)
        self.resignal = 0

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
        required fields of sn, watts now, watts max and lastReading endDate
        """
        inverters_data: dict[str, Any] = await self._json_request(URL_DEVICE_DATA)
        envoy_data.raw[URL_DEVICE_DATA] = inverters_data
        inverters: dict[str, EnvoyInverter] = {}
        # filter active pcu from devices.
        failed_inverters: bool = False
        filtered_inverters: dict[str, Any] = {}
        try:
            filtered_inverters = self._filter_inverters(inverters_data)
        except (KeyError, IndexError, TypeError, AttributeError) as e:
            # some devices may have no sn, devName or active keys
            # they had it at probe, don't try finding what is
            # going on, something is really messed up.
            failed_inverters = True
            _LOGGER.debug("Inverter data extraction failed: %r", e)

        # process found inverter devices, if any
        if not failed_inverters and filtered_inverters:
            for sn, inverter in filtered_inverters.items():
                try:
                    inverters[sn] = EnvoyInverter.from_device_data(inverter)
                except (  # noqa: PERF203
                    KeyError,
                    IndexError,
                    TypeError,
                    AttributeError,
                    ValueError,
                ) as e:
                    _LOGGER.debug("Missing datafields for inverter %s: %r", sn, e)

        # we now have all data we can get from data.
        # keep track of missed and refound inverters
        # warn and rewarn on issues
        # keep warnings simple, tell them to enable debug to check

        current_set = set(inverters)

        # report original list changes
        if current_set != self.probed_inverters:
            _LOGGER.debug(
                "Inverter list changed from Probe, added: %s , removed: %s (%s)",
                ", ".join(sorted(current_set - self.probed_inverters)),
                ", ".join(sorted(self.probed_inverters - current_set)),
                self.resignal,
            )
            # Add new inverters to probed set
            self.probed_inverters.update(current_set - self.probed_inverters)

        # if current set still differs from probed let resignal run
        if current_set != self.probed_inverters:
            self.resignal += 1
        else:
            self.resignal = 0

        # If current set is is not equal to verified set we have changes in found inverters
        # verified_inverters set started from probed_inverters
        if current_set != self.verified_inverters:
            _LOGGER.debug(
                "Inverter list changed, added: %s , removed: %s",
                ", ".join(sorted(current_set - self.verified_inverters)),
                ", ".join(sorted(self.verified_inverters - current_set)),
            )
            # force resignal on lost inverters
            if self.verified_inverters - current_set:
                self.resignal = RESIGNAL_INTERVAL + 1
            self.verified_inverters = current_set

        # signal or resignal warning something is wrong and user should look at debug
        if self.resignal >= RESIGNAL_INTERVAL:
            _LOGGER.warning(
                "Inverter device data issues found, missing from probe: %s.",
                ", ".join(sorted(self.probed_inverters - current_set)),
            )
            self.resignal = 0

        envoy_data.inverters = inverters
