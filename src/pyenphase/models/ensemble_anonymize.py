"""Anonymization for ensemble endpoint containing serial numbers."""

from collections import Counter
from typing import Any

from pyenphase.const import ANONYMIZATION_EXC, FIXTURE_STATE
from pyenphase.utilities import device_type_name, usable_fixture


def anonymize_ensemble_power(
    serials: dict[str, str], fixtures: dict[str, Any], scan_only: bool
) -> tuple[str, set[str]]:
    """
    Anonymize ensemble power serial numbers.

    Processes endpoint fixtures[/ivp/ensemble/power].
    See :ref:`endpoint JSON<endpoint_ensemble_power>` for data details

    In scan_only True mode:
        add serial numbers found in ["devices"]["serial_num"] to serials.
        using "ENCHARGE" for device serial mapping in :any:`TYPE_SERIALS`.

    In scan_only False mode:
        replace serial numbers ["devices"]["serial_num"] by replacement in serials

        .. code-block:: json

            {
                "devices:": [
                    {
                        "serial_num": "123123123123",

                    },
                    {
                        "serial_num": "123123123124",

                    },
                ]
            }

    :param serials: dict {serial,dev_type|serial} to add serial and device type
        to in scan_only: True mode or obtain serial replacement from in
        scan_only: False mode
    :param fixtures: dict {endpoint, endpoint_data} to find or replace serials in
    :param scan_only: when true scan data for serial numbers and add to serials dict.
        when false replace serial numbers in data using serials dict as mapping.
    :returns: endpoint used and set of error descriptions occurred, empty if none
    """
    anonymization_errors: set[str] = set()
    if (
        (state := usable_fixture((endpoint := "/ivp/ensemble/power"), fixtures, dict))
        == FIXTURE_STATE.USABLE
        and "devices:" in (power_data := fixtures[endpoint])
        and isinstance((devices := power_data["devices:"]), list)
    ):
        for device in devices:
            if isinstance(device, dict) and "serial_num" in device:
                try:
                    if scan_only:
                        serials |= {device["serial_num"]: "ENCHARGE"}
                    else:
                        device["serial_num"] = serials.get(
                            device["serial_num"], "UNKNOWN"
                        )
                except ANONYMIZATION_EXC as exc:
                    anonymization_errors.add(f"Error on {endpoint} {exc!r}")
            else:
                anonymization_errors.add(f"Unexpected data type for {endpoint}")

    elif state in (FIXTURE_STATE.USABLE, FIXTURE_STATE.TYPE_ERROR):
        anonymization_errors.add(f"Unexpected data type for {endpoint}")

    return endpoint, anonymization_errors


def anonymize_ensemble_inventory(
    serials: dict[str, str], fixtures: dict[str, Any], scan_only: bool
) -> tuple[str, set[str]]:
    """
    Anonymize ensemble inventory serial numbers.

    Processes endpoint fixtures[/ivp/ensemble/inventory].
    See :ref:`endpoint JSON<endpoint_ensemble_inventory>` for data details.

    In scan_only True mode:
        add serial numbers found in [*]{*}["devices"]["serial_num"]
        to serials using "type" for device serial mapping in :any:`TYPE_SERIALS`.

    In scan_only False mode:
        replace serial_num found by replacement in serials[serial_num]

        .. code-block:: json

            [
                {
                    "type": "ENCHARGE",
                    "devices": [
                        {

                            "serial_num": "492516006337",
                        },
                        {

                        }
                    ]
                },
                {

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
    if (
        state := usable_fixture((endpoint := "/ivp/ensemble/inventory"), fixtures, list)
    ) == FIXTURE_STATE.USABLE:
        for inv_type in fixtures[endpoint]:
            if (
                isinstance(inv_type, dict)
                and "devices" in inv_type
                and isinstance((devices := inv_type["devices"]), list)
            ):
                dName = v if isinstance(v := inv_type.get("type"), str) else "UNKNOWN"
                for device in devices:
                    if isinstance(device, dict) and "serial_num" in device:
                        try:
                            if scan_only:
                                serials |= {device["serial_num"]: dName.upper()}
                            else:
                                device["serial_num"] = serials.get(
                                    device["serial_num"], "UNKNOWN"
                                )
                        except ANONYMIZATION_EXC as exc:
                            anonymization_errors.add(f"Error on {endpoint} {exc!r}")
                    else:
                        anonymization_errors.add(f"Unexpected data type for {endpoint}")
            else:
                anonymization_errors.add(f"Unexpected data type for {endpoint}")

    elif state == FIXTURE_STATE.TYPE_ERROR:
        anonymization_errors.add(f"Unexpected data type for {endpoint}")

    return endpoint, anonymization_errors


def new_keys(target: dict[str, Any], mask_with: str, serials: dict[str, str]) -> None:
    # replace serials in dict keys
    # prevent target entries without serials entry leaking serial, patch with unique string serial
    serial_counts = {k: v for k, v in Counter(serials.values()).items() if v > 1}
    unique_serials = {
        k: f"{v or 'BLANK'}{i}" if v in serial_counts else v
        for i, (k, v) in enumerate(serials.items())
    }
    renamed = {
        unique_serials.get(k, f"{mask_with}{i}"): v
        for i, (k, v) in enumerate(target.items())
    }
    target.clear()
    target.update(renamed)


def anonymize_ensemble_status(
    serials: dict[str, str], fixtures: dict[str, Any], scan_only: bool
) -> tuple[str, set[str]]:
    """
    Anonymize ensemble status serial numbers.

    Processes endpoint fixtures[/ivp/ensemble/status].
    See :ref:`endpoint JSON<endpoint_ensemble_status>` for data details.

    In scan_only True mode:
        add keys found in [inventory][serial_nums], serial_nums[device_id] value,
        serial_nums[submodules] keys to serials using
        ["device_type"] for device lookup in :any:`DEVICE_TYPES` with fallback to UNKNOWN

    In scan_only False mode:
        replace serial numbers found in [inventory][serial_nums] keys,
        serial_nums[device_id] values, serial_nums[submodules] keys
        by replacement in serials

        .. code-block:: json

            {
                "inventory": {
                    "serial_nums": {
                        "654320000039": {
                            "device_type": 27,
                            "device_id": "654320000039",

                            "submodule_count": 1,
                            "submodules": {
                                "654320000040": {
                                    "device_type": 31,
                                },
                            },
                        },
                    },
                },
            }

    :param serials: dict {serial,dev_type|serial} to add serial and device type
        to in scan_only: True mode or obtain serial replacement from in
        scan_only: False mode
    :param fixtures: dict {endpoint, endpoint_data} to find or replace serials in
    :param scan_only: when true scan data for serial numbers and add to serials dict.
        when false replace serial numbers in data using serials dict as mapping.
    :returns: endpoint used and set of error descriptions occurred, empty if none
    """
    anonymization_errors: set[str] = set()
    subidx: int = 0

    if (
        (state := usable_fixture((endpoint := "/ivp/ensemble/status"), fixtures, dict))
        == FIXTURE_STATE.USABLE
        and "inventory" in fixtures[endpoint]
        and isinstance((inventory := fixtures[endpoint]["inventory"]), dict)
        and "serial_nums" in inventory
        and isinstance((serial_nums := inventory["serial_nums"]), dict)
    ):
        for serial, data in serial_nums.items():
            if isinstance(data, dict):
                dType = device_type_name(data, "device_type")
                try:
                    if scan_only:
                        serials |= {serial: dType}
                        if "device_id" in data:
                            serials |= {data["device_id"]: dType}
                    else:
                        if "device_id" in data:
                            data["device_id"] = serials.get(
                                data["device_id"], "UNKNOWN"
                            )
                except ANONYMIZATION_EXC as exc:
                    anonymization_errors.add(f"Error on {endpoint} {exc!r}")

                if "submodules" in data and isinstance(
                    (sub_modules := data["submodules"]), dict
                ):
                    for sub_serial, sub_data in sub_modules.items():
                        if isinstance(sub_data, dict):
                            dsType = device_type_name(sub_data, "device_type")
                            try:
                                if scan_only:
                                    serials |= {sub_serial: dsType}
                            except ANONYMIZATION_EXC as exc:  # pragma: no cover
                                anonymization_errors.add(f"Error on {endpoint} {exc!r}")
                        elif scan_only:
                            serials |= {sub_serial: "UNKNOWN"}
                        else:
                            anonymization_errors.add(
                                f"Unexpected data type for {endpoint}"
                            )

                    if not scan_only:
                        # serials are key in dict, need to replace keys
                        new_keys(sub_modules, f"SUBSERIAL{subidx}", serials)
                        subidx += 1
                else:
                    anonymization_errors.add(f"Unexpected data type for {endpoint}")

            elif scan_only:
                serials |= {serial: "UNKNOWN"}

            else:
                anonymization_errors.add(f"Unexpected data type for {endpoint}")

        if not scan_only:
            # serials are key in dict, need to replace keys
            new_keys(serial_nums, "SERIAL", serials)

    elif state in (FIXTURE_STATE.USABLE, FIXTURE_STATE.TYPE_ERROR):
        anonymization_errors.add(f"Unexpected data type for {endpoint}")

    return endpoint, anonymization_errors
