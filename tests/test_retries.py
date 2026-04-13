"""Test tenacity retry functioning."""

import asyncio
import logging
from typing import Any

import aiohttp
import pytest
from aioresponses import aioresponses
from tenacity import wait_none

from pyenphase import Envoy
from pyenphase.const import (
    DEFAULT_MAX_REQUEST_ATTEMPTS,
    MAX_PROBE_REQUEST_ATTEMPTS,
)
from pyenphase.exceptions import (
    EnvoyAuthenticationRequired,
    EnvoyCommunicationError,
    EnvoyFirmwareCheckError,
    EnvoyFirmwareFatalCheckError,
    EnvoyHTTPStatusError,
)

from .common import load_fixture, override_mock, prep_envoy, start_7_firmware_mock


# Helper function to create ClientConnectorError
def _make_client_connector_error(msg="Test error"):
    """Create a ClientConnectorError that can be converted to string."""

    # Create a simple mock object with the minimal attributes needed
    class MockConnKey:
        ssl = True
        host = "127.0.0.1"
        port = 443

    return aiohttp.ClientConnectorError(
        connection_key=MockConnKey(), os_error=OSError(msg)
    )


LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_full_connected_from_start_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test envoy connected and replying from start"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test
    # retries are defined by MAX_PROBE_REQUEST_ATTEMPTS and MAX_PROBE_REQUEST_DELAY
    envoy._firmware._get_info.retry.wait = wait_none()

    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Ensure that there was 1 attempt only.
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1

    assert envoy.firmware == "7.6.175"
    assert envoy.part_number == "800-00656-r06"

    data = await envoy.update()
    assert data


@pytest.mark.asyncio
async def test_full_disconnected_from_start_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test envoy disconnect at start, should return EnvoyFirmwareFatalCheckError."""
    start_7_firmware_mock(mock_aioresponse)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    # retries are defined by MAX_PROBE_REQUEST_ATTEMPTS and MAX_PROBE_REQUEST_DELAY
    envoy._firmware._get_info.retry.wait = wait_none()

    # Mock both HTTPS and HTTP since firmware code falls back to HTTP
    mock_aioresponse.get(
        "https://127.0.0.1/info",
        exception=_make_client_connector_error("Test timeoutexception"),
        repeat=True,
    )
    mock_aioresponse.get(
        "http://127.0.0.1/info",
        exception=_make_client_connector_error("Test timeoutexception"),
        repeat=True,
    )

    with pytest.raises(
        EnvoyFirmwareFatalCheckError, match="Unable to connect to Envoy"
    ):
        await envoy.setup()

    # Ensure there were MAX_PROBE_REQUEST_ATTEMPTS attempts.
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == MAX_PROBE_REQUEST_ATTEMPTS


@pytest.mark.asyncio
async def test_2_timeout_from_start_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test envoy timeout at start, timeout is not in retry loop."""
    start_7_firmware_mock(mock_aioresponse)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    # retries are defined by MAX_PROBE_REQUEST_ATTEMPTS and MAX_PROBE_REQUEST_DELAY
    envoy._firmware._get_info.retry.wait = wait_none()

    # Mock both HTTPS and HTTP since firmware code falls back to HTTP
    mock_aioresponse.get(
        "https://127.0.0.1/info",
        exception=asyncio.TimeoutError("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "http://127.0.0.1/info", exception=asyncio.TimeoutError("Test timeoutexception")
    )

    with pytest.raises(
        EnvoyFirmwareFatalCheckError, match="Timeout connecting to Envoy"
    ):
        await envoy.setup()

    # Ensure there was only 1 attempt
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1


@pytest.mark.asyncio
async def test_httperror_from_start_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test envoy httperror at start, is not in retry loop."""
    start_7_firmware_mock(mock_aioresponse)
    # Don't call prep_envoy because we want to control the /info response

    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    # retries are defined by MAX_PROBE_REQUEST_ATTEMPTS and MAX_PROBE_REQUEST_DELAY
    envoy._firmware._get_info.retry.wait = wait_none()

    # The test expects no retries, which means we need to trigger the code path
    # that doesn't retry. Since _get_info retries all https exceptions on http, we need to
    # make the first https attempt succeeds but return bad data that causes setup() to fail
    mock_aioresponse.get(
        "https://127.0.0.1/info",
        status=500,  # Return HTTP error status
        body="Server Error",
    )

    with pytest.raises(EnvoyFirmwareCheckError, match="500"):
        await envoy.setup()

    # Ensure there was 1 attempt.
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1


@pytest.mark.asyncio
async def test_1_timeout_from_start_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test envoy timeout at start, timeout is not in retry loop but tries http after https."""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    # retries are defined by MAX_PROBE_REQUEST_ATTEMPTS and MAX_PROBE_REQUEST_DELAY
    envoy._firmware._get_info.retry.wait = wait_none()

    # Mock both HTTPS and HTTP since firmware code falls back to HTTP
    mock_aioresponse.get(
        "https://127.0.0.1/info",
        exception=asyncio.TimeoutError("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "http://127.0.0.1/info", status=200, body=await load_fixture(version, "info")
    )

    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Ensure there was 1 attempt.
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1

    assert envoy.firmware == "7.6.175"
    assert envoy.part_number == "800-00656-r06"

    data = await envoy.update()
    assert data


@pytest.mark.asyncio
async def test_5_not_connected_at_start_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test 5 connection failures at start and last one works"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    # Don't call prep_envoy because we want to control the /info response

    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    # retries are defined by MAX_PROBE_REQUEST_ATTEMPTS and MAX_PROBE_REQUEST_DELAY
    envoy._firmware._get_info.retry.wait = wait_none()

    # Each retry attempt tries HTTPS first, then falls back to HTTP
    # We want 2 full failures (4 requests) then success on the 3rd attempt (request 5-6)
    # Attempt 1: HTTPS fails, HTTP fails
    mock_aioresponse.get(
        "https://127.0.0.1/info",
        exception=_make_client_connector_error("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "http://127.0.0.1/info",
        exception=_make_client_connector_error("Test timeoutexception"),
    )
    # Attempt 2: HTTPS fails, HTTP fails
    mock_aioresponse.get(
        "https://127.0.0.1/info",
        exception=_make_client_connector_error("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "http://127.0.0.1/info",
        exception=_make_client_connector_error("Test timeoutexception"),
    )
    # Attempt 3: HTTPS fails, HTTP succeeds
    mock_aioresponse.get(
        "https://127.0.0.1/info",
        exception=_make_client_connector_error("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "http://127.0.0.1/info", status=200, body=await load_fixture(version, "info")
    )
    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Ensure that there were retries.
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 3

    assert envoy.firmware == "7.6.175"
    assert envoy.part_number == "800-00656-r06"

    # Now set up the other endpoints for the update call
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    data = await envoy.update()
    assert data


@pytest.mark.asyncio
async def test_2_network_errors_at_start_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test 2 network error failures at start and 3th works"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    # Don't call prep_envoy because we want to control the /info response

    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    # retries are defined by MAX_PROBE_REQUEST_ATTEMPTS and MAX_PROBE_REQUEST_DELAY
    envoy._firmware._get_info.retry.wait = wait_none()

    # we need 2 side effects for each try as https and then http is attempted
    mock_aioresponse.get(
        "https://127.0.0.1/info", exception=aiohttp.ClientError("Test timeoutexception")
    )
    mock_aioresponse.get(
        "https://127.0.0.1/info",
        exception=_make_client_connector_error("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/info", status=200, body=await load_fixture(version, "info")
    )

    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Ensure that there were retries.
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 3

    assert envoy.firmware == "7.6.175"
    assert envoy.part_number == "800-00656-r06"

    # Now set up the other endpoints for the update call
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    data = await envoy.update()
    assert data


@pytest.mark.asyncio
async def test_network_errors_at_start_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test network error failures at start"""
    start_7_firmware_mock(mock_aioresponse)
    # Don't call prep_envoy because we want to control the /info response

    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    # retries are defined by MAX_PROBE_REQUEST_ATTEMPTS and MAX_PROBE_REQUEST_DELAY
    envoy._firmware._get_info.retry.wait = wait_none()

    # We need 3 failures, each could try HTTPS then HTTP fallback
    mock_aioresponse.get(
        "https://127.0.0.1/info",
        exception=aiohttp.ClientError("Test timeoutexception"),
        repeat=True,
    )

    with pytest.raises(
        EnvoyFirmwareCheckError, match="Unable to query firmware version"
    ):
        await envoy.setup()

    # Ensure that there were retries.
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == MAX_PROBE_REQUEST_ATTEMPTS


@pytest.mark.asyncio
async def test_noconnection_at_probe_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test 3 network error failures at start"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    # retries are defined by MAX_PROBE_REQUEST_ATTEMPTS and MAX_PROBE_REQUEST_DELAY
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy.probe_request.retry.wait = wait_none()

    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Ensure there was 1 attempt.
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1

    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/admin/lib/tariff",
        exception=aiohttp.ClientError("Test timeoutexception"),
        repeat=True,
    )

    await envoy.probe()

    stats = envoy.probe_request.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == MAX_PROBE_REQUEST_ATTEMPTS


@pytest.mark.asyncio
async def test_noconnection_at_update_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test network error failures at update"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    # retries are defined by MAX_PROBE_REQUEST_ATTEMPTS and MAX_PROBE_REQUEST_DELAY
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy.request.retry.wait = wait_none()

    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Ensure there was 1 attempt.
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1

    await envoy.probe()

    stats = envoy.probe_request.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1

    # Test timeout exceptions - need to override existing mock
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production",
        exception=asyncio.TimeoutError("Test timeoutexception"),
        repeat=True,
    )

    # Clear endpoint cache to force retries
    envoy._endpoint_cache.clear()

    with pytest.raises(EnvoyCommunicationError, match="Timeout"):
        await envoy.update()

    # Don't check statistics here - they get reset between update() calls

    # Test connection errors
    envoy._endpoint_cache.clear()
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production",
        exception=_make_client_connector_error("Test timeoutexception"),
        repeat=True,
    )

    with pytest.raises(EnvoyCommunicationError, match="aiohttp ClientError"):
        await envoy.update()

    # Check statistics immediately after the failed update
    stats = envoy.request.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == DEFAULT_MAX_REQUEST_ATTEMPTS

    # Test general client errors (equivalent to RemoteProtocolError)
    envoy._endpoint_cache.clear()
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production",
        exception=aiohttp.ClientError("Test timeoutexception"),
        repeat=True,
    )

    with pytest.raises(EnvoyCommunicationError, match="aiohttp ClientError"):
        await envoy.update()

    stats = envoy.request.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == DEFAULT_MAX_REQUEST_ATTEMPTS

    # Test network errors (using ClientConnectorError as equivalent)
    envoy._endpoint_cache.clear()
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production",
        exception=_make_client_connector_error("Test timeoutexception"),
        repeat=True,
    )

    with pytest.raises(EnvoyCommunicationError, match="aiohttp ClientError"):
        await envoy.update()

    stats = envoy.request.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == DEFAULT_MAX_REQUEST_ATTEMPTS

    # other error EnvoyAuthenticationRequired should end cycle
    # First mock will be consumed, then the EnvoyAuthenticationRequired will stop retries
    envoy._endpoint_cache.clear()
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production",
        exception=_make_client_connector_error("Test timeoutexception"),
    )
    # We can't directly mock EnvoyAuthenticationRequired from aioresponses,
    # so we'll use a 401 status to trigger it
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production",
        status=401,
        payload={"message": "Test authentication required"},
    )
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production",
        exception=_make_client_connector_error("Should not reach this"),
    )

    with pytest.raises(EnvoyAuthenticationRequired):
        await envoy.update()

    stats = envoy.request.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 2


@pytest.mark.asyncio
async def test_bad_request_status_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test request status not between 200-300."""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    # retries are defined by MAX_PROBE_REQUEST_ATTEMPTS and MAX_PROBE_REQUEST_DELAY
    envoy._firmware._get_info.retry.wait = wait_none()

    await envoy.setup()
    await envoy.authenticate("username", "password")

    data = await envoy.update()
    assert data

    # force status 503 on /api/vi/production
    # test status results in EnvoyHTTPStatusError
    override_mock(
        mock_aioresponse, "get", "https://127.0.0.1/api/v1/production", status=503
    )

    with pytest.raises(EnvoyHTTPStatusError, match="503"):
        await envoy.update()

    stats = envoy.request.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1


@pytest.mark.asyncio
async def test_retry_policy(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Test envoy retry policy."""
    version = "7.6.175_with_cts"
    start_7_firmware_mock(mock_aioresponse)
    envoy = Envoy("127.0.0.1", client=test_client_session)

    # remove the waits between retries for this test and set known retries
    # retries are defined by MAX_PROBE_REQUEST_ATTEMPTS and MAX_PROBE_REQUEST_DELAY
    envoy._firmware._get_info.retry.wait = wait_none()

    # verify MAX_PROBE_REQUEST_ATTEMPTS are used in fw setup
    # Mock both HTTPS and HTTP since firmware code falls back to HTTP
    mock_aioresponse.get(
        "https://127.0.0.1/info",
        exception=_make_client_connector_error("Test timeoutexception"),
        repeat=True,
    )
    mock_aioresponse.get(
        "http://127.0.0.1/info",
        exception=_make_client_connector_error("Test timeoutexception"),
        repeat=True,
    )

    with pytest.raises(EnvoyFirmwareFatalCheckError):
        await envoy.setup()

    # verify probe attempts where used
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == MAX_PROBE_REQUEST_ATTEMPTS

    # restore info mock
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/info",
        status=200,
        body=await load_fixture(version, "info"),
        repeat=True,
    )

    override_mock(
        mock_aioresponse,
        "get",
        "http://127.0.0.1/info",
        status=200,
        body=await load_fixture(version, "info"),
        repeat=True,
    )
    # setup all other mocks
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    await envoy.setup()
    await envoy.authenticate("username", "password")

    # do initial probe to get updaters identified
    await envoy.probe()

    # verify DEFAULT_MAX_REQUEST_ATTEMPTS are used for update
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters",
        exception=asyncio.TimeoutError("Test timeoutexception"),
        repeat=True,
    )
    with pytest.raises(EnvoyCommunicationError):
        await envoy.update()

    # verify custom attempts where used
    stats = envoy.request.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == DEFAULT_MAX_REQUEST_ATTEMPTS

    # Add second envoy instance
    mock_aioresponse.get("https://127.0.0.2/auth/check_jwt", status=200, repeat=True)
    envoy2 = Envoy("127.0.0.2", client=test_client_session)
    await prep_envoy(mock_aioresponse, "127.0.0.2", version)
    await envoy2.setup()
    await envoy2.authenticate("username", "password")

    data2 = await envoy2.update()
    assert data2

    # set retry policy to use custom retries on first envoy
    envoy.set_retry_policy(max_delay=600, max_attempts=8)
    with pytest.raises(EnvoyCommunicationError):
        await envoy.update()

    # verify custom attempts where used
    stats = envoy.request.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 8

    # verify custom retries are used on second envoy as well
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.2/ivp/meters",
        exception=asyncio.TimeoutError("Test timeoutexception"),
        repeat=True,
    )
    with pytest.raises(EnvoyCommunicationError):
        await envoy2.update()

    # verify custom attempts where used on second envoy as well
    stats2: dict[str, Any] = envoy2.request.statistics
    assert "attempt_number" in stats2
    assert stats2["attempt_number"] == 8
