"""Anonymization for info endpoint containing serial numbers."""

import re
from typing import Any

from pyenphase.const import FIXTURE_STATE
from pyenphase.utilities import usable_fixture


def anonymize_info(
    serials: dict[str, str], fixtures: dict[str, Any], scan_only: bool
) -> tuple[str, set[str]]:
    """
    Anonymize Envoy info endpoint.

    Processes endpoint fixtures[/info]
    See :ref:`endpoint JSON<endpoint_info>` for data details with
    device type "ENVOY"

    In scan_only True mode:
        add serial number found in string between <sn>...</sn> to serials.

    In scan_only False mode:
        replace serial number found in string between
        <sn>...</sn> by replacement in serials

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
        state := usable_fixture((endpoint := "/info"), fixtures, str)
    ) == FIXTURE_STATE.USABLE:
        match = re.search(r"(<sn>([^<]+)<\/sn>)", (data := fixtures[endpoint]))
        if match:
            if scan_only:
                serials[match.group(2)] = "ENVOY"
            else:
                fixtures[endpoint] = data.replace(
                    match.group(1),
                    f"<sn>{serials.get(match.group(2), 'UNKNOWN')}</sn>",
                )
        else:
            anonymization_errors.add(
                f"Unexpected data type for {endpoint}, no <sn>serial</sn> found"
            )

    elif state == FIXTURE_STATE.MISSING:
        return "", anonymization_errors

    elif state == FIXTURE_STATE.TYPE_ERROR:
        anonymization_errors.add(f"Unexpected data type for {endpoint}")

    else:
        # signal unusable data that may contain some serials or not
        anonymization_errors.add(f"Unusable data for {endpoint}")

    return endpoint, anonymization_errors
