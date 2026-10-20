"""Anonymization for inventory endpoint containing serial numbers."""

from typing import Any

from pyenphase.const import ANONYMIZATION_EXC
from pyenphase.utilities import usable_fixture


def anonymize_inventory(
    serials: dict[str, str], fixtures: dict[str, Any], scan_only: bool
) -> tuple[str, set[str]]:
    """
    Anonymize inventory serial numbers.

    Processes endpoint fixtures[[/inventory.json?deleted=1].
    See :ref:`endpoint JSON<endpoint_inventory>` for data details

    In scan_only True mode:
        add serial numbers found in [*]{*}["devices"]["serial_num"]
        to serials using "type" value for device serial mapping
        in :any:`TYPE_SERIALS` with fallback to UNKNOWN.


    In scan_only False mode:
        replace serial numbers found in
        [*]{*}["devices"]["serial_num"] by replacement in serials

        .. code-block:: json

            [
                {
                    "type": "PCU",
                    "devices": [
                        {

                        "serial_num": "654321000001",

                        },
                    ]
                }
            ]

    :param serials: dict {serial,dev_type|serial} to add serial and device type
        to in scan_only: True mode or obtain serial replacement from in
        scan_only: False mode
    :param fixtures: dict {endpoint, endpoint_data} to find or replace serials in
    :param scan_only: when true scan data for serial numbers and add to serials dict.
        when false replace serial numbers in data using serials dict as mapping.
    :returns: endpoint used and set of error descriptions occurred, empty if none
    """
    anonymization_errors: set[str] = set()
    if usable_fixture((endpoint := "/inventory.json?deleted=1"), fixtures, list):
        for inv_type in fixtures[endpoint]:
            if (
                isinstance(inv_type, dict)
                and "devices" in inv_type
                and isinstance(inv_type["devices"], list)
            ):
                dType = v if isinstance(v := inv_type.get("type"), str) else "UNKNOWN"
                for device in inv_type["devices"]:
                    if isinstance(device, dict) and "serial_num" in device:
                        try:
                            if scan_only:
                                serials |= {device["serial_num"]: dType.upper()}
                            else:
                                device["serial_num"] = serials.get(
                                    device["serial_num"], "UNKNOWN"
                                )
                        except ANONYMIZATION_EXC as exc:
                            anonymization_errors.add(f"Error on {endpoint} {exc!r}")
    return endpoint, anonymization_errors
