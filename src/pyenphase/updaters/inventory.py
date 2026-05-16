"""Pyenphase inventory updater class."""

import logging
from typing import Any

from ..const import URL_INVENTORY, SupportedFeatures
from ..exceptions import ENDPOINT_PROBE_EXCEPTIONS, EnvoyAuthenticationRequired
from ..models.acb import EnvoyACB
from ..models.envoy import EnvoyData
from .base import EnvoyUpdater

_LOGGER = logging.getLogger(__name__)


class EnvoyInventoryUpdater(EnvoyUpdater):
    """Updater for generic inventory endpoint, currently for ACB devices."""

    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe inventory endpoint for ACB devices when ACB support is discovered."""
        if SupportedFeatures.ACB not in discovered_features:
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

        for item in inventory_data:
            if item.get("type") == "ACB" and item.get("devices"):
                self._supported_features |= SupportedFeatures.ACB
                return self._supported_features

        return None

    async def update(self, envoy_data: EnvoyData) -> None:
        """Update per-device ACB inventory from inventory endpoint."""
        if not self._supported_features & SupportedFeatures.ACB:
            return

        inventory_data: list[dict[str, Any]] = await self._json_request(URL_INVENTORY)
        envoy_data.raw[URL_INVENTORY] = inventory_data

        acb_inventory: dict[str, EnvoyACB] = {}
        for item in inventory_data:
            if item.get("type") != "ACB":
                continue
            for device in item.get("devices", []):
                serial = device.get("serial_num")
                if not serial:
                    continue
                serial_str = str(serial)
                inverter = envoy_data.inverters.get(serial_str)
                acb_inventory[serial_str] = EnvoyACB.from_api(device, inverter)

        if acb_inventory:
            envoy_data.acb_inventory = acb_inventory
