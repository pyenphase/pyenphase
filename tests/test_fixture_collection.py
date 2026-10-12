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


@patch(
    "pyenphase.envoy.TYPE_SERIALS",
    {
        "pcu": "101000000001",
        "acb": "201000000001",
        "encharge": "301000000001",
        "enpower": "401000000001",
        "collar": "511000000001",
        "c6 combiner controller": "521000000001",
        "c6 rgm": "531000000001",
        "nsrb": "611000000001",
        "esub": "621000000001",
    },
)
@patch("pyenphase.envoy.ENVOY_SERIAL", "923456789012")
@patch("pyenphase.envoy.UNKNOWN_SERIAL", "991000000001")
@pytest.mark.parametrize(
    ("version"),
    [
        "8.3.5169_ACB_inventory",
        "8.3.5169_with_generator",
    ],
)
@pytest.mark.asyncio
async def test_fixture_collection(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
) -> None:
    """
    Test fixture file data collection.
    Use different serials to test so we can test
    anonymized fixtures in the future as well
    """
    start_7_firmware_mock(mock_aioresponse)
    files = await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    envoy = await get_mock_envoy(test_client_session)
    full_host = endpoint_path(version, envoy.host)

    # override endpoints with serialnumbers to test serial anonimization
    info_xml = "<envoy_info><device><sn>210987654321</sn><software>D8.3.6087</software></device></envoy_info>"
    info_xml_patched = "<envoy_info><device><sn>923456789012</sn><software>D8.3.6087</software></device></envoy_info>"
    override_mock(mock_aioresponse, "get", f"{full_host}/info", body=info_xml)

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
            and file in files
        ):
            try:
                content = await load_json_fixture(version, file)
                assert fixtures_collection[endpoint] == content
                assert not fixtures_collection[f"{endpoint}_log"]["anonymization"]
            except orjson.JSONDecodeError:
                string_content = await load_fixture(version, file)
                string_content = string_content.replace("\n", "")
                assert fixtures_collection[endpoint] == string_content
                assert not fixtures_collection[f"{endpoint}_log"]["anonymization"]

    # verify endpoints with serial anonimization
    endpoint = "/info"
    assert endpoint in fixtures_collection
    assert fixtures_collection["/info"] == info_xml_patched
    assert fixtures_collection[f"{endpoint}_log"]["anonymization"]

    endpoint = "/api/v1/production/inverters"
    assert endpoint in fixtures_collection
    content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
    assert len(fixtures_collection[endpoint]) == len(content)
    assert fixtures_collection[f"{endpoint}_log"]["anonymization"]
    for inverter in fixtures_collection[endpoint]:
        if inverter["devType"] == 11:
            assert "201000000000" < inverter["serialNumber"] < "201000000099"
        else:
            assert "101000000000" < inverter["serialNumber"] < "101000000099"

    # verify pdm devices inventory serial anonymization
    endpoint = "/ivp/pdm/device_data"
    assert endpoint in fixtures_collection
    content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
    assert len(fixtures_collection[endpoint]) == len(content)
    # ^:  one of two true, not both true or both false
    assert not (
        (len(fixtures_collection[endpoint]) > 0)
        ^ fixtures_collection[f"{endpoint}_log"]["anonymization"]
    )
    for id in (pdm := fixtures_collection[endpoint]):
        if id not in ("deviceCount", "deviceDataLimit"):
            if pdm[id]["devName"] == "eim":
                assert "923456789012EIM" in pdm[id]["sn"]
            elif pdm[id]["devName"] == "acb":
                assert "201000000000" < pdm[id]["sn"] < "201000000099"
            else:
                assert "101000000000" < pdm[id]["sn"] < "101000000099"

    # verify ensemble inventory serial anonymization
    endpoint = "/ivp/ensemble/inventory"
    content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
    assert len(fixtures_collection[endpoint]) == len(content)
    assert not (
        (len(fixtures_collection[endpoint]) > 0)
        ^ fixtures_collection[f"{endpoint}_log"]["anonymization"]
    )
    for inventory_type in fixtures_collection[endpoint]:
        type = inventory_type["type"]
        for device in inventory_type["devices"]:
            if type == "ENCHARGE":
                assert "301000000000" < device["serial_num"] < "301000000099"
            elif type == "ENPOWER":
                assert "401000000000" < device["serial_num"] < "401000000099"
            elif type == "COLLAR":
                assert "511000000000" < device["serial_num"] < "511000000099"
            elif type == "C6 COMBINER CONTROLLER":
                assert "521000000000" < device["serial_num"] < "521000000099"
            elif type == "C6 RGM":
                assert "531000000000" < device["serial_num"] < "531000000099"
            else:
                assert "991000000000" < device["serial_num"] < "991000000099"

    endpoint = "/ivp/ensemble/power"
    content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
    assert len(fixtures_collection[endpoint]) == len(content)
    assert not (
        (len(fixtures_collection[endpoint]["devices:"]) > 0)
        ^ fixtures_collection[f"{endpoint}_log"]["anonymization"]
    )
    for device in fixtures_collection[endpoint]["devices:"]:
        assert "301000000000" < device["serial_num"] < "301000000099"

    # verify inventory serial anonymization
    endpoint = "/inventory.json?deleted=1"
    content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
    assert len(fixtures_collection[endpoint]) == len(content)
    assert not (
        (len(fixtures_collection[endpoint]) > 0)
        ^ fixtures_collection[f"{endpoint}_log"]["anonymization"]
    )
    for inventory_type in fixtures_collection[endpoint]:
        type = inventory_type["type"]
        for device in inventory_type["devices"]:
            if type == "PCU":
                assert "101000000000" < device["serial_num"] < "101000000099"
            elif type == "ACB":
                assert "201000000000" < device["serial_num"] < "201000000099"
            elif type == "NSRB":
                assert "611000000000" < device["serial_num"] < "611000000099"
            elif type == "ESUB":
                assert "621000000000" < device["serial_num"] < "621000000099"
            else:
                assert "991000000000" < device["serial_num"] < "991000000099"

    # Verify timeout will end fixture collection
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/api/v1/production",
        exception=asyncio.TimeoutError("Test timeoutexception"),
    )
    fixtures_collection = await envoy.fixture_collection()

    # validate we now have an error entry and failed endpoint is not in the list
    assert fixtures_collection
    assert "/api/v1/production" not in fixtures_collection
    assert ("error", "TimeoutError('Test timeoutexception')") in fixtures_collection[
        "/api/v1/production_log"
    ].items()
    assert ("code", 0) in fixtures_collection["/api/v1/production_log"].items()
    # verify endpoint failed in last in dict
    assert list(fixtures_collection.keys())[-1] == "/api/v1/production_log"

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
