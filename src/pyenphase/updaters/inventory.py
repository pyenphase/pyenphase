"""Pyenphase inventory updater class."""

import logging
from typing import Any

from ..const import URL_INVENTORY, URL_PRODUCTION_INVERTERS, SupportedFeatures
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS, EnvoyAuthenticationRequired
from ..models.acb import EnvoyACB
from ..models.envoy import EnvoyData
from ..models.inverter import EnvoyInverter
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyInventoryUpdater(EnvoyUpdater):
    """Updater for generic inventory endpoint, currently for inverter firmware and ACB devices."""

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe inventory endpoint when inverter or ACB support is discovered."""
        if not discovered_features & (
            SupportedFeatures.ACB | SupportedFeatures.INVERTERS
        ):
            return None

        try:
            inventory_data = await self._json_probe_request(URL_INVENTORY)
        except ENDPOINT_PROBE_EXCEPTIONS as err:
            _LOGGER.debug("Inventory endpoint not found at %s: %s", URL_INVENTORY, err)
            return None
        except EnvoyAuthenticationRequired as err:
            _LOGGER.debug(
                "Skipping inventory endpoint as user does not have access to %s: %s",
                URL_INVENTORY,
                err,
            )
            return None

        if not isinstance(inventory_data, list):
            return None

        # Inventory reports the running firmware of every inverter, which the
        # inverter updaters' endpoints lack.
        if SupportedFeatures.INVERTERS in discovered_features:
            self._supported_features |= SupportedFeatures.INVERTERS

        if SupportedFeatures.ACB in discovered_features:
            for item in inventory_data:
                if item.get("type") != "ACB":
                    continue
                # Only declare ACB support if there is at least one active (non-decommissioned) device.
                # admin_state == 0 means decommissioned; absent means active.
                if any(
                    isinstance(d, dict) and d.get("admin_state") != 0
                    for d in item.get("devices", [])
                ):
                    self._supported_features |= SupportedFeatures.ACB
                    break

        return self._supported_features or None

    async def update(self, envoy_data: EnvoyData) -> None:
        """Update inverter firmware and per-device ACB inventory from inventory endpoint."""
        if not self._supported_features:
            return

        inventory_data: list[dict[str, Any]] = await self._json_request(URL_INVENTORY)
        envoy_data.raw[URL_INVENTORY] = inventory_data

        for item in inventory_data:
            for device in item.get("devices", []):
                if not isinstance(device, dict) or device.get("admin_state") == 0:
                    continue
                if inverter := envoy_data.inverters.get(str(device.get("serial_num"))):
                    inverter.firmware_version = device.get("img_pnum_running")

        if not self._supported_features & SupportedFeatures.ACB:
            return

        # Build per-ACB power lookup from devType=11 entries in the v1 inverters response.
        # devType=1 (solar microinverters) are filtered out of envoy_data.inverters, so we
        # read directly from the raw response to avoid polluting the inverters dict.
        raw_v1_inverters: list[dict[str, Any]] = envoy_data.raw.get(
            URL_PRODUCTION_INVERTERS, []
        )
        if not raw_v1_inverters:
            try:
                raw_v1_inverters = await self._json_request(URL_PRODUCTION_INVERTERS)
                envoy_data.raw[URL_PRODUCTION_INVERTERS] = raw_v1_inverters
            except ENDPOINT_PROBE_EXCEPTIONS as err:
                _LOGGER.debug(
                    "Unable to fetch %s for ACB power details: %s",
                    URL_PRODUCTION_INVERTERS,
                    err,
                )
                raw_v1_inverters = []
            except EnvoyAuthenticationRequired as err:
                _LOGGER.debug(
                    "No access to %s for ACB power details: %s",
                    URL_PRODUCTION_INVERTERS,
                    err,
                )
                raw_v1_inverters = []
        acb_power_lookup: dict[str, EnvoyInverter] = {
            inv["serialNumber"]: EnvoyInverter.from_v1_api(inv)
            for inv in raw_v1_inverters
            if isinstance(inv, dict) and inv.get("devType") == 11
        }

        acb_inventory: dict[str, EnvoyACB] = {}
        for item in inventory_data:
            if item.get("type") != "ACB":
                continue
            for device in item.get("devices", []):
                # Skip decommissioned devices (admin_state == 0).
                # Devices without admin_state are treated as active.
                if not isinstance(device, dict) or device.get("admin_state") == 0:
                    continue
                serial = device.get("serial_num")
                if not serial:
                    continue
                serial_str = str(serial)
                inverter = acb_power_lookup.get(serial_str)
                acb_inventory[serial_str] = EnvoyACB.from_api(device, inverter)

        if acb_inventory:
            envoy_data.acb_inventory = acb_inventory
