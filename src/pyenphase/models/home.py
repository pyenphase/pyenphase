"""Model for ENphase Envoy home data"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _find_active_interface(
    interfaces: list[dict[str, Any]], name: str
) -> dict[str, Any] | None:
    """Find an interface by interface name."""
    if interfaces:
        for interface in interfaces:
            if interface.get("interface") == name:
                return interface
    return None


@dataclass(slots=True)
class EnvoyInterfaceInformation:
    """Envoy Interface information data model."""

    primary_interface: str  #: name of primary (active) interface
    mac: str  #: mac of primary interface, "unknown" if missing
    interface_type: str  #: primary interface type, "unknown" if missing
    dhcp: bool  #: interfaces uses DHCP, False if missing
    software_build_epoch: int  #: envoy software build time, 0 if missing
    timezone: str  #: Timezone set in Envoy, "unknown" if missing

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> EnvoyInterfaceInformation | None:
        """
        Return active interface information configured in Envoy

        Parses the received JSON into EnvoyInterfaceInformation model data
        Source data must be sourced from URL_HOME.

        software_build_epoch, timezone are returned as is.
        network.primary_interface is returned as is, and used
        to find interface data in network.interfaces from which
        type, mac and dhcp are returned.

        Not all Envoy firmware version may return all data. Defaults for
        str members is unknown, int 0 and bool False

        Example json returned from /home endpoint:

            .. code-block:: json

                {
                "software_build_epoch": 1719503966,
                "timezone": "Europe/Amsterdam",
                "current_date": "04/24/2025",
                "current_time": "14:53",
                "network": {
                    "web_comm": true,
                    "ever_reported_to_enlighten": true,
                    "last_enlighten_report_time": 1745499043,
                    "primary_interface": "eth0",
                    "interfaces": [
                    {
                        "type": "ethernet",
                        "interface": "eth0",
                        "mac": "00:1D:C0:7F:B6:3B",
                        "dhcp": true,
                        "ip": "192.168.3.112",
                        "signal_strength": 1,
                        "signal_strength_max": 1,
                        "carrier": true
                    },
                    {
                        "signal_strength": 0,
                        "signal_strength_max": 0,
                        "type": "wifi",
                        "interface": "wlan0",
                        "mac": "60:E8:5B:AB:9D:64",
                        "dhcp": true,
                        "ip": null,
                        "carrier": false,
                        "supported": true,
                        "present": true,
                        "configured": false,
                        "status": "connecting"
                    }
                ]
            }

        :param data: json returned by /home endpoint
        :return: Envoy interface configuration information
        """
        # not sure if all firmware versions have all the needed information
        if not (network := data.get("network")):
            return None
        if not (
            interface := _find_active_interface(
                network.get("interfaces"), (name := network.get("primary_interface"))
            )
        ):
            return None
        return cls(
            primary_interface=name,
            mac=interface.get("mac", "unknown"),
            interface_type=interface.get("type", "unknown"),
            dhcp=interface.get("dhcp", False),
            software_build_epoch=data.get("software_build_epoch", 0),
            timezone=data.get("timezone", "unknown"),
        )
