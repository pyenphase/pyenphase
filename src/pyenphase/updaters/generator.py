import logging
from collections.abc import Callable
from typing import Any

from ..const import (
    ENSEMBLE_MIN_VERSION,
    URL_GEN_CONFIG,
    URL_GEN_MODE,
    URL_GEN_SCHEDULE,
    URL_GENERATOR,
    SupportedFeatures,
)
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS
from ..models.envoy import EnvoyData
from ..models.generator import (
    EnvoyGenerator,
    EnvoyGeneratorConfig,
    EnvoyGeneratorMode,
    EnvoyGeneratorSchedule,
)
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyGeneratorUpdater(EnvoyUpdater):
    """Class to handle updates for Generator information."""

    #: Whether the Envoy exposes the generator status endpoint, set during probe
    _generator_available: bool = False
    #: Whether the Envoy exposes the gen_schedule endpoint, set during probe
    _gen_schedule_available: bool = False
    #: Whether the Envoy exposes the gen_mode endpoint, set during probe
    _gen_mode_available: bool = False

    async def _optional_endpoint_available(
        self,
        end_point: str,
        verify_method: Callable[[dict[str, Any]], object] | None = None,
    ) -> bool:
        """
        Probe an optional generator endpoint and report its availability.
        Optionally verify endpoint data validity using the verify method.

        :param end_point: Envoy endpoint to probe
        :param verify_method: If specified used to verify endpoint data.
            Bool result of verify method is returned instead of bool result of probe request
        :return: True if the endpoint returned usable data
        """
        try:
            result = await self._json_probe_request(end_point)
        except ENDPOINT_PROBE_EXCEPTIONS as e:
            _LOGGER.debug("Generator endpoint not found at %s: %s", end_point, e)
            return False
        # Newer firmware with no generator configured returns an empty dict
        if not bool(result) or "error" in result or "err" in result:
            _LOGGER.debug("No usable Generator data at %s", end_point)
            return False
        if verify_method:
            # verify returned data validity
            verified = verify_method(result)
            _LOGGER.debug(
                "Generator endpoint %s data passed verification: %s",
                end_point,
                bool(verified),
            )
            return bool(verified)
        return True

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """
        Probe the Envoy for this updater and return found generator features.

        May set :any:`SupportedFeatures.GENERATOR` or
        :any:`SupportedFeatures.GENERATOR_SCHEDULE`.

        Probes endpoints :any:`URL_GEN_CONFIG`, :any:`URL_GENERATOR`,
        :any:`URL_GEN_SCHEDULE` and :any:`URL_GEN_MODE`

        Requires :any:`SupportedFeatures.ENPOWER` to be set,
        if not, no probe efforts are done and None is returned.
        """
        if self._envoy_version < ENSEMBLE_MIN_VERSION:
            _LOGGER.debug("Firmware too old for Ensemble support")
            return None

        # If there's no Enpower smart switch, we can skip the generator probe
        if SupportedFeatures.ENPOWER not in discovered_features:
            return None

        # Check for generator support
        result = await self._optional_endpoint_available(URL_GEN_CONFIG)
        if not result:
            _LOGGER.debug("No generator configuration found")
            return None

        self._supported_features |= SupportedFeatures.GENERATOR

        # The generator status, schedule and operation mode live in
        # separate endpoints that are not all present on every
        # generator-capable firmware. Probe each one so update() only
        # fetches what is available and the corresponding data fields
        # degrade independently to None.
        self._generator_available = await self._optional_endpoint_available(
            URL_GENERATOR
        )
        # verify data for missing exercise_config
        self._gen_schedule_available = await self._optional_endpoint_available(
            URL_GEN_SCHEDULE, EnvoyGeneratorSchedule.from_api
        )
        # if valid schedule signal availability to clients so they can use it as guard
        if self._gen_schedule_available:
            self._supported_features |= SupportedFeatures.GENERATOR_SCHEDULE

        self._gen_mode_available = await self._optional_endpoint_available(URL_GEN_MODE)

        return self._supported_features

    async def update(self, envoy_data: EnvoyData) -> None:
        """Update the generator data if supported."""
        if self._generator_available:
            generator_data: dict[str, Any] = await self._json_request(URL_GENERATOR)
            envoy_data.raw[URL_GENERATOR] = generator_data
            envoy_data.generator = EnvoyGenerator.from_api(generator_data)

        generator_config_data: dict[str, Any] = await self._json_request(URL_GEN_CONFIG)
        envoy_data.raw[URL_GEN_CONFIG] = generator_config_data
        envoy_data.generator_config = EnvoyGeneratorConfig.from_api(
            generator_config_data
        )

        if self._gen_schedule_available:
            generator_schedule_data: dict[str, Any] = await self._json_request(
                URL_GEN_SCHEDULE
            )
            envoy_data.raw[URL_GEN_SCHEDULE] = generator_schedule_data
            envoy_data.generator_schedule = EnvoyGeneratorSchedule.from_api(
                generator_schedule_data
            )
            if not envoy_data.generator_schedule:
                _LOGGER.debug("Generator Schedule returned None.")

        if self._gen_mode_available:
            generator_mode_data: dict[str, Any] = await self._json_request(URL_GEN_MODE)
            envoy_data.raw[URL_GEN_MODE] = generator_mode_data
            envoy_data.generator_mode = EnvoyGeneratorMode.from_api(generator_mode_data)
