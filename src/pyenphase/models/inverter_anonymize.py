"""Anonymization for inverters containing serial numbers."""

from typing import Any

from pyenphase.const import ANONYMIZATION_EXC, FIXTURE_STATE
from pyenphase.utilities import device_type_name, usable_fixture


def anonymize_inverters(
    serials: dict[str, str], fixtures: dict[str, Any], scan_only: bool
) -> tuple[str, set[str]]:
    """
    Anonymize inverter serial numbers.

    Processes endpoint fixtures[/api/v1/production/inverters]
    See :ref:`endpoint JSON<endpoint_inverters>` for data details

    In scan_only True mode:
        add serial numbers found [*]["serialNumber"] to serials using ["devType"]
        for device lookup in :any:`DEVICE_TYPES` in turn used for device serial
        mapping in :any:`TYPE_SERIALS` with fallback to UNKNOWN.

    In scan_only False mode:
        replace serial numbers found by replacement in serials

        .. code-block:: json

            [
                {
                    "serialNumber": "202020202020",
                    "devType": 1,

                },
            ]

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
        state := usable_fixture(
            (endpoint := "/api/v1/production/inverters"), fixtures, list
        )
    ) == FIXTURE_STATE.USABLE:
        for inverter in fixtures[endpoint]:
            if isinstance(inverter, dict) and "serialNumber" in inverter:
                dType = device_type_name(inverter, "devType")
                try:
                    if scan_only:
                        serials |= {inverter["serialNumber"]: dType}
                    else:
                        inverter["serialNumber"] = serials.get(
                            inverter["serialNumber"], "UNKNOWN"
                        )
                except ANONYMIZATION_EXC as exc:
                    anonymization_errors.add(f"Error on {endpoint} {exc!r}")
            else:
                anonymization_errors.add(f"Unexpected data type for {endpoint}")

    elif state == FIXTURE_STATE.TYPE_ERROR:
        anonymization_errors.add(f"Unexpected data type for {endpoint}")

    return endpoint, anonymization_errors
