"""Test envoy fixture set collection"""

import asyncio
import logging
from typing import Any
from unittest.mock import patch

import aiohttp
import orjson
import pytest
from aioresponses import aioresponses

from pyenphase.const import FIXTURE_LIST

from .common import (
    endpoint_fixture_file,
    endpoint_path,
    get_mock_envoy,
    load_fixture,
    load_json_fixture,
    override_mock,
    prep_envoy,
    start_7_firmware_mock,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    ("version", "endpoints"),
    [
        (
            "8.3.6087_storage_ct_drops",
            [
                "/ivp/meters/readings",
                "/ivp/meters",
            ],
        ),
        (
            "8.3.5169_with_generator",
            [
                "/ivp/ensemble/generator",
                "/ivp/meters/readings",
                "/ivp/meters",
            ],
        ),
    ],
    ids=[
        "8.3.6087_storage_ct_drops",
        "8.3.5169_with_generator",
    ],
)
@pytest.mark.asyncio
async def test_fixture_collection(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    endpoints: str,
    version: str,
) -> None:
    """Test fixture file data collection"""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    envoy = await get_mock_envoy(test_client_session)
    full_host = endpoint_path(version, envoy.host)

    # override endpoints with serialnumbers to test serial anonimization
    info_xml = "<envoy_info><device><sn>210987654321</sn><software>D8.3.6087</software></device></envoy_info>"
    info_xml_patched = "<envoy_info><device><sn>123456789012</sn><software>D8.3.6087</software></device></envoy_info>"
    override_mock(mock_aioresponse, "get", f"{full_host}/info", body=info_xml)

    # use low test serial numbers to avoid pdm device serials sorted first
    inverters_json: list[dict[str, Any]] = [
        {
            "serialNumber": "000000000001",
            "lastReportDate": 1791196789,
            "devType": 1,
            "lastReportWatts": 143,
            "maxReportWatts": 173,
        },
        {
            "serialNumber": "000000000002",
            "lastReportDate": 1791196067,
            "devType": 1,
            "lastReportWatts": 155,
            "maxReportWatts": 230,
        },
    ]
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/api/v1/production/inverters",
        payload=inverters_json,
    )

    # test fixtures_collection method
    fixtures_collection: dict[str, Any] = await envoy.fixture_collection()
    # validate all fixture logs are created
    assert fixtures_collection
    for fixture in FIXTURE_LIST:
        assert f"{fixture}_log" in fixtures_collection

    # map endpoint to fixture file and verify fixture_collection samples to file content
    endpoint_to_fixture_file = {
        endpoint: endpoint_fixture_file(endpoint) for endpoint in FIXTURE_LIST
    }
    # verify endpoints without serial anonimization
    for endpoint in endpoints:
        assert endpoint in fixtures_collection
        try:
            content = await load_json_fixture(
                version, endpoint_to_fixture_file[endpoint]
            )
            assert fixtures_collection[endpoint] == content
        except orjson.JSONDecodeError:
            string_content = await load_fixture(
                version, endpoint_to_fixture_file[endpoint]
            )
            string_content = string_content.replace("\n", "")
            assert fixtures_collection[endpoint] == string_content

    # verify endpoints with serial anonimization
    assert "/info" in fixtures_collection
    assert fixtures_collection["/info"] == info_xml_patched

    assert "/api/v1/production/inverters" in fixtures_collection
    expected_inverters_json: list[dict[str, Any]] = [
        {
            "serialNumber": "100000000001",
            "lastReportDate": 1791196789,
            "devType": 1,
            "lastReportWatts": 143,
            "maxReportWatts": 173,
        },
        {
            "serialNumber": "100000000002",
            "lastReportDate": 1791196067,
            "devType": 1,
            "lastReportWatts": 155,
            "maxReportWatts": 230,
        },
    ]
    assert (
        fixtures_collection["/api/v1/production/inverters"] == expected_inverters_json
    )

    # verify pdm devices inventory serial anonymization
    endpoint = "/ivp/pdm/device_data"
    assert endpoint in fixtures_collection
    content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
    assert len(fixtures_collection[endpoint]) == len(content)
    for id in (pdm := fixtures_collection[endpoint]):
        if id not in ("deviceCount", "deviceDataLimit"):
            if pdm[id]["devName"] == "eim":
                assert "123456789012EIM" in pdm[id]["sn"]
            else:
                assert "100000000000" < pdm[id]["sn"] < "100000000099"

    # verify ensemble inventory serial anonymization
    endpoint = "/ivp/ensemble/inventory"
    content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
    assert len(fixtures_collection[endpoint]) == len(content)
    for ensemble_type in fixtures_collection[endpoint]:
        type = ensemble_type["type"]
        for device in ensemble_type["devices"]:
            if type == "ENCHARGE":
                assert "300000000000" < device["serial_num"] < "300000000099"
            elif type == "ENPOWER":
                assert "400000000000" < device["serial_num"] < "400000000099"
            elif type == "COLLAR":
                assert "510000000000" < device["serial_num"] < "510000000099"
            elif type == "C6 COMBINER CONTROLLER":
                assert "520000000000" < device["serial_num"] < "520000000099"
            elif type == "C6 RGM":
                assert "530000000000" < device["serial_num"] < "530000000099"
            else:
                assert "590000000000" < device["serial_num"] < "590000000099"

    endpoint = "/ivp/ensemble/power"
    content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
    assert len(fixtures_collection[endpoint]) == len(content)
    for device in fixtures_collection[endpoint]["devices:"]:
        assert "300000000000" < device["serial_num"] < "300000000099"

    # Verify timeout will end fixture collection
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}{endpoints[0]}",
        exception=asyncio.TimeoutError("Test timeoutexception"),
    )
    fixtures_collection = await envoy.fixture_collection()

    # validate we now have an error entry and failed endpoint is not in the list
    assert fixtures_collection
    assert endpoints[0] not in fixtures_collection
    assert ("error", "TimeoutError('Test timeoutexception')") in fixtures_collection[
        f"{endpoints[0]}_log"
    ].items()
    assert ("code", 0) in fixtures_collection[f"{endpoints[0]}_log"].items()
    # verify endpoint failed in last in dict
    assert list(fixtures_collection.keys())[-1] == f"{endpoints[0]}_log"

    # Test additional endpoints
    test_json: dict[str, str | int] = {"test": 1, "envoy": "1234"}
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/test/my/endpoint",
        payload=test_json,
        status=200,
        repeat=True,
    )
    # test conent-type application/json fallback to text
    invalid_json = "invalid json"
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/test/my/invalid_endpoint",
        body=invalid_json,
        status=200,
        repeat=True,
    )
    # test with missing endpoints
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/ivp/ensemble/power",
        status=404,
    )
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/ivp/ensemble/inventory",
        status=404,
    )

    fixtures_collection = await envoy.fixture_collection(
        ["/test/my/endpoint", "/test/my/invalid_endpoint"]
    )
    assert fixtures_collection
    assert "/test/my/endpoint" in fixtures_collection
    assert "/test/my/endpoint_log" in fixtures_collection
    assert fixtures_collection["/test/my/endpoint"] == test_json
    assert "/test/my/invalid_endpoint" in fixtures_collection
    assert "/test/my/invalid_endpoint_log" in fixtures_collection
    assert fixtures_collection["/test/my/invalid_endpoint"] == invalid_json
    assert "/ivp/ensemble/power_log" in fixtures_collection
    assert ("code", 404) in fixtures_collection["/ivp/ensemble/power_log"].items()
    assert "/ivp/ensemble/inventory_log" in fixtures_collection
    assert ("code", 404) in fixtures_collection["/ivp/ensemble/inventory_log"].items()

    # test data error in anonymization
    override_mock(mock_aioresponse, "get", f"{full_host}/info", body=info_xml)
    with patch(
        "pyenphase.Envoy.anonymize_serials",
        side_effect=KeyError,
    ):
        fixtures_collection = await envoy.fixture_collection()
    assert fixtures_collection["/info"] == info_xml
