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
            if item.get("type") != "ACB":
                continue
            # Only declare ACB support if there is at least one active (non-decommissioned) device
            if any(
                isinstance(d, dict) and d.get("admin_state", 0) != 0
                for d in item.get("devices", [])
            ):
                self._supported_features |= SupportedFeatures.ACB
                return self._supported_features

        return None

    async def update(self, envoy_data: EnvoyData) -> None:
        """Update per-device ACB inventory from inventory endpoint."""
        if not self._supported_features & SupportedFeatures.ACB:
            return

        inventory_data: list[dict[str, Any]] = await self._json_request(URL_INVENTORY)
        envoy_data.raw[URL_INVENTORY] = inventory_data

        # Build per-ACB power lookup from devType=11 entries in the v1 inverters response.
        # devType=1 (solar microinverters) are filtered out of envoy_data.inverters, so we
        # read directly from the raw response to avoid polluting the inverters dict.
        raw_v1_inverters: list[dict[str, Any]] = envoy_data.raw.get(
            URL_PRODUCTION_INVERTERS, []
        )
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
                # Skip decommissioned devices (admin_state == 0)
                if not isinstance(device, dict) or device.get("admin_state", 0) == 0:
                    continue
                serial = device.get("serial_num")
                if not serial:
                    continue
                serial_str = str(serial)
                inverter = acb_power_lookup.get(serial_str)
                acb_inventory[serial_str] = EnvoyACB.from_api(device, inverter)

        if acb_inventory:
            envoy_data.acb_inventory = acb_inventory
