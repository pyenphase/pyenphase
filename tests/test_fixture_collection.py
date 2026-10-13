"""Test envoy fixture set collection"""

import asyncio
import logging
from typing import Any
from unittest.mock import patch

import aiohttp
import orjson
import pytest
from aioresponses import aioresponses

from pyenphase.const import DEVICE_TYPES, FIXTURE_LIST, TYPE_SERIALS

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
    },
)
@patch("pyenphase.envoy.ENVOY_SERIAL", "923456789012")
@patch("pyenphase.envoy.UNKNOWN_SERIAL", "999999999901")
@pytest.mark.parametrize(
    ("version", "exclude"),
    [
        ("8.3.5169_ACB_inventory", []),
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
async def test_fixture_collection(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    exclude: list[str],  # exclude from fixture tests
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

    # verify DEVICE_TYPES values and TYPE_SERIALS keys match
    assert sorted(set(DEVICE_TYPES.values())) == sorted(TYPE_SERIALS)

    # map endpoint to fixture file and verify fixture_collection samples to file content
    endpoint_to_fixture_file = {
        endpoint: endpoint_fixture_file(endpoint) for endpoint in FIXTURE_LIST
    }

    # test fixtures_collection method without serial anonymization
    fixtures_collection: dict[str, Any] = await envoy.fixture_collection(
        mask_serials=False
    )
    # validate all fixture logs are created
    assert fixtures_collection
    for fixture in FIXTURE_LIST:
        assert f"{fixture}_log" in fixtures_collection

    assert "collection_aborted_log" not in fixtures_collection
    assert "anonymization_errors_log" not in fixtures_collection

    for endpoint, file in endpoint_to_fixture_file.items():
        if endpoint not in exclude and file in files:
            assert "anonymization" not in fixtures_collection[f"{endpoint}_log"]
            try:
                content = await load_json_fixture(version, file)
                assert fixtures_collection[endpoint] == content
            except orjson.JSONDecodeError:
                string_content = await load_fixture(version, file)
                string_content = string_content.replace("\n", "")
                assert fixtures_collection[endpoint] == string_content

    # override envoy serial, use patched serials so we can test anonymized fixtures as well
    info_xml = "<envoy_info><device><sn>210987654321</sn><software>D8.3.6087</software></device></envoy_info>"
    info_xml_patched = "<envoy_info><device><sn>923456789012</sn><software>D8.3.6087</software></device></envoy_info>"
    override_mock(mock_aioresponse, "get", f"{full_host}/info", body=info_xml)

    # test fixtures_collection method with serial anonymization
    fixtures_collection = await envoy.fixture_collection()

    # validate all fixture logs are created
    assert fixtures_collection
    assert "collection_aborted_log" not in fixtures_collection
    assert "anonymization_errors_log" not in fixtures_collection

    for fixture in FIXTURE_LIST:
        assert f"{fixture}_log" in fixtures_collection

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
            assert not fixtures_collection[f"{endpoint}_log"]["anonymization"]
            try:
                content = await load_json_fixture(version, file)
                assert fixtures_collection[endpoint] == content
            except orjson.JSONDecodeError:
                string_content = await load_fixture(version, file)
                string_content = string_content.replace("\n", "")
                assert fixtures_collection[endpoint] == string_content

    # verify endpoints with serial anonimization
    endpoint = "/info"
    assert endpoint in fixtures_collection
    assert fixtures_collection["/info"] == info_xml_patched
    assert fixtures_collection[f"{endpoint}_log"]["anonymization"]

    endpoint = "/api/v1/production/inverters"
    if endpoint not in exclude:
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
    if endpoint not in exclude:
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
                if pdm[id]["devName"].upper() == "EIM":
                    assert "923456789012EIM" in pdm[id]["sn"]
                elif pdm[id]["devName"].upper() == "ACB":
                    assert "201000000000" < pdm[id]["sn"] < "201000000099"
                else:
                    assert "101000000000" < pdm[id]["sn"] < "101000000099"

    # verify ensemble inventory serial anonymization
    endpoint = "/ivp/ensemble/inventory"
    if endpoint not in exclude:
        content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
        assert len(fixtures_collection[endpoint]) == len(content)
        assert not (
            (len(fixtures_collection[endpoint]) > 0)
            ^ fixtures_collection[f"{endpoint}_log"]["anonymization"]
        )
        for inventory_type in fixtures_collection[endpoint]:
            dev_type = inventory_type["type"]
            for device in inventory_type["devices"]:
                if dev_type == "ENCHARGE":
                    assert "301000000000" < device["serial_num"] < "301000000099"
                elif dev_type == "ENPOWER":
                    assert "401000000000" < device["serial_num"] < "401000000099"
                elif dev_type == "COLLAR":
                    assert "511000000000" < device["serial_num"] < "511000000099"
                elif dev_type == "C6 COMBINER CONTROLLER":
                    assert "521000000000" < device["serial_num"] < "521000000099"
                elif dev_type == "C6 RGM":
                    assert "531000000000" < device["serial_num"] < "531000000099"
                elif dev_type == "UNKNOWN":
                    assert "991000000000" < device["serial_num"] < "991000000099"
                else:
                    assert "999999999001" < device["serial_num"] < "999999999099"

    endpoint = "/ivp/ensemble/power"
    if endpoint not in exclude:
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
    if endpoint not in exclude:
        content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
        assert len(fixtures_collection[endpoint]) == len(content)
        assert not (
            (len(fixtures_collection[endpoint]) > 0)
            ^ fixtures_collection[f"{endpoint}_log"]["anonymization"]
        )
        for inventory_type in fixtures_collection[endpoint]:
            dev_type = inventory_type["type"]
            for device in inventory_type["devices"]:
                if dev_type == "PCU":
                    assert "101000000000" < device["serial_num"] < "101000000099"
                elif dev_type == "ACB":
                    assert "201000000000" < device["serial_num"] < "201000000099"
                elif dev_type == "NSRB":
                    assert "611000000000" < device["serial_num"] < "611000000099"
                elif dev_type == "ESUB":
                    assert "621000000000" < device["serial_num"] < "621000000099"
                elif dev_type == "UNKNOWN":
                    assert "991000000000" < device["serial_num"] < "991000000099"
                else:
                    assert "999999999001" < device["serial_num"] < "999999999099"

    # verify ensemble status serial anonymization
    endpoint = "/ivp/ensemble/status"
    if endpoint not in exclude:
        content = await load_json_fixture(version, endpoint_to_fixture_file[endpoint])
        assert len(fixtures_collection[endpoint]) == len(content)
        assert not (
            (len(fixtures_collection[endpoint]["inventory"]["serial_nums"]) > 0)
            ^ fixtures_collection[f"{endpoint}_log"]["anonymization"]
        )
        for serial_num, device in fixtures_collection[endpoint]["inventory"][
            "serial_nums"
        ].items():
            dev_type = DEVICE_TYPES.get(device["device_type"], "UNKNOWN")
            if dev_type == "PCU":
                assert "101000000000" < serial_num < "101000000099"
            elif dev_type == "ACB":
                assert "201000000000" < serial_num < "201000000099"
            elif dev_type == "ENCHARGE":
                assert "301000000000" < serial_num < "301000000099"
            elif dev_type == "ENPOWER":
                assert "401000000000" < serial_num < "401000000099"
            elif dev_type == "COLLAR":
                assert "511000000000" < serial_num < "511000000099"
            elif dev_type == "C6 COMBINER CONTROLLER":
                assert "521000000000" < serial_num < "521000000099"
            elif dev_type == "C6 RGM":
                assert "531000000000" < serial_num < "531000000099"
            elif dev_type == "NSRB":
                assert "611000000000" < serial_num < "611000000099"
            elif dev_type == "ESUB":
                assert "621000000000" < serial_num < "621000000099"
            elif dev_type == "UNKNOWN":
                assert "991000000000" < serial_num < "991000000099"
            else:
                assert "999999999001" < serial_num < "999999999099"

    # anonymize raw data
    assert envoy.data
    anonymized_raw = envoy.anonymize_serials(envoy.data.raw)
    assert "collection_aborted_log" not in anonymized_raw
    assert "anonymization_errors_log" not in anonymized_raw

    # verify raw entries serial mapping is the same
    for endpoint in anonymized_raw:
        assert endpoint in fixtures_collection
        if not endpoint.endswith("_log") and endpoint.startswith("/"):
            assert anonymized_raw[endpoint] == fixtures_collection[endpoint]

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
    # verify collection_aborted_log is in the list
    assert "collection_aborted_log" in fixtures_collection
    assert "Test timeoutexception" in fixtures_collection["collection_aborted_log"]

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
    # test content-type application/json fallback to text
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
    info_xml_nosn = "<envoy_info><device><nosn>210987654321</nosn><software>D8.3.6087</software></device></envoy_info>"
    override_mock(
        mock_aioresponse, "get", f"{full_host}/info", body=info_xml_nosn, repeat=True
    )
    sn = envoy.serial_number
    envoy._firmware._serial_number = None
    fixtures_collection = await envoy.fixture_collection(
        ["/test/my/endpoint", "/test/my/invalid_endpoint"]
    )
    envoy._firmware._serial_number = sn

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
    assert fixtures_collection
    assert "anonymization_errors_log" in fixtures_collection
    assert (
        "Error for /info 'no sn match'"
        in fixtures_collection["anonymization_errors_log"]
    )
    # test data error in anonymization
    override_mock(
        mock_aioresponse, "get", f"{full_host}/info", body=info_xml, repeat=True
    )
    inverters_keyerror = [{"maxReportWatts": 297}]
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/api/v1/production/inverters",
        payload=inverters_keyerror,
    )
    # test with data errors
    invalid_device_data: dict[str, Any] = {
        "553648384": {
            "sn": "202305037927",
            "active": True,
            "modGone": False,
            "channels": [],
        }
    }
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/ivp/pdm/device_data",
        payload=invalid_device_data,
        status=200,
    )
    # test with data errors
    invalid_inventory_data: list[dict[str, Any]] = [
        {
            "type": "PCU",
            "devices": [
                {
                    "part_num": "800-01331-r02",
                    "installed": "1750786534",
                },
            ],
        },
    ]
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/inventory.json?deleted=1",
        payload=invalid_inventory_data,
        status=200,
    )
    # test with data errors
    invalid_power_data: dict[str, Any] = {
        "devices:": ["hello", "world"],
    }
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/ivp/ensemble/power",
        payload=invalid_power_data,
        status=200,
    )
    # test with data errors
    invalid_ensemble_data: list[dict[str, Any]] = [
        {
            "type": "ENCHARGE",
            "devices": [
                {
                    "part_num": "836-01250-r00",
                }
            ],
        }
    ]
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/ivp/ensemble/inventory",
        payload=invalid_ensemble_data,
        status=200,
    )
    # test with data errors
    invalid_status_data: dict[str, Any] = {
        "inventory": {
            "serial_nums": {
                "482520020939": {
                    "DEVICE_TYPE": 27,
                    "com_interface_str": "CAN",
                    "device_id": "482520020939",
                }
            }
        }
    }
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/ivp/ensemble/status",
        payload=invalid_status_data,
        status=200,
    )

    fixtures_collection = await envoy.fixture_collection()
    assert fixtures_collection
    assert fixtures_collection["/info"] == info_xml_patched
    assert "anonymization_errors_log" in fixtures_collection
    assert (
        "Error for /api/v1/production/inverters 'serialNumber'"
        in fixtures_collection["anonymization_errors_log"]
    )
    assert (
        "Error for /ivp/pdm/device_data 'devName'"
        in fixtures_collection["anonymization_errors_log"]
    )
    assert (
        "Error for /inventory.json?deleted=1 'serial_num'"
        in fixtures_collection["anonymization_errors_log"]
    )
    assert (
        "Error for /ivp/ensemble/power string indices must be integers, not 'str'"
        in fixtures_collection["anonymization_errors_log"]
    )
    assert (
        "Error for /ivp/ensemble/inventory 'serial_num'"
        in fixtures_collection["anonymization_errors_log"]
    )
    assert (
        "Error for /ivp/ensemble/status 'device_type'"
        in fixtures_collection["anonymization_errors_log"]
    )

    # test any error leaking is raised
    with (
        patch(
            "pyenphase.Envoy.anonymize_serials",
            side_effect=FileExistsError,
        ),
        pytest.raises(FileExistsError),
    ):
        fixtures_collection = await envoy.fixture_collection()
