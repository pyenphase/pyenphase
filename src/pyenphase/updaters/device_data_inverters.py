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

    all_bad: bool = False
    verified_inverters: set[str]
    skipped_inverters: set[str]
    resignal: int

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

        except (KeyError, IndexError, TypeError) as e:
            # if any inverter returned None there's something messed by json format, fall back to production
            _LOGGER.debug(
                "Disabling inverters device data endpoint "
                " as not all data fields are present %s: %s",
                URL_DEVICE_DATA,
                e,
            )
            return None

        # remember number of inverters found and init skipped tracking list
        self.verified_inverters = set(inverters)
        self.skipped_inverters = set()
        self.all_bad = False
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
        try:
            filtered_inverters = self._filter_inverters(inverters_data)
        except (KeyError, IndexError, TypeError) as e:
            # some devices have no sn, devName or active keys
            # they had it at probe, don't try finding what is
            # going on, something is really messed up.
            # issue warning on first occasion
            if not self.all_bad:
                _LOGGER.warning(
                    "Invalid device data detected: %s, skipping inverter data extraction",
                    e,
                )
                self.all_bad = True
                # reset warning resignal counter on each warning issued
                self.resignal = 0
            else:
                self.resignal += 1
                if self.resignal > RESIGNAL_INTERVAL:
                    self.resignal = 0
                    _LOGGER.warning(
                        "Invalid device data detected: %s, skipping inverter data extraction",
                        e,
                    )
                else:
                    _LOGGER.debug(
                        "Repeated invalid device data detected: %s, skipping inverter data extraction (%s)",
                        e,
                        self.resignal,
                    )

            envoy_data.inverters = {}
            return

        # if no inverter found warn or debug log
        if not filtered_inverters:
            if self.verified_inverters:
                _LOGGER.warning(
                    "No active inverter devices detected, skipping %s",
                    ", ".join(sorted(self.verified_inverters)),
                )
                self.verified_inverters = set()
                # reset warning resignal counter on each warning issued
                self.resignal = 0
            else:
                _LOGGER.debug("No active inverter devices detected repeat")
            envoy_data.inverters = {}
            return

        # Filter inverter returned data again, clear all bad
        self.all_bad = False

        # We now have all active inverters filtered
        # if inverters change between active True and False
        # we assume its the result of a user action in
        # the Envoy and don't report.
        # Get inverter data from device data
        # we know that lastReading section may be empty
        # and we exclude these from reported inverter data.
        skipped: set[str] = set()
        for sn, inverter in filtered_inverters.items():
            try:
                inverters[sn] = EnvoyInverter.from_device_data(inverter)
            except (KeyError, IndexError, TypeError) as e:  # noqa: PERF203
                _LOGGER.debug("Skipping inverter %s, incomplete data: %r", sn, e)
                skipped.add(sn)

        # any inverters that disappeared
        missing = self.verified_inverters - set(filtered_inverters)
        if len(missing) > 0:
            _LOGGER.warning(
                "Envoy did not provide previously reported inverters, no data reported for: %s",
                ", ".join(sorted(missing)),
            )
            # remove from verified inverters so they report when coming back
            self.verified_inverters = {
                sn for sn in self.verified_inverters if sn not in missing
            }
            # add to skipped
            self.skipped_inverters.update(missing)
            # reset warning resignal counter on each warning issued
            self.resignal = 0

        # warn for new found incomplete device data once
        add_to_skipped = skipped - self.skipped_inverters
        if len(add_to_skipped) > 0:
            _LOGGER.warning(
                "Envoy returned incomplete inverter data, no data reported for: %s",
                ", ".join(sorted(add_to_skipped)),
            )
            # add new skipped inverters to skipped list
            self.skipped_inverters.update(add_to_skipped)
            # reset warning resignal counter on each warning issued
            self.resignal = 0

        # remove skipped inverters from verified list
        remove_from_verified_inverters = skipped & self.verified_inverters
        if remove_from_verified_inverters:
            _LOGGER.debug(
                "Removing %s from verified inverters list",
                ", ".join(sorted(remove_from_verified_inverters)),
            )
            self.verified_inverters = {
                sn
                for sn in self.verified_inverters
                if sn not in remove_from_verified_inverters
            }

        # remove restored inverters from skipped list
        add_to_verified = set(inverters) - self.verified_inverters
        if len(add_to_verified) > 0:
            _LOGGER.debug(
                "Envoy returned complete inverter data for: %s",
                ", ".join(sorted(add_to_verified)),
            )
            self.verified_inverters.update(add_to_verified)
            self.skipped_inverters = {
                sn for sn in self.skipped_inverters if sn not in add_to_verified
            }

        # resignal warning for skipped inverters if any left and if no log entry for some time
        self.resignal += 1 if self.skipped_inverters else 0
        if self.resignal > RESIGNAL_INTERVAL:
            self.resignal = 0
            _LOGGER.warning(
                "Envoy did not provide all inverters or inverter data, no data reported for: %s",
                ", ".join(sorted(self.skipped_inverters)),
            )

        envoy_data.inverters = inverters
