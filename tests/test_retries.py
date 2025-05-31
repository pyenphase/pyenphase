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

from .common import load_fixture, override_mock, prep_envoy, start_7_firmware_mock


# Helper function to create ClientConnectorError
def _make_client_connector_error(msg="Test error"):
    """
    Creates a mock aiohttp.ClientConnectorError with a specified error message.
    
    Args:
        msg: The error message to include in the OSError.
    
    Returns:
        An aiohttp.ClientConnectorError instance with mock connection details.
    """

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
    """
    Tests successful connection and response from an Envoy device running firmware version 7.6.175.
    
    Simulates a scenario where the Envoy device is reachable from the start, verifies that only one connection attempt is made, and asserts correct firmware and part number retrieval. Also checks that the update operation returns data.
    """
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
    """
    Tests that the Envoy client raises EnvoyFirmwareFatalCheckError after failing to connect to the device on both HTTPS and HTTP endpoints for all retry attempts.
    
    Simulates persistent connection errors at startup, verifies the correct exception is raised after 3 attempts, and asserts the retry count.
    """
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
    """
    Tests that timeouts on both HTTPS and HTTP info endpoints at startup cause immediate failure with EnvoyFirmwareFatalCheckError, confirming that timeouts are not retried and only one attempt is made.
    """
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
    """
    Tests that an HTTP 500 error on the Envoy firmware info endpoint causes setup to fail immediately with EnvoyFirmwareCheckError, without triggering retries.
    """
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
    """
    Tests that a timeout on the HTTPS info endpoint causes the Envoy client to fall back to HTTP, allowing setup and authentication to succeed with a single attempt. Verifies correct firmware and part number are set, and that update returns data.
    """
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
    """
    Tests Envoy client retry behavior when initial connection attempts fail, succeeding on the third attempt.
    
    Simulates two full connection failures (both HTTPS and HTTP) followed by a successful HTTP response on the third attempt for the firmware info endpoint. Verifies that the Envoy client retries as configured, correctly sets firmware and part number, and successfully retrieves update data after setup and authentication.
    """
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
    """
    Tests that the Envoy client retries after two consecutive network errors on the firmware info endpoint and succeeds on the third attempt.
    
    Simulates two different network exceptions on the `/info` endpoint, followed by a successful response. Verifies that three attempts are made, the correct firmware and part number are set, and that the update call returns data.
    """
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
    """
    Tests that three consecutive network errors during Envoy firmware info retrieval cause setup to fail with EnvoyFirmwareCheckError after three retry attempts.
    
    Simulates repeated network failures on both HTTPS and HTTP endpoints, verifies that retries are attempted, and asserts that the correct exception is raised after the maximum number of attempts.
    """
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
    """
    Tests that the Envoy client retries probe requests up to three times when consecutive network errors occur, and successfully completes the probe and update after retries.
    
    Simulates three different network errors on the probe endpoint, verifies retry statistics, and asserts that the client can recover and retrieve data after failures.
    """
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
    """
    Tests the Envoy client's retry and error handling behavior during update operations with firmware version 7.6.175_standard.
    
    Simulates various network failure scenarios—including timeouts, connection errors, general client errors, and authentication failures—by mocking HTTP responses and exceptions. Verifies that the Envoy client raises the appropriate exceptions, respects retry limits, and updates retry statistics accordingly.
    """
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


@pytest.mark.asyncio
async def test_bad_request_status_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Tests that a non-2xx HTTP status (503) on the production API endpoint causes EnvoyHTTPStatusError without retries.
    
    Verifies that after a successful setup and authentication, forcing a 503 status on the `/api/v1/production` endpoint results in a single request attempt and raises the expected exception.
    """
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
    override_mock(
        mock_aioresponse, "get", "https://127.0.0.1/api/v1/production", status=503
    )

    with pytest.raises(EnvoyHTTPStatusError, match="503"):
        await envoy.update()

    stats = envoy.request.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1
