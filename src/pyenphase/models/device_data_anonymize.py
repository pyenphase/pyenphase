"""Anonymization for device_data endpoint containing serial numbers."""

from typing import Any

from pyenphase.const import ANONYMIZATION_EXC, FIXTURE_STATE
from pyenphase.utilities import safe_error_description, usable_fixture


def anonymize_device_data(
    serials: dict[str, str], fixtures: dict[str, Any], scan_only: bool
) -> tuple[str, set[str]]:
    """
    Anonymize device_data serial numbers.

    Processes endpoint fixtures[/ivp/pdm/device_data]
    See :ref:`endpoint JSON<endpoint_device_data>` for data details

    In scan_only True mode:
        add sn found serials specifying uppercase devName device type
        with fallback to UNKNOWN.

    In scan_only False mode:
        replace sn found by replacement in serial[serial_num]

        .. code-block:: json

            {
                "654321984": {
                    "devName": "pcu",
                    "sn": "202020202020",
                    "active": true,
                    "modGone": false,
                    "channels": [
                    ]
                },
            }

    :param serials: dict {serial,dev_type | serial} to add serial and device type
        to in scan_only: True mode or obtain serial replacement from in
        scan_only: False mode
    :param fixtures: dict {endpoint, endpoint_data} to find or replace serials in
    :param scan_only: when true scan data for serial numbers and add to serials dict.
        when false replace serial numbers in data using serials dict as mapping.
    :returns: endpoint used and set of error descriptions occurred, empty if none
    """
    anonymization_errors: set[str] = set()
    if (
        state := usable_fixture((endpoint := "/ivp/pdm/device_data"), fixtures, dict)
    ) == FIXTURE_STATE.USABLE:
        for name, device in fixtures[endpoint].items():
            # "deviceCount" are "deviceDataLimit" are plain numbers, not dict
            if isinstance(device, dict) and "sn" in device:
                dName = v if isinstance(v := device.get("devName"), str) else "UNKNOWN"
                try:
                    if scan_only:
                        serials |= {device["sn"]: dName.upper()}
                    else:
                        device["sn"] = serials.get(device["sn"], "UNKNOWN")
                except ANONYMIZATION_EXC as exc:
                    anonymization_errors.add(
                        f"Error on {endpoint} {safe_error_description(exc)}"
                    )
            else:
                if name not in (
                    "deviceCount",
                    "deviceDataLimit",
                ):
                    anonymization_errors.add(f"Unexpected data type for {endpoint}")

    elif state == FIXTURE_STATE.MISSING:
        return "", anonymization_errors

    elif state == FIXTURE_STATE.TYPE_ERROR:
        anonymization_errors.add(f"Unexpected data type for {endpoint}")

    else:
        # signal unusable data that may contain some serials or not
        anonymization_errors.add(f"Unusable data for {endpoint}")

    return endpoint, anonymization_errors
