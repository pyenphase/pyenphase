"""Pyenphase Ensemble updater class."""

import logging
from typing import Any

from ..const import (
    ENSEMBLE_MIN_VERSION,
    URL_DRY_CONTACT_SETTINGS,
    URL_DRY_CONTACT_STATUS,
    URL_ENCHARGE_BATTERY,
    URL_ENSEMBLE_INVENTORY,
    URL_ENSEMBLE_SECCTRL,
    SupportedFeatures,
)
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS
from ..models.acb import EnvoyBatteryAggregate
from ..models.c6combiner import EnvoyC6CC
from ..models.collar import EnvoyCollar
from ..models.dry_contacts import EnvoyDryContactSettings, EnvoyDryContactStatus
from ..models.encharge import EnvoyEncharge, EnvoyEnchargeAggregate, EnvoyEnchargePower
from ..models.enpower import EnvoyEnpower
from ..models.envoy import EnvoyData
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyEnembleUpdater(EnvoyUpdater):
    """Class to handle updates for Ensemble devices."""

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe the Envoy for this updater and return SupportedFeatures."""
        if self._envoy_version < ENSEMBLE_MIN_VERSION:
            _LOGGER.debug("Firmware too old for Ensemble support")
            return None

        # Check for various Ensemble support
        # The Ensemble Inventory endpoint will tell us if we have Enpower or Encharge support
        try:
            result = await self._json_probe_request(URL_ENSEMBLE_INVENTORY)
        except ENDPOINT_PROBE_EXCEPTIONS as e:
            _LOGGER.debug("Ensemble Inventory endpoint not found: %s", e)
        else:
            if not result or "error" in result:
                # Newer firmware with no Ensemble devices returns an empty list
                _LOGGER.debug("No Ensemble devices found")
                return None

            for item in result:
                if item["type"] == "ENPOWER":
                    self._supported_features |= SupportedFeatures.ENPOWER
                if item["type"] == "ENCHARGE":
                    self._supported_features |= SupportedFeatures.ENCHARGE
                if item["type"] == "COLLAR":
                    self._supported_features |= SupportedFeatures.COLLAR
                if item["type"] == "C6 COMBINER CONTROLLER":
                    self._supported_features |= SupportedFeatures.C6CC

        return self._supported_features

    async def update(self, envoy_data: EnvoyData) -> None:
        """Update the Envoy for this updater."""
        # Update Enpower and Encharge data if supported
        supported_features = self._supported_features
        ensemble_inventory_data: list[dict[str, Any]] = await self._json_request(
            URL_ENSEMBLE_INVENTORY
        )
        envoy_data.raw[URL_ENSEMBLE_INVENTORY] = ensemble_inventory_data

        ensemble_secctrl_data: dict[str, Any] = await self._json_request(
            URL_ENSEMBLE_SECCTRL
        )
        envoy_data.raw[URL_ENSEMBLE_SECCTRL] = await self._json_request(
            URL_ENSEMBLE_SECCTRL
        )

        if supported_features & SupportedFeatures.ENCHARGE:
            encharge_power_data: dict[str, Any] = await self._json_request(
                URL_ENCHARGE_BATTERY
            )
            envoy_data.raw[URL_ENCHARGE_BATTERY] = encharge_power_data
            power: dict[str, Any] = {
                device["serial_num"]: device
                for device in encharge_power_data["devices:"]
            }
            inventory: dict[str, Any] = {}
            for item in ensemble_inventory_data:
                if item["type"] != "ENCHARGE":
                    continue
                inventory = {device["serial_num"]: device for device in item["devices"]}

            envoy_data.encharge_inventory = {
                serial: EnvoyEncharge.from_api(inventory[serial])
                for serial in inventory
            }
            envoy_data.encharge_power = {
                serial: EnvoyEnchargePower.from_api(power[serial]) for serial in power
            }
            envoy_data.encharge_aggregate = EnvoyEnchargeAggregate.from_api(
                ensemble_secctrl_data
            )

        if supported_features & SupportedFeatures.ENPOWER:
            # Update Enpower data
            for item in ensemble_inventory_data:
                if item["type"] != "ENPOWER":
                    continue
                enpower_data = item["devices"][0]
            envoy_data.enpower = EnvoyEnpower.from_api(enpower_data)

            # Update dry contact data
            dry_contact_status_data: dict[str, Any] = await self._json_request(
                URL_DRY_CONTACT_STATUS
            )
            envoy_data.raw[URL_DRY_CONTACT_STATUS] = dry_contact_status_data

            dry_contact_settings_data: dict[str, Any] = await self._json_request(
                URL_DRY_CONTACT_SETTINGS
            )
            envoy_data.raw[URL_DRY_CONTACT_SETTINGS] = dry_contact_settings_data

            envoy_data.dry_contact_status = {
                relay["id"]: EnvoyDryContactStatus.from_api(relay)
                for relay in dry_contact_status_data["dry_contacts"]
            }
            envoy_data.dry_contact_settings = {
                relay["id"]: EnvoyDryContactSettings.from_api(relay)
                for relay in dry_contact_settings_data["dry_contacts"]
            }

        # production updater will set common_properties.ACB_batteries_reported
        # to count of ACB batteries. Check if production report found
        # acb batteries and if so report combined soc and max capacity
        # for Encharge and ACB batteries
        if self._common_properties.acb_batteries_reported:
            envoy_data.battery_aggregate = EnvoyBatteryAggregate.from_api(
                ensemble_secctrl_data
            )

        # IQ Meter collar seems like a single instance only
        if supported_features & SupportedFeatures.COLLAR:
            # Update Collar data
            for item in ensemble_inventory_data:
                if item["type"] != "COLLAR":
                    continue
                if item.get("devices"):
                    collar_data = item["devices"][0]
                    envoy_data.collar = EnvoyCollar.from_api(collar_data)

        # C6 Combiner seems like a single instance only
        if supported_features & SupportedFeatures.C6CC:
            # Update C6CC data
            for item in ensemble_inventory_data:
                if item["type"] != "C6 COMBINER CONTROLLER":
                    continue
                if item.get("devices"):
                    c6cc_data = item["devices"][0]
                    envoy_data.c6cc = EnvoyC6CC.from_api(c6cc_data)
