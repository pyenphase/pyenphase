"""Anonymize known serial numbers in Envoy data."""

import copy
import logging
import re
from typing import Any

import orjson

from pyenphase.models.device_data_anonymize import anonymize_device_data
from pyenphase.models.ensemble_anonymize import (
    anonymize_ensemble_inventory,
    anonymize_ensemble_power,
    anonymize_ensemble_status,
)
from pyenphase.models.envoy_anonymize import anonymize_info
from pyenphase.models.inventory_anonymize import anonymize_inventory
from pyenphase.models.inverter_anonymize import anonymize_inverters

from .const import (
    ANONYMIZATION_ERROR_KEY,
    ANONYMIZATION_EXC,
    ENVOY_SERIAL,
    MASK_STATE,
    TYPE_SERIALS,
)

_LOGGER = logging.getLogger(__name__)

ANONYMIZERS = [
    anonymize_info,
    anonymize_inverters,
    anonymize_device_data,
    anonymize_inventory,
    anonymize_ensemble_power,
    anonymize_ensemble_inventory,
    anonymize_ensemble_status,
]


def anonymize_serials(
    endpoint_data: dict[str, Any], envoy_serial: str | None = None, strict: bool = False
) -> dict[str, Any]:
    """
    Replace serial numbers by neutral values.

    Deep copies endpoint_data and replaces serial numbers in known
    locations for the Envoy, inverters, ensemble and pdm devices by
    generic values and returns the new dict.

    Replacement is on best effort based on current knowledge of Envoy
    local API. Depending on actual Envoy firmware version running in the Envoy
    and its configuration, original serials may still be present upon completion.

    If any error occurs during serial replacement, the data may be returned
    with partial replaced serials. Any error is signalled by the presence of
    the `anonymization_errors_log` key in the returned dict. The key value
    contains a list of occurred errors. Callers should check for this key
    and decide how to handle it.

    If strict == True, failed serial masking entries will be removed
    from the result.

    A matching '<endpoint>_log' dict entry will be added or updated with
    a 'mask_state' key of type :any:`MASK_STATE` that signals the
    resulting status of the masking.

    If the '<endpoint>_log' exists when masking, it will be checked
    for the presence of the key 'code'. If present and its value is not
    200 (HTML status) the endpoint data will be considered invalid and excluded
    from masking.

    Generics serial numbers assigned to mask originals:

    - Envoy: 123456789012.
    - Inverter: 1000000000nn
    - ACB: 2000000000nn
    - Ensemble devices
        - Encharge batteries: 3000000000nn
        - Enpower device: 4000000000nn
        - COLLAR: 5100000000nn
        - C6 COMBINER CONTROLLER: 5200000000nn
        - C6 RGM: 5300000000nn
    - Other devices
        - NSRB: 6100000000nn
        - ESUB: 6200000000nn
        - ENCHARGE PCU: 6300000000nn
        - ENCHARGE BMU: 6400000000nn
    - Unknown devices: 9900000000nn

    :param endpoint_data: dict keyed by endpoint and containing endpoint
        data. Only entries that start with / and do not end in _log
        are masked.
    :param envoy_serial: envoy serial number to include in serials
         to replace, use if no /info endpoint is in the data set
    :param strict: if True then failed anonymizations will be removed from
        the result. Default False
    :returns: New dict copy of collected_fixtures with serials replaced.
        Key 'anonymization_errors_log' will be present if anonymization had
        errors and could not anonymize all entries.
    """
    fixtures = copy.deepcopy(endpoint_data)
    anonymization_errors: set[str] = set()
    serials: dict[str, Any] = {}
    endpoint_processed: list[str] = []
    endpoint_status: dict[str, Any] = {}

    def add_log(
        endpoint: str, endpoint_fixtures: dict[str, Any], log_entry: dict[str, Any]
    ) -> None:
        endpoint_fixtures[f"{endpoint}_log"] = (
            endpoint_fixtures.get(f"{endpoint}_log", {}) | log_entry
        )

    # Add the Envoy serial
    if envoy_serial:
        serials[envoy_serial] = "ENVOY"

    # scan data for serial numbers to replace
    for anonymizer in ANONYMIZERS:
        cur_count = len(serials)
        endpoint, result = anonymizer(serials, fixtures, scan_only=True)
        endpoint_processed.append(endpoint)
        if len(result):
            anonymization_errors.update(result)
            _LOGGER.debug(
                "Anonymizer scan for %s returned %s serials, %s errors: %s",
                endpoint,
                len(serials) - cur_count,
                len(result),
                result,
            )
            endpoint_status[endpoint] = len(result)
            add_log(endpoint, fixtures, {"mask_state": MASK_STATE.FAILED})

    # group all unknown device types into unknown group
    serials = {
        k: (v if v in TYPE_SERIALS or v in ("ENVOY", "EIM") else "UNKNOWN")
        for k, v in serials.items()
    }

    # assign replacement serials by types in serial sequential order
    try:
        serials.update(
            {
                key: f"{int(TYPE_SERIALS[serials[key]]) + index}"
                for serial_type in set(serials.values())
                if serial_type not in ("ENVOY", "EIM")
                for index, key in enumerate(
                    sorted(
                        [
                            key
                            for key, value in serials.items()
                            if value == serial_type
                            # leave empty and non str keys as their device code
                            and isinstance(key, str)
                            and key
                        ]
                    )
                )
            }
        )
    except ANONYMIZATION_EXC as exc:
        _LOGGER.debug(
            "Error when calculating replacement serials %s",
            repr(exc),
        )
        anonymization_errors.add(f"Error during serial sequencing {exc!r}")
        if strict:
            for endpoint in endpoint_processed:
                if endpoint not in fixtures:
                    continue
                _LOGGER.debug(
                    "Anonymizer in strict mode, removing %s from data", endpoint
                )
                fixtures.pop(endpoint, None)
                add_log(endpoint, fixtures, {"mask_state": MASK_STATE.REMOVED})

    # envoy and pdm EIM device contain envoy serial followed by EIMn
    serials.update(
        {
            key: f"{ENVOY_SERIAL}{key[key.find('EIM') :] if key.find('EIM') != -1 else ''}"
            for key, value in serials.items()
            if value in ("ENVOY", "EIM") and isinstance(key, str) and key
        }
    )

    # replace serials
    for anonymizer in ANONYMIZERS:
        endpoint, result = anonymizer(serials, fixtures, scan_only=False)
        if len(result):
            anonymization_errors.update(result)
            _LOGGER.debug(
                "Anonymizer serial replacement for %s returned %s errors: %s",
                endpoint,
                len(result),
                result,
            )
            endpoint_status[endpoint] = endpoint_status.get(endpoint, len(result))
            add_log(endpoint, fixtures, {"mask_state": MASK_STATE.FAILED})

    # scan for known serials in all endpoints and signal for strict removal if found
    known_serials = [s for s in serials if isinstance(s, str) and s and len(s) > 6]
    if known_serials:
        pattern = re.compile(
            f"(?<![0-9A-Za-z])({'|'.join(known_serials)})(?![0-9A-Za-z])"
        )
        for endpoint in list(fixtures):
            if not endpoint.endswith("_log") and endpoint.startswith("/"):
                try:
                    match = re.search(
                        pattern, orjson.dumps(fixtures[endpoint]).decode()
                    )
                    if match:
                        endpoint_status[endpoint] = endpoint_status.get(endpoint, 1)
                        anonymization_errors.add(
                            f"Masked serials also found in {endpoint}"
                        )
                        add_log(endpoint, fixtures, {"mask_state": MASK_STATE.FAILED})

                except ANONYMIZATION_EXC as exc:
                    endpoint_status[endpoint] = endpoint_status.get(endpoint, 1)
                    anonymization_errors.add(
                        f"Error during serial replacement for {endpoint} {exc!r}"
                    )
                    add_log(endpoint, fixtures, {"mask_state": MASK_STATE.FAILED})
                    continue

    # in strict modus remove failed endpoints
    if strict and len(endpoint_status):
        for endpoint in endpoint_status:
            _LOGGER.debug("Anonymizer in strict mode, removing %s from data", endpoint)
            fixtures.pop(endpoint, None)
            add_log(endpoint, fixtures, {"mask_state": MASK_STATE.REMOVED})

    # mark endpoint_log entry for unchanged endpoints
    for endpoint in list(fixtures):
        if (
            not endpoint.endswith("_log")
            and endpoint.startswith("/")
            and "mask_state" not in fixtures.get(f"{endpoint}_log", {})
        ):
            add_log(
                endpoint,
                fixtures,
                {
                    "mask_state": MASK_STATE.MASKED
                    if (fixtures[endpoint] != endpoint_data[endpoint])
                    else MASK_STATE.UNCHANGED
                },
            )

    # Add anonymization errors to returned dict
    if len(anonymization_errors) > 0:
        fixtures[ANONYMIZATION_ERROR_KEY] = fixtures.get(
            ANONYMIZATION_ERROR_KEY, []
        ) + list(anonymization_errors)
    return fixtures
