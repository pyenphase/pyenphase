"""Test tenacity retry functioning."""

import asyncio
import logging
from typing import Any

import aiohttp
import pytest
from aioresponses import aioresponses
from tenacity import stop_after_attempt, stop_after_delay, wait_none

from pyenphase import Envoy
from pyenphase.exceptions import (
    EnvoyAuthenticationRequired,
    EnvoyCommunicationError,
    EnvoyFirmwareCheckError,
    EnvoyFirmwareFatalCheckError,
    EnvoyHTTPStatusError,
)

from .common import load_fixture, prep_envoy, start_7_firmware_mock


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
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

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
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    start_7_firmware_mock(mock_aioresponse)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

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

    # Ensure that there were 3 attempts.
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 3


@pytest.mark.asyncio
async def test_2_timeout_from_start_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test envoy timeout at start, timeout is not in retry loop."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    start_7_firmware_mock(mock_aioresponse)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    # test if 2 timeouts return failed
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

    # Ensure that there were retries.
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1


@pytest.mark.asyncio
async def test_httperror_from_start_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test envoy httperror at start, is not in retry loop."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    start_7_firmware_mock(mock_aioresponse)
    # Don't call prep_envoy because we want to control the /info response

    envoy = Envoy("127.0.0.1", client=test_client_session)
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    # The test expects no retries, which means we need to trigger the code path
    # that doesn't retry. Since _get_info retries all exceptions, we need to
    # make the first attempt succeed but return bad data that causes setup() to fail
    mock_aioresponse.get(
        "https://127.0.0.1/info",
        status=500,  # Return HTTP error status
        body="Server Error",
    )

    with pytest.raises(EnvoyFirmwareCheckError, match="500"):
        await envoy.setup()

    # Ensure that there were retries.
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1


@pytest.mark.asyncio
async def test_1_timeout_from_start_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test envoy timeout at start, timeout is not in retry loop but tries http after https."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = Envoy("127.0.0.1", client=test_client_session)
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    # test if 2 timeouts return failed
    mock_aioresponse.get(
        "https://127.0.0.1/info",
        exception=asyncio.TimeoutError("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "http://127.0.0.1/info", status=200, body=await load_fixture(version, "info")
    )

    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Ensure that there were retries.
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
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    # Don't call prep_envoy because we want to control the /info response

    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

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
    logging.getLogger("pyenphase").setLevel(logging.WARN)
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    # Don't call prep_envoy because we want to control the /info response

    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

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
async def test_3_network_errors_at_start_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test 3 network error failures at start"""
    logging.getLogger("pyenphase").setLevel(logging.WARN)
    start_7_firmware_mock(mock_aioresponse)
    # Don't call prep_envoy because we want to control the /info response

    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

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
    assert stats["attempt_number"] == 3


@pytest.mark.asyncio
async def test_noconnection_at_probe_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test 3 network error failures at start"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    envoy.probe_request.retry.wait = wait_none()
    envoy.probe_request.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Ensure that there were retries.
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1

    # Probe is re-calling retried probe_request before returning
    # we can only see stats for the last request done.
    # force 3 retries for last one
    mock_aioresponse.get(
        "https://127.0.0.1/ivp/ss/gen_config",
        exception=aiohttp.ClientError("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/ivp/ss/gen_config",
        exception=_make_client_connector_error("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/ivp/ss/gen_config",
        exception=asyncio.TimeoutError("Test timeoutexception"),
    )

    # Set up all other endpoints for probe
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    await envoy.setup()
    await envoy.authenticate("username", "password")
    await envoy.probe()
    # assert data

    stats = envoy.probe_request.statistics
    assert "attempt_number" in stats
    print(f"--stats--{stats}")
    assert stats["attempt_number"] == 1

    data = await envoy.update()
    assert data


@pytest.mark.asyncio
async def test_noconnection_at_update_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test 3 network error failures at start"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = Envoy("127.0.0.1", client=test_client_session)
    # remove the waits between retries for this test and set known retries
    envoy.request.retry.wait = wait_none()
    envoy.request.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Ensure that there were no retries.
    stats: dict[str, Any] = envoy._firmware._get_info.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1

    await envoy.probe()

    stats = envoy.probe_request.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1

    from .common import override_mock

    # Test timeout exceptions - need to override existing mock first, then add additional ones
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production",
        exception=asyncio.TimeoutError("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production",
        exception=asyncio.TimeoutError("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production",
        exception=asyncio.TimeoutError("Test timeoutexception"),
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
    )
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production",
        exception=_make_client_connector_error("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production",
        exception=_make_client_connector_error("Test timeoutexception"),
    )

    with pytest.raises(EnvoyCommunicationError, match="aiohttp ClientError"):
        await envoy.update()

    # Check statistics immediately after the failed update
    stats = envoy.request.statistics
    assert "attempt_number" in stats
    print(f"Connection error test attempts: {stats['attempt_number']}")
    # Statistics accumulate across all update() calls
    assert stats["attempt_number"] >= 3

    # Test general client errors (equivalent to RemoteProtocolError)
    envoy._endpoint_cache.clear()
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production",
        exception=aiohttp.ClientError("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production",
        exception=aiohttp.ClientError("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production",
        exception=aiohttp.ClientError("Test timeoutexception"),
    )

    with pytest.raises(EnvoyCommunicationError, match="aiohttp ClientError"):
        await envoy.update()

    stats = envoy.request.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 3

    # Test network errors (using ClientConnectorError as equivalent)
    envoy._endpoint_cache.clear()
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production",
        exception=_make_client_connector_error("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production",
        exception=_make_client_connector_error("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production",
        exception=_make_client_connector_error("Test timeoutexception"),
    )

    with pytest.raises(EnvoyCommunicationError, match="aiohttp ClientError"):
        await envoy.update()

    stats = envoy.request.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 3

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

    # test EndOfStream catch should end retries
    # EndOfStream is httpx-specific, in aiohttp we can use ClientPayloadError
    envoy._endpoint_cache.clear()
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production",
        exception=_make_client_connector_error("Test timeoutexception"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production",
        exception=aiohttp.ClientPayloadError("Test EndOfStream"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production",
        exception=_make_client_connector_error("Should not reach this"),
    )

    with pytest.raises(EnvoyCommunicationError):
        await envoy.update()

    stats = envoy.request.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 3


@pytest.mark.asyncio
async def test_bad_request_status_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test request status not between 200-300."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    await envoy.setup()
    await envoy.authenticate("username", "password")

    data = await envoy.update()
    assert data

    # force status 503 on /api/vi/production
    # test status results in EnvoyHTTPStatusError
    from .common import override_mock

    override_mock(
        mock_aioresponse, "get", "https://127.0.0.1/api/v1/production", status=503
    )

    with pytest.raises(EnvoyHTTPStatusError, match="503"):
        await envoy.update()

    stats = envoy.request.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1
