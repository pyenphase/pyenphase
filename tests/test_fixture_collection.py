"""Test envoy fixture set collection"""

import asyncio
import logging
from typing import Any
from unittest.mock import patch

import aiohttp
import orjson
import pytest
from aiohttp.client import RequestInfo
from aioresponses import aioresponses
from syrupy.assertion import SnapshotAssertion
from syrupy.filters import props

from pyenphase import Envoy
from pyenphase.const import (
    ANONYMIZATION_ERROR_KEY,
    DEVICE_TYPES,
    FIXTURE_LIST,
    TYPE_SERIALS,
)
from pyenphase.exceptions import EnvoyAuthenticationRequired

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
from .test_anonymization import PATCHED_ENVOY_SERIAL, PATCHED_SERIALS

LOGGER = logging.getLogger(__name__)
ENSEMBLE_POWER_DEVICE = "devices:"

TEST_FIXTURES = [
    (
        "8.3.5169_ACB_inventory",
        [
            "/ivp/ensemble/relay",
            "/admin/lib/acb_config",
            "/ivp/sc/sched",
            "/ivp/livedata/status",
        ],
    ),
    (
        "8.3.5169_with_generator",
        [
            "/ivp/ensemble/relay",
            "/admin/lib/acb_config",
            "/ivp/sc/sched",
            "/ivp/livedata/status",
        ],
    ),
    (
        "8.3.1598_collar",
        [
            "/ivp/ensemble/relay",
            "/admin/lib/acb_config",
            "/ivp/sc/sched",
            "/ivp/livedata/status",
            "/ivp/pdm/energy",
        ],
    ),
]

TEST_IDS = [
    "8.3.5169_ACB_inventory",
    "8.3.5169_with_generator",
    "8.3.1598_collar",
]


@patch("pyenphase.anonymization.TYPE_SERIALS", PATCHED_SERIALS)
@patch("pyenphase.anonymization.ENVOY_SERIAL", PATCHED_ENVOY_SERIAL)
@pytest.mark.parametrize(
    ("mode"),
    ("report", "anonymized", "strict_anonymized"),
)
@pytest.mark.parametrize(
    ("version", "exclude"),
    TEST_FIXTURES,
    ids=TEST_IDS,
)
@pytest.mark.asyncio
async def test_fixture_collection_snapshots(
    snapshot: SnapshotAssertion,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    exclude: list[str],  # exclude from fixture tests
    mode: str,
) -> None:
    """Test fixture file data collection."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    envoy = await get_mock_envoy(test_client_session)

    # verify DEVICE_TYPES values and TYPE_SERIALS keys match
    assert sorted(set(DEVICE_TYPES.values())) == sorted(TYPE_SERIALS)

    # test fixtures_collection method without serial anonymization
    fixtures_collection: dict[str, Any] = await envoy.fixture_collection(
        mask_serials=mode != "report",
        strict_masking=mode == "strict_anonymized",
    )
    assert fixtures_collection

    # track fixture and/or code change impact
    # ignore report time and duration in <endpoint>_log
    assert fixtures_collection == snapshot(
        exclude=props("report_time", "duration_seconds")
    )


@patch("pyenphase.anonymization.TYPE_SERIALS", PATCHED_SERIALS)
@patch("pyenphase.anonymization.ENVOY_SERIAL", PATCHED_ENVOY_SERIAL)
@pytest.mark.parametrize(
    ("version", "exclude"),
    TEST_FIXTURES,
    ids=TEST_IDS,
)
@pytest.mark.asyncio
async def test_fixture_collection(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    exclude: list[str],  # exclude from fixture tests
) -> None:
    """Test fixture file data collection."""
    start_7_firmware_mock(mock_aioresponse)
    files = await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    envoy = await get_mock_envoy(test_client_session)
    full_host = endpoint_path(version, envoy.host)

    # verify DEVICE_TYPES values and TYPE_SERIALS keys match
    assert sorted(set(DEVICE_TYPES.values())) == sorted(TYPE_SERIALS)

    # map endpoints to fixture file
    endpoint_to_fixture_file = {
        endpoint: endpoint_fixture_file(endpoint) for endpoint in FIXTURE_LIST
    }

    # test fixtures_collection method without serial anonymization
    fixtures_collection: dict[str, Any] = await envoy.fixture_collection(
        mask_serials=False
    )
    assert fixtures_collection

    for fixture in FIXTURE_LIST:
        assert f"{fixture}_log" in fixtures_collection
        assert "code" in fixtures_collection[f"{fixture}_log"]
        assert "report_time" in fixtures_collection[f"{fixture}_log"]
        assert "duration_seconds" in fixtures_collection[f"{fixture}_log"]
        assert "mask_state" not in fixtures_collection[f"{fixture}_log"]

    # verify if exclude still matches fixture
    for fixture in exclude:
        assert fixture not in fixtures_collection

    assert "collection_aborted_log" not in fixtures_collection
    assert ANONYMIZATION_ERROR_KEY not in fixtures_collection

    # compare fixture_collection data to file content
    for endpoint, file in endpoint_to_fixture_file.items():
        if endpoint not in exclude and file in files:
            assert "mask_state" not in fixtures_collection[f"{endpoint}_log"]
            try:
                content = await load_json_fixture(version, file)
                assert fixtures_collection[endpoint] == content
            except orjson.JSONDecodeError:
                string_content = await load_fixture(version, file)
                string_content = string_content.replace("\n", "")
                assert fixtures_collection[endpoint] == string_content

    # test with regular anonymization and no errors
    fixtures_collection = await envoy.fixture_collection(
        mask_serials=True,
    )
    assert fixtures_collection
    for fixture in FIXTURE_LIST:
        assert f"{fixture}_log" in fixtures_collection
        assert "code" in fixtures_collection[f"{fixture}_log"]
        assert "report_time" in fixtures_collection[f"{fixture}_log"]
        assert "duration_seconds" in fixtures_collection[f"{fixture}_log"]
        if fixture not in exclude:
            assert "mask_state" in fixtures_collection[f"{fixture}_log"]

    assert "collection_aborted_log" not in fixtures_collection

    # Verify timeout will end fixture collection
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/api/v1/production",
        exception=asyncio.TimeoutError("Test timeoutexception"),
    )
    fixtures_collection = await envoy.fixture_collection()

    # validate we have an error entry and failed endpoint is not in the list
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
    )
    # test content-type application/json fallback to text
    invalid_json = "invalid json"
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/test/my/invalid_endpoint",
        body=invalid_json,
        status=200,
    )
    # test with missing endpoints
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/ivp/ensemble/power",
        status=404,
        body="<html>404</html>",
    )
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/ivp/ensemble/inventory",
        status=404,
        body="<html>404</html>",
    )

    fixtures_collection = await envoy.fixture_collection(
        ["/test/my/endpoint", "/test/my/invalid_endpoint"], mask_serials=True
    )

    assert fixtures_collection
    # verify additional endpoints are in result
    assert "/test/my/endpoint" in fixtures_collection
    assert "/test/my/endpoint_log" in fixtures_collection
    assert fixtures_collection["/test/my/endpoint"] == test_json
    assert "/test/my/invalid_endpoint" in fixtures_collection
    assert "/test/my/invalid_endpoint_log" in fixtures_collection
    assert fixtures_collection["/test/my/invalid_endpoint"] == invalid_json
    assert "<sn>923456789012</sn>" in fixtures_collection["/info"]

    # verify handling of missing endpoints
    assert "/ivp/ensemble/power_log" in fixtures_collection
    assert ("code", 404) in fixtures_collection["/ivp/ensemble/power_log"].items()
    assert "/ivp/ensemble/inventory_log" in fixtures_collection
    assert ("code", 404) in fixtures_collection["/ivp/ensemble/inventory_log"].items()

    # test automatic serial anonymization in regular mode with serial sequencing error

    with patch("pyenphase.anonymization.TYPE_SERIALS", {"NEW": "1", "OLD": 2}):
        fixtures_collection = await envoy.fixture_collection(
            ["/test/my/endpoint", "/test/my/invalid_endpoint"], mask_serials=True
        )
    assert ANONYMIZATION_ERROR_KEY in fixtures_collection
    assert (
        "Error during serial sequencing KeyError"
        in fixtures_collection[ANONYMIZATION_ERROR_KEY]
    )
    assert "/info" in fixtures_collection

    # test automatic serial anonymization in strict mode with serial sequencing error

    with patch("pyenphase.anonymization.TYPE_SERIALS", {"NEW": "1", "OLD": 2}):
        fixtures_collection = await envoy.fixture_collection(
            ["/test/my/endpoint", "/test/my/invalid_endpoint"],
            mask_serials=True,
            strict_masking=True,
        )
    assert ANONYMIZATION_ERROR_KEY in fixtures_collection
    assert (
        "Error during serial sequencing KeyError"
        in fixtures_collection[ANONYMIZATION_ERROR_KEY]
    )
    assert "/info" not in fixtures_collection

    anonymized_fixtures: dict[str, Any] = {ANONYMIZATION_ERROR_KEY: "Yes"}
    with patch("pyenphase.envoy.anonymize_serials", return_value=anonymized_fixtures):
        fixtures_collection = await envoy.fixture_collection(
            mask_serials=True,
        )
    assert ANONYMIZATION_ERROR_KEY in fixtures_collection
    assert fixtures_collection == anonymized_fixtures


@pytest.mark.asyncio
async def test_fixture_collection_unauthorized() -> None:
    """Test fixture file data collection while not authorized."""
    envoy = Envoy("127.0.0.1")
    with pytest.raises(EnvoyAuthenticationRequired):
        await envoy.fixture_collection()
    await envoy.close()


@patch("pyenphase.anonymization.TYPE_SERIALS", PATCHED_SERIALS)
@patch("pyenphase.anonymization.ENVOY_SERIAL", PATCHED_ENVOY_SERIAL)
@pytest.mark.parametrize(
    ("version", "exclude"),
    TEST_FIXTURES,
    ids=TEST_IDS,
)
@pytest.mark.asyncio
async def test_fixture_collection_entries_unauthorized(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    exclude: list[str],  # exclude from fixture tests
) -> None:
    """Test fixture file data collection."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    envoy = await get_mock_envoy(test_client_session)

    with patch(
        "pyenphase.Envoy._request",
        side_effect=EnvoyAuthenticationRequired("Test all failed"),
    ):
        fixtures_collection = await envoy.fixture_collection(
            skip_standard=True, additional_endpoints=["/info"]
        )

    assert "collection_aborted_log" in fixtures_collection
    assert (
        "Error getting fixture endpoints, all failed"
        in fixtures_collection["collection_aborted_log"]
    )
    assert fixtures_collection["/info_log"]["error"] == "Test all failed"


@patch("pyenphase.anonymization.TYPE_SERIALS", PATCHED_SERIALS)
@patch("pyenphase.anonymization.ENVOY_SERIAL", PATCHED_ENVOY_SERIAL)
@pytest.mark.parametrize(
    ("version", "exclude"),
    TEST_FIXTURES,
    ids=TEST_IDS,
)
@pytest.mark.asyncio
async def test_fixture_collection_entries_clienterrors(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    exclude: list[str],  # exclude from fixture tests
) -> None:
    """Test fixture file data collection client errors don't leak headers."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    envoy = await get_mock_envoy(test_client_session)

    with patch(
        "pyenphase.Envoy._request",
        side_effect=aiohttp.ClientResponseError(
            RequestInfo(
                url="http://example.com",
                method="GET",
                headers={
                    "Host": "www.example.com",
                    "Connection": "keep-alive",
                    "secret": "very secret secret",
                },
                real_url="http://example.com",
            ),
            None,
            status=-27,
        ),
    ):
        fixtures_collection = await envoy.fixture_collection(
            skip_standard=True, additional_endpoints=["/info"]
        )
    # one endpoint only and failing so all failed
    assert "collection_aborted_log" in fixtures_collection
    assert (
        "Error getting fixture endpoints, all failed"
        in fixtures_collection["collection_aborted_log"]
    )
    # verify header is not in endpoint_log error text
    assert fixtures_collection["/info_log"]["error"] == "-27"
