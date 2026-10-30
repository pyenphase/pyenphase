"""Test envoy serial number anonymization."""

import re
from collections import Counter
from copy import deepcopy as dc
from typing import Any
from unittest.mock import patch

import aiohttp
import orjson
import pytest
from aioresponses import aioresponses

from pyenphase.anonymization import SHORT_SERIAL, anonymize_serials
from pyenphase.const import (
    ANONYMIZATION_ERROR_KEY,
    DEVICE_TYPES,
    ENVOY_SERIAL,
    FIXTURE_LIST,
    MASK_STATE,
    TYPE_SERIALS,
)
from pyenphase.models.device_data_anonymize import anonymize_device_data
from pyenphase.models.ensemble_anonymize import (
    anonymize_ensemble_inventory,
    anonymize_ensemble_power,
    anonymize_ensemble_status,
    new_keys,
)
from pyenphase.models.envoy_anonymize import anonymize_info
from pyenphase.models.inventory_anonymize import anonymize_inventory
from pyenphase.models.inverter_anonymize import anonymize_inverters

from .common import (
    endpoint_fixture_file,
    endpoint_path,
    get_mock_envoy,
    load_fixture,
    load_json_fixture,
    load_json_list_fixture,
    override_mock,
    prep_envoy,
    start_7_firmware_mock,
)

ENSEMBLE_POWER_DEVICE = "devices:"


def verify_expected_type_and_http_error(test_json: Any, endpoint: str) -> None:
    """Test expected data type present with HTTP errors in endpoint_log in standard and strict mode"""
    # test with expected type and non-200 http status
    fixtures: dict[str, Any] = {endpoint: test_json, f"{endpoint}_log": {"code": 203}}
    anonymized_fixtures = anonymize_serials(fixtures)

    # In standard modde non http 200 status should return unchanged data flagged as unusable
    assert anonymized_fixtures[endpoint] == test_json
    assert ANONYMIZATION_ERROR_KEY in anonymized_fixtures
    assert (
        f"Unusable data for {endpoint}" in anonymized_fixtures[ANONYMIZATION_ERROR_KEY]
    )
    assert "mask_state" in anonymized_fixtures[f"{endpoint}_log"]
    assert anonymized_fixtures[f"{endpoint}_log"]["mask_state"] == MASK_STATE.FAILED

    # test with expected type and non-200 http status in strict mode
    fixtures = {endpoint: test_json, f"{endpoint}_log": {"code": 203}}
    anonymized_fixtures = anonymize_serials(fixtures, strict=True)

    # In strict modde non http 200 status should not data flagged as removed
    assert endpoint not in anonymized_fixtures
    assert ANONYMIZATION_ERROR_KEY in anonymized_fixtures
    assert (
        f"Unusable data for {endpoint}" in anonymized_fixtures[ANONYMIZATION_ERROR_KEY]
    )
    assert "mask_state" in anonymized_fixtures[f"{endpoint}_log"]
    assert anonymized_fixtures[f"{endpoint}_log"]["mask_state"] == MASK_STATE.REMOVED


def verify_formats(
    source: Any, endpoint: str, expected: Any, result: MASK_STATE
) -> None:
    """Test fixture data anonymization in standard and strict mode"""
    fixtures = {endpoint: source}

    # standard mode
    anonymized_fixtures = anonymize_serials(fixtures)
    assert anonymized_fixtures[endpoint] == expected
    assert anonymized_fixtures[f"{endpoint}_log"]["mask_state"] == result
    # if expected result is UNCHANGED or MASKED there should not be anynymization errors
    if result in (MASK_STATE.UNCHANGED, MASK_STATE.MASKED):
        assert (ANONYMIZATION_ERROR_KEY not in anonymized_fixtures) or (
            anonymized_fixtures[ANONYMIZATION_ERROR_KEY]
            == ["No serial numbers identified, masking not verified"]
        )
    # Otherwise there unexpected data should be flagged
    else:
        assert ANONYMIZATION_ERROR_KEY in anonymized_fixtures
        assert any(
            f"Unexpected data type for {endpoint}" in log
            for log in anonymized_fixtures[ANONYMIZATION_ERROR_KEY]
        )

    # strict mode. any failed state becomes removed
    fixtures = {endpoint: source}
    anonymized_fixtures = anonymize_serials(fixtures, strict=True)
    # if expected result is UNCHANGED or MASKED there should not be anynymization errors
    if result in (MASK_STATE.UNCHANGED, MASK_STATE.MASKED):
        assert anonymized_fixtures[f"{endpoint}_log"]["mask_state"] == result
        assert anonymized_fixtures[endpoint] == expected
        assert (ANONYMIZATION_ERROR_KEY not in anonymized_fixtures) or (
            anonymized_fixtures[ANONYMIZATION_ERROR_KEY]
            == ["No serial numbers identified, masking not verified"]
        )
    # Otherwise, in strict mode,  data should be removed
    else:
        assert (
            anonymized_fixtures[f"{endpoint}_log"]["mask_state"] == MASK_STATE.REMOVED
        )
        assert ANONYMIZATION_ERROR_KEY in anonymized_fixtures
        assert endpoint not in anonymized_fixtures
        assert any(
            f"Unexpected data type for {endpoint}" in log
            for log in anonymized_fixtures[ANONYMIZATION_ERROR_KEY]
        )


@pytest.mark.asyncio
async def test_anonymization_info() -> None:
    """Test serial anonymization for info endpoint."""
    endpoint = "/info"
    # verify DEVICE_TYPES values and TYPE_SERIALS keys match
    assert sorted(set(DEVICE_TYPES.values())) == sorted(TYPE_SERIALS)

    original_xml = "<envoy_info><device><sn>272727272727</sn><software>D8.3.6087</software></device></envoy_info>"
    original_xml_anonymized = f"<envoy_info><device><sn>{ENVOY_SERIAL}</sn><software>D8.3.6087</software></device></envoy_info>"

    # test serial detection
    serials: dict[str, Any] = {}
    test_xml: Any = dc(original_xml)
    fixtures: Any = {endpoint: test_xml}
    used_endpoint, result = anonymize_info(serials, fixtures, scan_only=True)
    assert used_endpoint == endpoint
    assert len(result) == 0
    assert "272727272727" in serials
    assert serials["272727272727"] == "ENVOY"

    # manual serial sequencing
    serials["272727272727"] = ENVOY_SERIAL

    # test serial replacement
    used_endpoint, result = anonymize_info(serials, fixtures, scan_only=False)
    assert used_endpoint == endpoint
    assert len(result) == 0
    assert fixtures[endpoint] == original_xml_anonymized

    # test mapping to unknown
    del serials["272727272727"]
    used_endpoint, result = anonymize_info(serials, fixtures, scan_only=False)
    assert used_endpoint == endpoint
    assert len(result) == 0
    assert (
        fixtures[endpoint]
        == "<envoy_info><device><sn>UNKNOWN</sn><software>D8.3.6087</software></device></envoy_info>"
    )

    # test automatic serial anonymization with various formats
    test_xml = dc(original_xml)
    for source, expected, result in (  # type: ignore
        (test_xml, original_xml_anonymized, MASK_STATE.MASKED),
        ({"<sn>": "123456</sn>"}, None, MASK_STATE.FAILED),
        (["<sn>123456</sn>"], None, MASK_STATE.FAILED),
        (1, None, MASK_STATE.FAILED),
        ("", None, MASK_STATE.FAILED),
        ([1, 2], None, MASK_STATE.FAILED),
        (
            "<envoy_info><device><nosn>1</nosn><software>D8.3.6087</software></device></envoy_info>",
            None,
            MASK_STATE.FAILED,
        ),
        (
            "<envoy_info><device><nosn> 1 </nosn><software>D8.3.6087</software></device></envoy_info>",
            None,
            MASK_STATE.FAILED,
        ),
    ):
        verify_formats(source, endpoint, expected or source, result)  # type: ignore

    # test expected data type and non-200 http status
    verify_expected_type_and_http_error("", endpoint)


@pytest.mark.asyncio
async def test_anonymization_inverters() -> None:
    """Test serial anonymization for inverters endpoint."""
    endpoint = "/api/v1/production/inverters"

    # verify DEVICE_TYPES values and TYPE_SERIALS keys match
    assert sorted(set(DEVICE_TYPES.values())) == sorted(TYPE_SERIALS)

    original_json: list[Any] = [
        {
            "serialNumber": "480000000001",
            "devType": 1,
        },
        {
            "serialNumber": "480000000002",
            "devType": 1,
        },
        {
            "serialNumber": "480000000003",
            "devType": 11,
        },
    ]

    # test serial detection
    serials: dict[str, Any] = {}
    test_json: Any = dc(original_json)
    fixtures = {endpoint: test_json}
    used_endpoint, result = anonymize_inverters(serials, fixtures, scan_only=True)

    assert used_endpoint == endpoint
    assert test_json[0]["serialNumber"] in serials
    assert test_json[1]["serialNumber"] in serials
    assert test_json[2]["serialNumber"] in serials
    assert serials[test_json[0]["serialNumber"]] == "PCU"
    assert serials[test_json[1]["serialNumber"]] == "PCU"
    assert serials[test_json[2]["serialNumber"]] == "ACB"
    assert len(result) == 0

    # manual serial assignment
    serials[test_json[0]["serialNumber"]] = "1"
    # remove second serial from found to simulate error should become UNKNOWN
    del serials[test_json[1]["serialNumber"]]
    # list for serial will not map and create error
    test_json[2]["serialNumber"] = [1, 2]

    # test serial replacement
    used_endpoint, result = anonymize_inverters(serials, fixtures, scan_only=False)
    assert used_endpoint == endpoint
    assert fixtures[endpoint][0]["serialNumber"] == "1"
    assert fixtures[endpoint][1]["serialNumber"] == "UNKNOWN"
    assert fixtures[endpoint][2]["serialNumber"] == [1, 2]
    # we should have error caused by list as serial
    assert len(result) == 1
    assert any(
        log
        == f"Error on {endpoint} TypeError(cannot use 'list' as a dict key (unhashable type: 'list'))"
        for log in result
    )

    # test automatic serial anonymization
    test_json = dc(original_json)
    original_json_anonymized: Any = dc(original_json)
    original_json_anonymized[0]["serialNumber"] = TYPE_SERIALS["PCU"]
    original_json_anonymized[1]["serialNumber"] = f"{int(TYPE_SERIALS['PCU']) + 1}"
    original_json_anonymized[2]["serialNumber"] = TYPE_SERIALS["ACB"]
    expected_json: Any = dc(original_json_anonymized)

    # first test: replace second dict by string
    test_json[2] = "482020200002"
    expected_json[2] = "482020200002"

    # second test: malformed data is returned as is
    test_json2 = dc(original_json)
    expected_json2 = dc(original_json_anonymized)
    # no serial number key
    del test_json2[0]["serialNumber"]
    del expected_json2[0]["serialNumber"]
    # devType as list should come back as unknown
    test_json2[1]["devType"] = [1, 2]
    expected_json2[1]["serialNumber"] = TYPE_SERIALS["UNKNOWN"]
    expected_json2[1]["devType"] = [1, 2]
    # test integer serial number comes back as device type
    test_json2[2]["serialNumber"] = 480000000002
    expected_json2[2]["serialNumber"] = "ACB"

    # test in standard and strict modes
    for source, expected, result in (  # type: ignore
        (dc(original_json), original_json_anonymized, MASK_STATE.MASKED),
        ({"maxReportWatts": 297}, None, MASK_STATE.FAILED),
        ("maxReportWatts: 297", None, MASK_STATE.FAILED),
        (1, None, MASK_STATE.FAILED),
        (test_json, expected_json, MASK_STATE.FAILED),
        (test_json2, expected_json2, MASK_STATE.FAILED),
        ([{"maxReportWatts": 297}], None, MASK_STATE.FAILED),
    ):
        verify_formats(source, endpoint, expected or source, result)  # type: ignore

    # test expected data type and non-200 http status
    verify_expected_type_and_http_error([], endpoint)


@pytest.mark.asyncio
async def test_anonymization_device_data() -> None:
    """Test serial anonymization for device_data endpoint."""
    endpoint = "/ivp/pdm/device_data"

    # verify DEVICE_TYPES values and TYPE_SERIALS keys match
    assert sorted(set(DEVICE_TYPES.values())) == sorted(TYPE_SERIALS)

    original_json: Any = {
        "123123123": {
            "devName": "eim",
            "sn": "202020202001EIM1",
        },
        "123123124": {
            "devName": "pcu",
            "sn": "480000000001",
        },
        "123123125": {
            "devName": "pcu",
            "sn": "480000000002",
        },
        "deviceCount": 22,
        "deviceDataLimit": 50,
    }

    # test serial detection
    serials: dict[str, Any] = {}
    test_json: Any = dc(original_json)

    fixtures = {endpoint: test_json}
    used_endpoint, result = anonymize_device_data(serials, fixtures, scan_only=True)
    assert used_endpoint == endpoint
    assert test_json["123123123"]["sn"] in serials
    assert test_json["123123124"]["sn"] in serials
    assert test_json["123123125"]["sn"] in serials
    assert serials[test_json["123123123"]["sn"]] == "EIM"
    assert serials[test_json["123123124"]["sn"]] == "PCU"
    assert serials[test_json["123123125"]["sn"]] == "PCU"
    assert len(result) == 0

    # manual serial assignment
    serials[test_json["123123123"]["sn"]] = "1"
    # without sn field it will get UNKNOWN
    del serials[test_json["123123124"]["sn"]]
    # list for serial will not map and create error
    test_json["123123125"]["sn"] = [1, 2]
    serials["123123125"] = "2"

    # test serial replacement
    used_endpoint, result = anonymize_device_data(serials, fixtures, scan_only=False)
    assert used_endpoint == endpoint
    assert fixtures[endpoint]["123123123"]["sn"] == "1"
    assert fixtures[endpoint]["123123124"]["sn"] == "UNKNOWN"
    assert fixtures[endpoint]["123123125"]["sn"] == [1, 2]
    # we should have error caused by list as serial
    assert len(result) == 1
    assert any(
        log
        == f"Error on {endpoint} TypeError(cannot use 'list' as a dict key (unhashable type: 'list'))"
        for log in result
    )

    # test automatic serial anonymization
    test_json = dc(original_json)
    original_json_anonymized: Any = dc(original_json)
    original_json_anonymized["123123123"]["sn"] = f"{ENVOY_SERIAL}EIM1"
    original_json_anonymized["123123124"]["sn"] = TYPE_SERIALS["PCU"]
    original_json_anonymized["123123125"]["sn"] = f"{int(TYPE_SERIALS['PCU']) + 1}"
    expected_json = dc(original_json_anonymized)

    # test with missing fields
    del test_json["123123123"]["devName"]
    del expected_json["123123123"]["devName"]
    # missing devName becomes UNKNOWN group
    expected_json["123123123"]["sn"] = TYPE_SERIALS["UNKNOWN"]
    # within sn it will map to UNKNOWN
    del test_json["123123124"]["sn"]
    del expected_json["123123124"]["sn"]
    # last one is now first in PCU group
    expected_json["123123125"]["sn"] = TYPE_SERIALS["PCU"]

    for source, expected, result in (  # type: ignore
        (dc(original_json), original_json_anonymized, MASK_STATE.MASKED),
        ("some text data", None, MASK_STATE.FAILED),
        (1, None, MASK_STATE.FAILED),
        ({"test": test_json}, None, MASK_STATE.FAILED),
        (test_json, expected_json, MASK_STATE.FAILED),
        ({}, None, MASK_STATE.UNCHANGED),
    ):
        verify_formats(source, endpoint, expected or source, result)  # type: ignore

    verify_expected_type_and_http_error({}, endpoint)


@pytest.mark.asyncio
async def test_anonymization_inventory() -> None:
    """Test serial anonymization for inventory endpoint."""
    endpoint = "/inventory.json?deleted=1"

    # verify DEVICE_TYPES values and TYPE_SERIALS keys match
    assert sorted(set(DEVICE_TYPES.values())) == sorted(TYPE_SERIALS)

    original_json: Any = [
        {
            "type": "PCU",
            "devices": [
                {
                    "serial_num": "482020200001",
                },
                {
                    "serial_num": "482020200002",
                },
                {
                    "serial_num": "482020200003",
                },
            ],
        },
        {
            "type": "ACB",
            "devices": [
                {
                    "serial_num": "482020200004",
                },
            ],
        },
        {
            "type": "NSRB",
            "devices": [
                {
                    "serial_num": "482020200005",
                },
            ],
        },
        {
            "type": "ESUB",
            "devices": [
                {
                    "serial_num": "482020200006",
                },
            ],
        },
        {
            "type": "NEW",
            "devices": [
                {
                    "serial_num": "482020200007",
                },
            ],
        },
    ]

    # test serial detection
    serials: dict[str, Any] = {}
    test_json: Any = dc(original_json)

    fixtures = {endpoint: test_json}
    used_endpoint, result = anonymize_inventory(serials, fixtures, scan_only=True)
    assert used_endpoint == endpoint
    assert len(result) == 0
    for i in range(3):
        assert test_json[0]["devices"][i]["serial_num"] in serials
        assert serials[test_json[0]["devices"][i]["serial_num"]] == "PCU"
    for i in range(1, 5):
        assert test_json[i]["devices"][0]["serial_num"] in serials
        assert (
            serials[test_json[i]["devices"][0]["serial_num"]]
            == ["PCU", "ACB", "NSRB", "ESUB", "NEW"][i]
        )

    # manual serial assignments
    serials[test_json[0]["devices"][0]["serial_num"]] = "1"
    # missing serial will return UNKNOWN
    del serials[test_json[0]["devices"][1]["serial_num"]]
    serials[test_json[0]["devices"][2]["serial_num"]] = "3"
    serials[test_json[1]["devices"][0]["serial_num"]] = "4"
    serials[test_json[2]["devices"][0]["serial_num"]] = "5"
    serials[test_json[3]["devices"][0]["serial_num"]] = "6"
    serials[test_json[4]["devices"][0]["serial_num"]] = "7"

    # list for serial will not map and create error
    test_json[1]["devices"][0]["serial_num"] = [1, 2]

    hold_json = dc(test_json)  # keep for next test

    # test serial replacement
    used_endpoint, result = anonymize_inventory(serials, fixtures, scan_only=False)
    assert used_endpoint == endpoint
    assert original_json[0]["devices"][0]["serial_num"] in serials
    assert fixtures[endpoint][0]["devices"][0]["serial_num"] == "1"
    assert fixtures[endpoint][0]["devices"][1]["serial_num"] == "UNKNOWN"
    assert fixtures[endpoint][0]["devices"][2]["serial_num"] == "3"
    assert fixtures[endpoint][1]["devices"][0]["serial_num"] == [1, 2]
    assert fixtures[endpoint][2]["devices"][0]["serial_num"] == "5"
    assert fixtures[endpoint][3]["devices"][0]["serial_num"] == "6"
    assert fixtures[endpoint][4]["devices"][0]["serial_num"] == "7"
    assert len(result) == 1
    assert any(
        log
        == f"Error on {endpoint} TypeError(cannot use 'list' as a dict key (unhashable type: 'list'))"
        for log in result
    )

    # test automatic serial anonymization in strict mode removes failed entries

    fixtures = {endpoint: dc(hold_json)}
    fixtures["/info"] = {}
    anonymized_fixtures = anonymize_serials(fixtures, strict=True)
    assert endpoint not in anonymized_fixtures
    assert "/info" not in anonymized_fixtures
    assert anonymized_fixtures[f"{endpoint}_log"]["mask_state"] == MASK_STATE.REMOVED
    assert anonymized_fixtures["/info_log"]["mask_state"] == MASK_STATE.REMOVED
    assert ANONYMIZATION_ERROR_KEY in anonymized_fixtures
    assert any(
        log
        == f"Error on {endpoint} TypeError(cannot use 'list' as a dict key (unhashable type: 'list'))"
        for log in anonymized_fixtures[ANONYMIZATION_ERROR_KEY]
    )
    assert any(
        log == "Unexpected data type for /info"
        for log in anonymized_fixtures[ANONYMIZATION_ERROR_KEY]
    )

    # test automatic serial anonymization in regular mode

    original_json_anonymized: Any = dc(original_json)
    original_json_anonymized[0]["devices"][0]["serial_num"] = TYPE_SERIALS["PCU"]
    original_json_anonymized[0]["devices"][1]["serial_num"] = (
        f"{int(TYPE_SERIALS['PCU']) + 1}"
    )
    original_json_anonymized[0]["devices"][2]["serial_num"] = (
        f"{int(TYPE_SERIALS['PCU']) + 2}"
    )
    original_json_anonymized[1]["devices"][0]["serial_num"] = TYPE_SERIALS["ACB"]
    original_json_anonymized[2]["devices"][0]["serial_num"] = TYPE_SERIALS["NSRB"]
    original_json_anonymized[3]["devices"][0]["serial_num"] = TYPE_SERIALS["ESUB"]
    original_json_anonymized[4]["devices"][0]["serial_num"] = TYPE_SERIALS["UNKNOWN"]

    test_json = dc(original_json)
    expected_json: Any = dc(original_json_anonymized)

    for source, expected, result in (  # type: ignore
        (dc(test_json), expected_json, MASK_STATE.MASKED),
        ("some text data", None, MASK_STATE.FAILED),
        (1, None, MASK_STATE.FAILED),
        ({"test": test_json}, None, MASK_STATE.FAILED),
        ([test_json], None, MASK_STATE.FAILED),
        ([], None, MASK_STATE.UNCHANGED),
    ):
        verify_formats(source, endpoint, expected or source, result)  # type: ignore

    del test_json[0]["devices"][1]["serial_num"]
    # missing serial_num will sho as UNKNOWN type
    del expected_json[0]["devices"][1]["serial_num"]
    # assignemt shift one with previous moving to unknown
    expected_json[0]["devices"][2]["serial_num"] = f"{int(TYPE_SERIALS['PCU']) + 1}"
    del test_json[1]["devices"]
    del expected_json[1]["devices"]
    del test_json[2]["type"]
    del expected_json[2]["type"]
    # mssining serial no in unknown
    expected_json[2]["devices"][0]["serial_num"] = TYPE_SERIALS["UNKNOWN"]
    test_json[4]["type"] = [1, 2]
    expected_json[4]["type"] = [1, 2]
    # existing unknown moves 1 number up
    expected_json[4]["devices"][0]["serial_num"] = f"{int(TYPE_SERIALS['UNKNOWN']) + 1}"

    fixtures = {endpoint: test_json}
    anonymized_fixtures = anonymize_serials(fixtures)
    assert anonymized_fixtures[endpoint] == expected_json
    assert ANONYMIZATION_ERROR_KEY in anonymized_fixtures

    # test with expected type and non-200 http status
    verify_expected_type_and_http_error([], endpoint)

    # some wider test for anonymization code body

    # test automatic serial anonymization  errors in strict mode removes entries
    fixtures = {endpoint: dc(original_json)}
    with (
        patch("pyenphase.anonymization.TYPE_SERIALS", {"PCU": "1", "ACB": 2}),
        patch(
            "pyenphase.anonymization.re.compile",
            side_effect=re.error("Test failed compile"),
        ),
    ):
        anonymized_fixtures = anonymize_serials(fixtures, strict=True)
    assert endpoint not in anonymized_fixtures
    assert f"{endpoint}_log" in anonymized_fixtures
    assert "mask_state" in anonymized_fixtures[f"{endpoint}_log"]
    assert anonymized_fixtures[f"{endpoint}_log"]["mask_state"] == MASK_STATE.REMOVED
    assert ANONYMIZATION_ERROR_KEY in anonymized_fixtures
    # Sequencing errors in strict mode pops entry before regex compile so only 1 error
    assert anonymized_fixtures[ANONYMIZATION_ERROR_KEY] == [
        "Error during serial sequencing KeyError(UNKNOWN)"
    ]

    # test strict mode with regex compile errors removes entries
    fixtures = {endpoint: dc(original_json)}
    with (
        patch(
            "pyenphase.anonymization.re.compile",
            side_effect=re.error("Test failed compile"),
        ),
    ):
        anonymized_fixtures = anonymize_serials(fixtures, strict=True)
    assert endpoint not in anonymized_fixtures
    assert f"{endpoint}_log" in anonymized_fixtures
    assert "mask_state" in anonymized_fixtures[f"{endpoint}_log"]
    assert anonymized_fixtures[f"{endpoint}_log"]["mask_state"] == MASK_STATE.REMOVED
    assert ANONYMIZATION_ERROR_KEY in anonymized_fixtures
    assert anonymized_fixtures[ANONYMIZATION_ERROR_KEY] == [
        f"Error during serial replacement for regex compile {re.error.__name__}"
    ]

    # test automatic serial anonymization in regular mode with serial sequencing error
    fixtures = {endpoint: dc(original_json)}
    with patch("pyenphase.anonymization.TYPE_SERIALS", {"PCU": "1", "ACB": 2}):
        anonymized_fixtures = anonymize_serials(fixtures)
    assert endpoint in anonymized_fixtures
    assert f"{endpoint}_log" in anonymized_fixtures
    assert "mask_state" in anonymized_fixtures[f"{endpoint}_log"]
    assert anonymized_fixtures[f"{endpoint}_log"]["mask_state"] == MASK_STATE.FAILED
    assert ANONYMIZATION_ERROR_KEY in anonymized_fixtures
    assert anonymized_fixtures[ANONYMIZATION_ERROR_KEY] == [
        "Error during serial sequencing KeyError(UNKNOWN)"
    ]

    # test regular mode with regex compile errors flags entries as failed
    with patch(
        "pyenphase.anonymization.re.compile",
        side_effect=re.error("Test failed compile"),
    ):
        anonymized_fixtures = anonymize_serials(fixtures)
    assert endpoint in anonymized_fixtures
    assert f"{endpoint}_log" in anonymized_fixtures
    assert "mask_state" in anonymized_fixtures[f"{endpoint}_log"]
    assert anonymized_fixtures[f"{endpoint}_log"]["mask_state"] == MASK_STATE.FAILED
    assert ANONYMIZATION_ERROR_KEY in anonymized_fixtures
    assert anonymized_fixtures[ANONYMIZATION_ERROR_KEY] == [
        f"Error during serial replacement for regex compile {re.error.__name__}"
    ]
    # test regular mode with sequencing and regex compile errors flags entries as failed
    with (
        patch("pyenphase.anonymization.TYPE_SERIALS", {"PCU": "1", "ACB": 2}),
        patch(
            "pyenphase.anonymization.re.compile",
            side_effect=re.error("Test failed compile"),
        ),
    ):
        anonymized_fixtures = anonymize_serials(fixtures)
    assert endpoint in anonymized_fixtures
    assert f"{endpoint}_log" in anonymized_fixtures
    assert "mask_state" in anonymized_fixtures[f"{endpoint}_log"]
    assert anonymized_fixtures[f"{endpoint}_log"]["mask_state"] == MASK_STATE.FAILED
    assert ANONYMIZATION_ERROR_KEY in anonymized_fixtures
    assert any(
        log == f"Error during serial replacement for regex compile {re.error.__name__}"
        for log in anonymized_fixtures[ANONYMIZATION_ERROR_KEY]
    )
    assert any(
        log == "Error during serial sequencing KeyError(UNKNOWN)"
        for log in anonymized_fixtures[ANONYMIZATION_ERROR_KEY]
    )


@pytest.mark.asyncio
async def test_anonymization_ensemble_power() -> None:
    """Test serial anonymization for ensemble power endpoint."""
    endpoint = "/ivp/ensemble/power"

    # verify DEVICE_TYPES values and TYPE_SERIALS keys match
    assert sorted(set(DEVICE_TYPES.values())) == sorted(TYPE_SERIALS)

    original_json: Any = {
        ENSEMBLE_POWER_DEVICE: [
            {
                "serial_num": "492000000111",
                "real_power_mw": 8000,
            },
            {
                "serial_num": "492000000123",
                "real_power_mw": 8000,
            },
            {
                "serial_num": "492000000125",
                "real_power_mw": 8000,
            },
        ]
    }

    # test serial detection
    serials: dict[str, Any] = {}
    test_json: Any = dc(original_json)

    # list for serial will not map and create error
    test_json[ENSEMBLE_POWER_DEVICE][0]["serial_num"] = [1, 2]

    fixtures = {endpoint: test_json}
    used_endpoint, result = anonymize_ensemble_power(serials, fixtures, scan_only=True)
    assert used_endpoint == endpoint
    assert "492000000111" not in serials
    assert test_json[ENSEMBLE_POWER_DEVICE][1]["serial_num"] in serials
    assert test_json[ENSEMBLE_POWER_DEVICE][2]["serial_num"] in serials
    assert serials[test_json[ENSEMBLE_POWER_DEVICE][1]["serial_num"]] == "ENCHARGE"
    assert serials[test_json[ENSEMBLE_POWER_DEVICE][2]["serial_num"]] == "ENCHARGE"
    assert len(result) == 1
    assert any(
        log
        == f"Error on {endpoint} TypeError(cannot use 'list' as a dict key (unhashable type: 'list'))"
        for log in result
    )

    # manual serial assignments
    # without serial_num is will return UNKNOWN
    # without serial assignment device type in serials from detection will be used
    del serials[test_json[ENSEMBLE_POWER_DEVICE][1]["serial_num"]]

    # test serial replacement
    used_endpoint, result = anonymize_ensemble_power(serials, fixtures, scan_only=False)
    assert used_endpoint == endpoint
    assert fixtures[endpoint][ENSEMBLE_POWER_DEVICE][0]["serial_num"] == [1, 2]
    assert fixtures[endpoint][ENSEMBLE_POWER_DEVICE][1]["serial_num"] == "UNKNOWN"
    assert fixtures[endpoint][ENSEMBLE_POWER_DEVICE][2]["serial_num"] == "ENCHARGE"
    assert len(result) == 1
    assert any(
        log
        == f"Error on {endpoint} TypeError(cannot use 'list' as a dict key (unhashable type: 'list'))"
        for log in result
    )

    # test automatic serial anonymization

    original_json_anonymized: Any = dc(original_json)
    original_json_anonymized[ENSEMBLE_POWER_DEVICE][0]["serial_num"] = TYPE_SERIALS[
        "ENCHARGE"
    ]
    original_json_anonymized[ENSEMBLE_POWER_DEVICE][1]["serial_num"] = (
        f"{int(TYPE_SERIALS['ENCHARGE']) + 1}"
    )
    original_json_anonymized[ENSEMBLE_POWER_DEVICE][2]["serial_num"] = (
        f"{int(TYPE_SERIALS['ENCHARGE']) + 2}"
    )

    test_json = dc(original_json)
    expected_json = dc(original_json_anonymized)

    # second test with incorrect formats
    test_json2 = dc(original_json)
    test_json2[ENSEMBLE_POWER_DEVICE].extend(
        [
            [],
            "Hello world",
            {
                "serial_num": 492000000130,
            },
            {
                "serial_num": "",
            },
            {
                "serial_num": None,
            },
            {
                "SERIAL_NUM": "as good as missing test",
            },
        ]
    )

    expected_json2 = dc(original_json_anonymized)
    expected_json2[ENSEMBLE_POWER_DEVICE].append([])
    for i in range(4, 9):
        expected_json2[ENSEMBLE_POWER_DEVICE].append(
            dc(test_json2[ENSEMBLE_POWER_DEVICE][i])
        )
    # non str serials should show device type in serial
    for i in range(5, 8):
        expected_json2[ENSEMBLE_POWER_DEVICE][i]["serial_num"] = "ENCHARGE"

    for source, expected, result in (  # type: ignore
        (test_json, expected_json, MASK_STATE.MASKED),
        ("some text data", None, MASK_STATE.FAILED),
        (1, None, MASK_STATE.FAILED),
        (["hello", "world"], None, MASK_STATE.FAILED),
        (test_json2, expected_json2, MASK_STATE.FAILED),
    ):
        verify_formats(source, endpoint, expected or source, result)  # type: ignore

    # test with expected type and non-200 http status
    verify_expected_type_and_http_error([], endpoint)


@pytest.mark.asyncio
async def test_anonymization_ensemble_inventory() -> None:
    """Test serial anonymization for ensemble inventory endpoint."""
    endpoint = "/ivp/ensemble/inventory"

    # verify DEVICE_TYPES values and TYPE_SERIALS keys match
    assert sorted(set(DEVICE_TYPES.values())) == sorted(TYPE_SERIALS)

    original_json: Any = [
        {
            "type": "ENCHARGE",
            "devices": [
                {
                    "serial_num": "492000000111",
                },
                {
                    "serial_num": "492000000112",
                },
                {
                    "serial_num": "492000000113",
                },
            ],
        },
        {
            "type": "ENPOWER",
            "devices": [
                {
                    "serial_num": "492000000200",
                },
            ],
        },
        {
            "type": "COLLAR",
            "devices": [
                {
                    "serial_num": "492000000300",
                },
            ],
        },
        {
            "type": "NEW",
            "devices": [
                {
                    "serial_num": "492000000400",
                },
            ],
        },
    ]

    # test serial detection
    serials: dict[str, Any] = {}
    test_json: Any = dc(original_json)

    # list for serial will not map and create error
    test_json[0]["devices"][2]["serial_num"] = [1, 2]

    fixtures = {endpoint: test_json}
    used_endpoint, result = anonymize_ensemble_inventory(
        serials, fixtures, scan_only=True
    )
    assert used_endpoint == endpoint
    assert test_json[0]["devices"][0]["serial_num"] in serials
    assert test_json[0]["devices"][1]["serial_num"] in serials
    assert "492000000113" not in serials
    assert test_json[1]["devices"][0]["serial_num"] in serials
    assert test_json[2]["devices"][0]["serial_num"] in serials
    assert test_json[3]["devices"][0]["serial_num"] in serials

    assert serials[test_json[0]["devices"][0]["serial_num"]] == "ENCHARGE"
    assert serials[test_json[0]["devices"][1]["serial_num"]] == "ENCHARGE"
    assert serials[test_json[0]["devices"][0]["serial_num"]] == "ENCHARGE"
    assert serials[test_json[1]["devices"][0]["serial_num"]] == "ENPOWER"
    assert serials[test_json[2]["devices"][0]["serial_num"]] == "COLLAR"
    assert serials[test_json[3]["devices"][0]["serial_num"]] == "NEW"

    assert len(result) == 1
    assert any(
        log
        == f"Error on {endpoint} TypeError(cannot use 'list' as a dict key (unhashable type: 'list'))"
        for log in result
    )

    # manual serial assignments
    serials[test_json[0]["devices"][0]["serial_num"]] = "1"
    # without serial_num is will return UNKNOWN
    del serials[test_json[0]["devices"][1]["serial_num"]]
    serials[test_json[1]["devices"][0]["serial_num"]] = "4"
    serials[test_json[2]["devices"][0]["serial_num"]] = "5"
    serials[test_json[3]["devices"][0]["serial_num"]] = "6"

    # test serial replacement
    used_endpoint, result = anonymize_ensemble_inventory(
        serials, fixtures, scan_only=False
    )
    assert used_endpoint == endpoint
    assert fixtures[endpoint][0]["devices"][0]["serial_num"] == "1"
    assert fixtures[endpoint][0]["devices"][1]["serial_num"] == "UNKNOWN"
    assert fixtures[endpoint][0]["devices"][2]["serial_num"] == [1, 2]
    assert fixtures[endpoint][1]["devices"][0]["serial_num"] == "4"
    assert fixtures[endpoint][2]["devices"][0]["serial_num"] == "5"
    assert fixtures[endpoint][3]["devices"][0]["serial_num"] == "6"
    assert len(result) == 1
    assert any(
        log
        == f"Error on {endpoint} TypeError(cannot use 'list' as a dict key (unhashable type: 'list'))"
        for log in result
    )

    # test automatic serial anonymization

    original_json_anonymized: Any = dc(original_json)
    original_json_anonymized[0]["devices"][0]["serial_num"] = TYPE_SERIALS["ENCHARGE"]
    original_json_anonymized[0]["devices"][1]["serial_num"] = (
        f"{int(TYPE_SERIALS['ENCHARGE']) + 1}"
    )
    original_json_anonymized[0]["devices"][2]["serial_num"] = (
        f"{int(TYPE_SERIALS['ENCHARGE']) + 2}"
    )
    original_json_anonymized[1]["devices"][0]["serial_num"] = TYPE_SERIALS["ENPOWER"]
    original_json_anonymized[2]["devices"][0]["serial_num"] = TYPE_SERIALS["COLLAR"]
    original_json_anonymized[3]["devices"][0]["serial_num"] = TYPE_SERIALS["UNKNOWN"]

    test_json = dc(original_json)
    expected_json = dc(original_json_anonymized)

    test_json2 = dc(original_json)
    test_json2.extend(
        [
            {},
            {
                "type": "NEW",
            },
            {
                "type": "NEW",
                "devices": {
                    "serial_num": "492000000700",
                },
            },
            {
                "type": "NEW",
                "devices": [
                    "serial_num: 492000000800",
                ],
            },
            {
                "type": "NEW",
                "devices": [
                    {
                        "SERIAL_NUM": "492000000900",
                    },
                ],
            },
            {
                "type": "NEW",
                "devices": [
                    {
                        "serial_num": 492000001000,
                    },
                ],
            },
            {
                "type": "NEW",
                "devices": [
                    {
                        "serial_num": None,
                    },
                ],
            },
            {
                "type": "NEW",
                "devices": [
                    {
                        "serial_num": "",
                    },
                ],
            },
        ]
    )
    expected_json2 = dc(original_json_anonymized)
    for i in range(4, 12):
        expected_json2.append(dc(test_json2[i]))
    for i in range(9, 12):
        expected_json2[i]["devices"][0]["serial_num"] = "UNKNOWN"

    for source, expected, result in (  # type: ignore
        (test_json, expected_json, MASK_STATE.MASKED),
        ("some text data", None, MASK_STATE.FAILED),
        (1, None, MASK_STATE.FAILED),
        ({"hello": "world"}, None, MASK_STATE.FAILED),
        (test_json2, expected_json2, MASK_STATE.FAILED),
    ):
        verify_formats(source, endpoint, expected or source, result)  # type: ignore

    # test with expected type and non-200 http status
    verify_expected_type_and_http_error([], endpoint)


@pytest.mark.asyncio
async def test_ensemble_status_new_keys() -> None:
    """Test serial anonymization for info endpoint."""
    serials: dict[str, Any] = {}
    target: dict[str, Any] = {}

    mask_with: str = "test"
    serials = {
        "123456789012": "1",
        "234567890123": "PCU",
        "36789012": "PCU",
        "123456": "4",
        "456789012345": "PCU",
    }
    target = {
        "123456789012": "original1",
        "234567890123": "originalPCU1",
        "36789012": "originalPCU2",
        "123456": "original4",
        "6789012": "original5",
        "567890123456": "original6",
        "456789012345": "original7",
    }
    expected_target = {
        "1": "original1",
        "PCU1": "originalPCU1",
        "PCU2": "originalPCU2",
        "4": "original4",
        "test4": "original5",
        "test5": "original6",
        "PCU4": "original7",
    }
    new_keys(target, mask_with, serials)
    assert target == expected_target


@pytest.mark.asyncio
async def test_anonymization_ensemble_status() -> None:
    """Test serial anonymization for ensemble status endpoint."""
    endpoint = "/ivp/ensemble/status"

    # verify DEVICE_TYPES values and TYPE_SERIALS keys match
    assert sorted(set(DEVICE_TYPES.values())) == sorted(TYPE_SERIALS)

    original_json: Any = {
        "inventory": {
            "serial_nums": {
                "482000020939": {
                    "device_type": 27,
                    "device_id": "482000020939",
                    "submodules": {},
                },
                "482000020940": {
                    "device_type": 27,
                    "device_id": "482000020940",
                    "submodules": {
                        "482000020941": {
                            "device_type": 31,
                        }
                    },
                },
                "482000020942": {
                    "device_type": 27,
                    "device_id": "482000020943",
                    "submodules": {
                        "482000020944": {
                            "device_type": 31,
                        },
                        "482000020945": {
                            "device_type": 31,
                        },
                    },
                },
            }
        },
        "secctrl": {
            "shutdown": False,
        },
    }

    # test serial detection
    serials: dict[str, Any] = {}
    test_json: Any = dc(original_json)

    # add serials to test multiple devtype and blank serial replacements
    test_json["inventory"]["serial_nums"].update(
        {
            "482000020946": {
                "device_type": 27,
                "device_id": "482000020946",
                "submodules": {
                    "482000020947": {
                        "device_type": 20,
                    }
                },
            },
            "482000020948": {
                "device_type": 27,
                "device_id": "482000020948",
                "submodules": {
                    "482000020949": {
                        "device_type": 20,
                    },
                    "482000020950": {
                        "device_type": 20,
                    },
                },
            },
            "482000020951": {
                "device_type": 27,
                "device_id": "482000020951",
                "submodules": {
                    "482000020952": {
                        "device_type": 20,
                    },
                    "482000020953": {
                        "device_type": 20,
                    },
                },
            },
        }
    )
    fixtures = {endpoint: test_json}
    status_serials = list(test_json["inventory"]["serial_nums"])
    status_sub_serials = [
        sub_serial
        for device in test_json["inventory"]["serial_nums"].values()
        for sub_serial in device.get("submodules", {})
    ]
    used_endpoint, result = anonymize_ensemble_status(serials, fixtures, scan_only=True)
    assert used_endpoint == endpoint
    for serial in status_serials:
        assert serial in serials
        assert serials[serial] == DEVICE_TYPES[27]
        assert test_json["inventory"]["serial_nums"][serial]["device_id"] in serials
        assert (
            serials[test_json["inventory"]["serial_nums"][serial]["device_id"]]
            == DEVICE_TYPES[27]
        )
    for serial in status_sub_serials:
        assert serial in serials
        assert serials[serial] in ("ESUB", "UNKNOWN")
    assert len(result) == 0

    # manual serial assignments

    for index, key in enumerate(serials):
        serials[key] = str(index + 1)
    # without serial_num is will return fallback masks
    # as serials are dict keys in this case
    del serials["482000020939"]
    del serials["482000020944"]
    del serials["482000020945"]
    # Leave some at their original type to test
    serials["482000020947"] = "MULTIPLE"
    serials["482000020948"] = "MULTIPLE"
    serials["482000020949"] = "MULTIPLE"
    serials["482000020950"] = "MULTIPLE"
    # test blank serial replacements
    serials["482000020951"] = ""
    serials["482000020952"] = ""
    serials["482000020953"] = ""

    # test serial replacement
    used_endpoint, result = anonymize_ensemble_status(
        serials, fixtures, scan_only=False
    )
    assert used_endpoint == endpoint
    # first had serials removed from serials, should show fallback serials
    assert test_json["inventory"]["serial_nums"]["SERIAL0"]["device_id"] == "UNKNOWN"
    assert test_json["inventory"]["serial_nums"]["2"]["device_id"] == "2"
    # last entry has different serial in ke and device_id field for testing
    assert test_json["inventory"]["serial_nums"]["4"]["device_id"] == "5"
    # last entries had serials removed from serials, should show fallback serials
    assert test_json["inventory"]["serial_nums"]["4"]["submodules"]["SUBSERIAL20"]
    assert test_json["inventory"]["serial_nums"]["4"]["submodules"]["SUBSERIAL21"]
    assert test_json["inventory"]["serial_nums"]["8"]["submodules"]["MULTIPLE5"]
    assert test_json["inventory"]["serial_nums"]["MULTIPLE6"]["device_id"] == "MULTIPLE"
    assert test_json["inventory"]["serial_nums"]["MULTIPLE6"]["submodules"]["MULTIPLE7"]
    assert test_json["inventory"]["serial_nums"]["MULTIPLE6"]["submodules"]["MULTIPLE8"]
    assert test_json["inventory"]["serial_nums"]["BLANK9"]["device_id"] == ""
    assert test_json["inventory"]["serial_nums"]["BLANK9"]["submodules"]["BLANK10"]
    assert test_json["inventory"]["serial_nums"]["BLANK9"]["submodules"]["BLANK11"]
    # should not have errors
    assert len(result) == 0

    # test automatic serial anonymization

    original_json_anonymized: Any = {
        "inventory": {
            "serial_nums": {
                "510000000001": {
                    "device_type": 27,
                    "device_id": "510000000001",
                    "submodules": {},
                },
                "510000000002": {
                    "device_type": 27,
                    "device_id": "510000000002",
                    "submodules": {
                        "990000000001": {
                            "device_type": 31,
                        }
                    },
                },
                "510000000003": {
                    "device_type": 27,
                    "device_id": "510000000004",
                    "submodules": {
                        "990000000002": {
                            "device_type": 31,
                        },
                        "990000000003": {
                            "device_type": 31,
                        },
                    },
                },
            }
        },
        "secctrl": {
            "shutdown": False,
        },
    }
    test_json = dc(original_json)
    expected_json = dc(original_json_anonymized)

    test_json2 = dc(test_json)
    expected_json2 = dc(original_json_anonymized)
    # add malformed dict
    test_json2["inventory"]["serial_nums"].update(
        {
            "482000020946": [
                "device_type",
                27,
                "device_id",
                "482000020947",
                {
                    "submodules": {
                        "482000020948": {
                            "device_type": 31,
                        }
                    }
                },
            ]
        }
    )
    expected_json2["inventory"]["serial_nums"].update(
        {
            "990000000004": [
                "device_type",
                27,
                "device_id",
                "482000020947",
                {
                    "submodules": {
                        "482000020948": {
                            "device_type": 31,
                        }
                    }
                },
            ],
        }
    )

    test_json3 = dc(test_json2)
    test_json3["inventory"]["serial_nums"].update(
        {
            "482000020949": {
                "DEVICE_TYPE": 27,
            },
            "482000020950": {
                "device_type": 27,
                "device_id": "482000020950",
                "submodules": {
                    "482000020951": {
                        "device_TYPE": 31,
                    }
                },
            },
        }
    )

    expected_json3 = dc(expected_json2)
    expected_json3["inventory"]["serial_nums"].update(
        {
            "990000000005": {
                "DEVICE_TYPE": 27,
            },
            "510000000005": {
                "device_type": 27,
                "device_id": "510000000005",
                "submodules": {
                    "990000000006": {
                        "device_TYPE": 31,
                    }
                },
            },
        }
    )

    test_json4 = dc(test_json3)
    test_json4["inventory"]["serial_nums"].update(
        {
            "482000020952": {
                "device_type": 27,
                "device_id": [2, 7],
                "submodules": {
                    "482000020953": {
                        "device_TYPE": [2, 7],
                    }
                },
            },
            "482000020954": {
                "device_type": 27,
                "device_id": "482000020954",
                "submodules": {
                    "482000020955": {
                        "device_type": [2, 7],
                    }
                },
            },
            "482000020956": {
                "device_type": 27,
                "device_id": "482000020956",
                "id": 6,
                "submodules": {
                    "482000020957": [
                        "device_type",
                        [2, 7],
                    ]
                },
            },
            "482000020957": {
                "device_type": 27,
                "device_id": "482000020957",
                "id": 6,
                "submodules": {
                    "482000020957": [1, 2],
                },
            },
        },
    )
    expected_json4 = dc(expected_json3)
    expected_json4["inventory"]["serial_nums"].update(
        {
            "510000000006": {
                "device_type": 27,
                "device_id": [2, 7],
                "submodules": {"990000000007": {"device_TYPE": [2, 7]}},
            },
            "510000000007": {
                "device_type": 27,
                "device_id": "510000000007",
                "submodules": {"990000000008": {"device_type": [2, 7]}},
            },
            "510000000008": {
                "device_type": 27,
                "device_id": "510000000008",
                "id": 6,
                "submodules": {"990000000009": ["device_type", [2, 7]]},
            },
            "990000000009": {
                "device_type": 27,
                "device_id": "990000000009",
                "id": 6,
                "submodules": {"990000000009": [1, 2]},
            },
        }
    )

    for source, expected, result in (  # type: ignore
        (test_json, expected_json, MASK_STATE.MASKED),
        ("some text data", None, MASK_STATE.FAILED),
        (1, None, MASK_STATE.FAILED),
        ({"hello": "world"}, None, MASK_STATE.FAILED),
        (test_json2, expected_json2, MASK_STATE.FAILED),
        (test_json3, expected_json3, MASK_STATE.FAILED),
        (test_json4, expected_json4, MASK_STATE.FAILED),
    ):
        verify_formats(source, endpoint, expected or source, result)  # type: ignore

    # test with expected type and non-200 http status
    verify_expected_type_and_http_error({}, endpoint)


PATCHED_SERIALS = {
    "PCU": "101000000001",
    "ACB": "201000000001",
    "ENCHARGE": "301000000001",
    "ENPOWER": "401000000001",
    "COLLAR": "511000000001",
    "C6 COMBINER CONTROLLER": "521000000001",
    "C6 RGM": "531000000001",
    "NSRB": "611000000001",
    "ESUB": "621000000001",
    "ENCH_PCU": "630000000001",
    "ENCH_BMU": "640000000001",
    "UNKNOWN": "991000000001",
}
PATCHED_ENVOY_SERIAL = "923456789012"


@patch("pyenphase.anonymization.TYPE_SERIALS", PATCHED_SERIALS)
@patch("pyenphase.anonymization.ENVOY_SERIAL", PATCHED_ENVOY_SERIAL)
@pytest.mark.parametrize(
    ("version", "exclude"),
    [
        ("8.3.5169_ACB_inventory", ["/ivp/ensemble/inventory"]),
        ("8.3.5169_with_generator", []),
        ("8.3.1598_collar", ["/ivp/pdm/device_data", "/inventory.json?deleted=1"]),
    ],
    ids=[
        "8.3.5169_ACB_inventory",
        "8.3.5169_with_generator",
        "8.3.1598_collar",
    ],
)
@pytest.mark.asyncio
async def test_anonymization(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    exclude: list[str],  # exclude from fixture tests
) -> None:
    """Test integrated anonimyzation."""
    start_7_firmware_mock(mock_aioresponse)
    files = await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    envoy = await get_mock_envoy(test_client_session)
    full_host = endpoint_path(version, envoy.host)

    # verify DEVICE_TYPES values and TYPE_SERIALS keys match
    assert sorted(set(DEVICE_TYPES.values())) == sorted(TYPE_SERIALS)

    # test fixtures_collection method with serial anonymization
    info_xml = "<envoy_info><device><sn>210987654321</sn><software>D8.3.6087</software></device>210987654321</envoy_info>"
    override_mock(
        mock_aioresponse, "get", f"{full_host}/info", body=info_xml, repeat=True
    )

    # and endpoint not in known anonimyzed set and containing known serial
    mock_aioresponse.get(
        f"{full_host}/my_endpoint",
        payload={"test": "this is the envoy serial '210987654321!"},
        status=200,
        repeat=True,
    )

    # obtain fixtures_collection without serial anonymization
    fixtures = await envoy.fixture_collection(
        additional_endpoints=["/my_endpoint"], mask_serials=False
    )

    # map endpoints to fixture file
    endpoint_to_fixture_file = {
        endpoint: endpoint_fixture_file(endpoint) for endpoint in FIXTURE_LIST
    }

    # validate all fixture logs are created
    assert fixtures
    assert "collection_aborted_log" not in fixtures
    anonymized_fixtures = anonymize_serials(fixtures)

    # verify all endpoints that don't contain serials
    for endpoint, file in endpoint_to_fixture_file.items():
        if (
            endpoint
            not in (
                "/info",
                "/api/v1/production/inverters",
                "/ivp/pdm/device_data",
                "/ivp/ensemble/inventory",
                "/ivp/ensemble/power",
                "/ivp/ensemble/status",
                "/inventory.json?deleted=1",
            )
            and endpoint not in exclude
            and file in files
        ):
            try:
                content = await load_json_fixture(version, file)
                assert anonymized_fixtures[endpoint] == content
            except orjson.JSONDecodeError:
                string_content = await load_fixture(version, file)
                string_content = string_content.replace("\n", "")
                assert anonymized_fixtures[endpoint] == string_content

    # verify endpoints with serial anonimization
    info_xml_anonymized = f"<envoy_info><device><sn>{PATCHED_ENVOY_SERIAL}</sn><software>D8.3.6087</software></device>210987654321</envoy_info>"
    endpoint = "/info"
    assert endpoint in anonymized_fixtures
    assert anonymized_fixtures["/info"] == info_xml_anonymized

    endpoint = "/api/v1/production/inverters"
    if endpoint not in exclude:
        assert endpoint in anonymized_fixtures
        content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
        assert len(anonymized_fixtures[endpoint]) == len(content)
        assert not (
            (len(anonymized_fixtures[endpoint]) > 0)
            ^ (
                anonymized_fixtures[f"{endpoint}_log"]["mask_state"]
                in (MASK_STATE.MASKED, MASK_STATE.UNCHANGED)
            )
        )
        for inverter in anonymized_fixtures[endpoint]:
            sn_start = PATCHED_SERIALS[DEVICE_TYPES[inverter["devType"]]]
            assert sn_start <= inverter["serialNumber"] < str(int(sn_start) + 99)

    # verify pdm devices inventory serial anonymization
    endpoint = "/ivp/pdm/device_data"
    if endpoint not in exclude:
        assert endpoint in anonymized_fixtures
        content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
        assert len(anonymized_fixtures[endpoint]) == len(content)
        # ^:  one of two true, not both true or both false
        assert not (
            (len(anonymized_fixtures[endpoint]) > 0)
            ^ (
                anonymized_fixtures[f"{endpoint}_log"]["mask_state"]
                in (MASK_STATE.MASKED, MASK_STATE.UNCHANGED)
            )
        )
        for id in (pdm := anonymized_fixtures[endpoint]):
            if id not in ("deviceCount", "deviceDataLimit"):
                sn = pdm[id]["sn"]
                if pdm[id]["devName"].upper() == "EIM":
                    assert f"{PATCHED_ENVOY_SERIAL}EIM" in sn
                else:
                    sn_start = PATCHED_SERIALS[pdm[id]["devName"].upper()]
                    assert sn_start <= sn < str(int(sn_start) + 99)

    # verify ensemble inventory serial anonymization
    endpoint = "/ivp/ensemble/inventory"
    if endpoint not in exclude:
        content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
        assert len(anonymized_fixtures[endpoint]) == len(content)
        assert not (
            (len(anonymized_fixtures[endpoint]) > 0)
            ^ (
                anonymized_fixtures[f"{endpoint}_log"]["mask_state"]
                in (MASK_STATE.MASKED, MASK_STATE.UNCHANGED)
            )
        )
        for inventory_type in anonymized_fixtures[endpoint]:
            dev_type = inventory_type["type"]
            sn_start = PATCHED_SERIALS[dev_type.upper()]
            for device in inventory_type["devices"]:
                assert sn_start <= device["serial_num"] < str(int(sn_start) + 99)

    # verify ensemble power serial anonymization
    endpoint = "/ivp/ensemble/power"
    if endpoint not in exclude:
        content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
        assert len(anonymized_fixtures[endpoint]) == len(content)
        assert not (
            (len(anonymized_fixtures[endpoint]) > 0)
            ^ (
                anonymized_fixtures[f"{endpoint}_log"]["mask_state"]
                in (MASK_STATE.MASKED, MASK_STATE.UNCHANGED)
            )
        )
        for device in anonymized_fixtures[endpoint][ENSEMBLE_POWER_DEVICE]:
            sn_start = PATCHED_SERIALS["ENCHARGE"]
            assert sn_start <= device["serial_num"] < str(int(sn_start) + 99)

    # verify inventory serial anonymization
    endpoint = "/inventory.json?deleted=1"
    if endpoint not in exclude:
        content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
        assert len(anonymized_fixtures[endpoint]) == len(content)
        assert not (
            (len(anonymized_fixtures[endpoint]) > 0)
            ^ (
                anonymized_fixtures[f"{endpoint}_log"]["mask_state"]
                in (MASK_STATE.MASKED, MASK_STATE.UNCHANGED)
            )
        )
        for inventory_type in anonymized_fixtures[endpoint]:
            dev_type = inventory_type["type"]
            sn_start = PATCHED_SERIALS[dev_type.upper()]
            for device in inventory_type["devices"]:
                assert sn_start <= device["serial_num"] < str(int(sn_start) + 99)

    # verify ensemble status serial anonymization
    endpoint = "/ivp/ensemble/status"
    if endpoint not in exclude:
        content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
        assert len(anonymized_fixtures[endpoint]) == len(content)
        assert not (
            (len(anonymized_fixtures[endpoint]) > 0)
            ^ (
                anonymized_fixtures[f"{endpoint}_log"]["mask_state"]
                in (MASK_STATE.MASKED, MASK_STATE.UNCHANGED)
            )
        )
        for serial_num, device in anonymized_fixtures[endpoint]["inventory"][
            "serial_nums"
        ].items():
            dev_type = DEVICE_TYPES.get(device["device_type"], "UNKNOWN")
            sn_start = PATCHED_SERIALS[dev_type.upper()]
            assert sn_start <= serial_num < str(int(sn_start) + 99)
            assert sn_start <= device["device_id"] < str(int(sn_start) + 99)
            for sub_serial, sub_device in device["submodules"].items():
                subdev_type = DEVICE_TYPES.get(sub_device["device_type"], "UNKNOWN")
                sub_sn_start = PATCHED_SERIALS[subdev_type.upper()]
                assert sub_sn_start <= sub_serial < str(int(sub_sn_start) + 99)

    # Verify serials in non-masked endpoints are signalled
    assert ANONYMIZATION_ERROR_KEY in anonymized_fixtures
    assert Counter(anonymized_fixtures[ANONYMIZATION_ERROR_KEY]) == Counter(
        [
            "Masked serials also found in /info",
            "Masked serials also found in /my_endpoint",
        ]
        + (
            ["Unusable data for /ivp/pdm/device_data"]
            if "/ivp/pdm/device_data" in exclude
            else []
        )
        + (
            ["Unusable data for /inventory.json?deleted=1"]
            if "/inventory.json?deleted=1" in exclude
            else []
        )
    )

    # test dumps error handling
    with patch("pyenphase.anonymization.orjson.dumps", side_effect=ValueError):
        strict_anonymized_fixtures = anonymize_serials(fixtures, strict=True)
    assert ANONYMIZATION_ERROR_KEY in strict_anonymized_fixtures
    assert any(
        "Error during final serial scan for" in log
        for log in strict_anonymized_fixtures[ANONYMIZATION_ERROR_KEY]
    )

    # test regex error handling
    with patch(
        "pyenphase.anonymization.re.compile",
        side_effect=re.error("Test failed compile"),
    ):
        strict_anonymized_fixtures = anonymize_serials(fixtures, strict=True)
    assert ANONYMIZATION_ERROR_KEY in strict_anonymized_fixtures
    assert any(
        "Error during serial replacement for regex" in log
        for log in strict_anonymized_fixtures[ANONYMIZATION_ERROR_KEY]
    )

    # test anonymize of raw data
    assert envoy.data
    anonymized_raw = anonymize_serials(envoy.data.raw)
    assert "collection_aborted_log" not in anonymized_raw

    # verify raw entries serial mapping is the same as fixtures
    for endpoint in anonymized_raw:
        if not endpoint.endswith("_log") and endpoint.startswith("/"):
            assert endpoint in anonymized_fixtures
            assert anonymized_raw[endpoint] == anonymized_fixtures[endpoint]
            assert f"{endpoint}_log" in anonymized_raw
            assert (
                anonymized_raw[f"{endpoint}_log"]["mask_state"]
                == anonymized_fixtures[f"{endpoint}_log"]["mask_state"]
            )

    override_mock(
        mock_aioresponse, "get", f"{full_host}/info", body=info_xml, repeat=True
    )

    inv_json = await load_json_list_fixture(
        version, endpoint_to_fixture_file["/api/v1/production/inverters"]
    )
    # test short serial to inverters
    inv_json[1]["serialNumber"] = "4501"
    # test numerical serial for inverters
    inv_json[2]["serialNumber"] = 4500000001
    # test blank serial
    inv_json[3]["serialNumber"] = ""

    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/api/v1/production/inverters",
        payload=inv_json,
        repeat=True,
    )

    mock_aioresponse.get(
        f"{full_host}/my_number_endpoint",
        payload={"test": "this is the inverter numerical serial 4500000001"},
        status=200,
        repeat=True,
    )

    mock_aioresponse.get(
        f"{full_host}/my_short_number_endpoint",
        payload={"test": "this is the inverter numerical serial 4501"},
        status=200,
        repeat=True,
    )

    mock_aioresponse.get(
        f"{full_host}/my_short_quoted_number_endpoint",
        payload={"test": "4501"},
        status=200,
        repeat=True,
    )

    mock_aioresponse.get(
        f"{full_host}/my_embedded_long_endpoint",
        payload={
            "test": "this is the embedded 67450000000101 inverter numerical serial"
        },
        repeat=True,
    )

    mock_aioresponse.get(
        f"{full_host}/my_string_embedded_long_endpoint",
        payload={
            "test": "this is the embedded SN4500000001EIM inverter numerical serial"
        },
        repeat=True,
    )

    # obtain fixtures_collection with serial anonymization
    fixtures = await envoy.fixture_collection(
        additional_endpoints=[
            "/my_number_endpoint",
            "/my_short_number_endpoint",
            "/my_embedded_long_endpoint",
            "/my_string_embedded_long_endpoint",
            "/my_short_quoted_number_endpoint",
        ],
        mask_serials=True,
    )

    assert ANONYMIZATION_ERROR_KEY in fixtures
    assert any(
        "Masked serials also found in /my_number_endpoint" in log
        for log in fixtures[ANONYMIZATION_ERROR_KEY]
    )
    assert "/my_number_endpoint" in fixtures
    assert fixtures["/my_number_endpoint_log"]["mask_state"] == MASK_STATE.FAILED

    assert any(
        f"Short serials of {SHORT_SERIAL} characters or less are only scanned within delimiters, found"
        in log
        for log in fixtures[ANONYMIZATION_ERROR_KEY]
    )
    assert "/my_short_number_endpoint" in fixtures
    assert (
        fixtures["/my_short_number_endpoint_log"]["mask_state"] == MASK_STATE.UNCHANGED
    )

    assert not any(
        "Masked serials also found in /my_embedded_long_endpoint" in log
        for log in fixtures[ANONYMIZATION_ERROR_KEY]
    )
    assert "/my_embedded_long_endpoint" in fixtures
    assert (
        fixtures["/my_embedded_long_endpoint_log"]["mask_state"] == MASK_STATE.UNCHANGED
    )

    assert any(
        "Masked serials also found in /my_string_embedded_long_endpoint" in log
        for log in fixtures[ANONYMIZATION_ERROR_KEY]
    )
    assert "/my_string_embedded_long_endpoint" in fixtures
    assert (
        fixtures["/my_string_embedded_long_endpoint_log"]["mask_state"]
        == MASK_STATE.FAILED
    )

    assert any(
        "Masked short serials also found in /my_short_quoted_number_endpoint" in log
        for log in fixtures[ANONYMIZATION_ERROR_KEY]
    )
    assert "/my_short_quoted_number_endpoint" in fixtures
    assert (
        fixtures["/my_short_quoted_number_endpoint_log"]["mask_state"]
        == MASK_STATE.FAILED
    )

    meter_json = await load_json_list_fixture(
        version, endpoint_to_fixture_file["/ivp/meters/readings"]
    )
    # meters should be untouched
    assert fixtures["/ivp/meters/readings"] == meter_json
    assert fixtures["/ivp/meters/readings"] == meter_json
    assert (
        anonymized_fixtures["/ivp/meters/readings_log"]["mask_state"]
        == MASK_STATE.UNCHANGED
    )

    # obtain fixtures_collection with strict serial anonymization
    fixtures = await envoy.fixture_collection(
        additional_endpoints=[
            "/my_number_endpoint",
            "/my_short_number_endpoint",
            "/my_embedded_long_endpoint",
            "/my_string_embedded_long_endpoint",
            "/my_short_quoted_number_endpoint",
        ],
        mask_serials=True,
        strict_masking=True,
    )

    assert ANONYMIZATION_ERROR_KEY in fixtures
    assert any(
        "Masked serials also found in /my_number_endpoint" in log
        for log in fixtures[ANONYMIZATION_ERROR_KEY]
    )
    assert "/my_number_endpoint" not in fixtures
    assert fixtures["/my_number_endpoint_log"]["mask_state"] == MASK_STATE.REMOVED

    assert any(
        f"Short serials of {SHORT_SERIAL} characters or less are only scanned within delimiters, found"
        in log
        for log in fixtures[ANONYMIZATION_ERROR_KEY]
    )
    assert "/my_short_number_endpoint" in fixtures
    assert (
        fixtures["/my_short_number_endpoint_log"]["mask_state"] == MASK_STATE.UNCHANGED
    )

    assert not any(
        "Masked serials also found in /my_embedded_long_endpoint" in log
        for log in fixtures[ANONYMIZATION_ERROR_KEY]
    )
    assert "/my_embedded_long_endpoint" in fixtures
    assert (
        fixtures["/my_embedded_long_endpoint_log"]["mask_state"] == MASK_STATE.UNCHANGED
    )

    assert any(
        "Masked serials also found in /my_string_embedded_long_endpoint" in log
        for log in fixtures[ANONYMIZATION_ERROR_KEY]
    )
    assert "/my_string_embedded_long_endpoint" not in fixtures
    assert (
        fixtures["/my_string_embedded_long_endpoint_log"]["mask_state"]
        == MASK_STATE.REMOVED
    )

    assert any(
        "Masked short serials also found in /my_short_quoted_number_endpoint" in log
        for log in fixtures[ANONYMIZATION_ERROR_KEY]
    )
    assert "/my_short_quoted_number_endpoint" not in fixtures
    assert (
        fixtures["/my_short_quoted_number_endpoint_log"]["mask_state"]
        == MASK_STATE.REMOVED
    )

    # meters should be untouched
    assert fixtures["/ivp/meters/readings"] == meter_json
    assert fixtures["/ivp/meters/readings"] == meter_json
    assert (
        anonymized_fixtures["/ivp/meters/readings_log"]["mask_state"]
        == MASK_STATE.UNCHANGED
    )
