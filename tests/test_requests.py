"""Test envoy request methods: _json_request"""

import asyncio
import logging
from unittest.mock import AsyncMock, patch

import aiohttp
import orjson
import pytest
from aioresponses import aioresponses

from pyenphase import EnvoyCommunicationError
from pyenphase.const import ENDPOINT_URL_HOME
from pyenphase.exceptions import EnvoyHTTPStatusError

from .common import (
    endpoint_path,
    get_mock_envoy,
    override_mock,
    prep_envoy,
    start_7_firmware_mock,
    temporary_log_level,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    ("error", "match", "close_session"),
    [
        (  # test _request error
            asyncio.TimeoutError("Test _json_request"),
            r"Timeout \(request\) Test _json_request",
            False,
        ),
        (  # test _request error
            aiohttp.ClientError("Test _json_request"),
            r"aiohttp ClientError \(request\) Test _json_request",
            False,
        ),
        (  # test _request error
            RuntimeError("Test _json_request runtimerror not closed"),
            "Test _json_request runtimerror not closed",
            False,
        ),
        (  # test _request error with session closed
            RuntimeError("Test _json_request"),
            r"RuntimeError \(request\) Session is closed",
            True,
        ),
    ],
    ids=[
        "timeout",
        "client",
        "runtime_open",
        "runtime_closed",
    ],
)
@pytest.mark.asyncio
async def test_json_request_error_on_request(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    caplog: pytest.LogCaptureFixture,
    error: Exception,
    match: str,
    close_session: bool,
) -> None:
    """Test _json_request request call error handling."""
    start_7_firmware_mock(mock_aioresponse)
    version = "7.6.175"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    full_host = endpoint_path(version, "127.0.0.1")
    envoy = await get_mock_envoy(test_client_session)
    caplog.set_level(logging.DEBUG)

    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}{ENDPOINT_URL_HOME}",
        status=200,
        exception=error,
        repeat=True,
    )

    if close_session:
        await envoy._client.close()

    with pytest.raises((EnvoyCommunicationError, RuntimeError), match=match):
        await envoy._json_request(ENDPOINT_URL_HOME, None)


@pytest.mark.parametrize(
    ("error", "match", "http_status", "close_session"),  # error to test
    [
        (asyncio.TimeoutError, r"Timeout \(response.read\)", 200, False),
        (aiohttp.ClientError, r"aiohttp ClientError \(response.read\)", 200, False),
        (NotImplementedError("_json_request"), "_json_request", 200, False),
        (RuntimeError("_json_request"), "_json_request", 200, False),
        (RuntimeError, r"RuntimeError \(request\) Session is closed", 200, True),
        (asyncio.TimeoutError, r"Timeout \(http status\)", 350, False),
        (aiohttp.ClientError, r"aiohttp ClientError \(http status\)", 350, False),
        (RuntimeError("_json_request"), "_json_request", 350, False),
        (RuntimeError, r"RuntimeError \(request\) Session is closed", 350, True),
    ],
    ids=[
        "timeout_200",
        "client_200",
        "notimplemented_200",
        "runtime_200",
        "runtime_closed_200",
        "timeout_350",
        "client_350",
        "runtime_350",
        "runtime_closed_350",
    ],
)
@pytest.mark.asyncio
async def test_json_request_response_read(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    caplog: pytest.LogCaptureFixture,
    error: Exception,
    match: str,
    http_status: int,
    close_session: bool,
) -> None:
    """Test _json_request error on response.read."""
    # we want to test the response.read RuntimeError of _json_request
    # if debug is enabled the debug statement in envoy._request
    # already perform a request.read which preempts our test
    # disable debug here so RuntimeError failure is caught by the
    # _json_request request.read and not by the _json_request
    # try except around _request call.
    with temporary_log_level("pyenphase", logging.WARN):
        start_7_firmware_mock(mock_aioresponse)
        version = "7.6.175"
        await prep_envoy(mock_aioresponse, "127.0.0.1", version)
        full_host = endpoint_path(version, "127.0.0.1")
        envoy = await get_mock_envoy(test_client_session)
        caplog.set_level(logging.WARN)

        override_mock(
            mock_aioresponse,
            "get",
            f"{full_host}{ENDPOINT_URL_HOME}",
            status=http_status,
            repeat=True,
        )

        if close_session:
            await envoy._client.close()

        # mock clientresponse.read to return error
        error_mock = AsyncMock(side_effect=error)
        with (
            patch.object(aiohttp.ClientResponse, "read", error_mock),
            pytest.raises(
                (EnvoyCommunicationError, RuntimeError, EnvoyHTTPStatusError),
                match=match,
            ),
        ):
            await envoy._json_request(ENDPOINT_URL_HOME, None)


@pytest.mark.asyncio
async def test_json_request_http_and_decode_error(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test _json_request http non-200 and decode errors."""
    start_7_firmware_mock(mock_aioresponse)
    version = "7.6.175"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    full_host = endpoint_path(version, "127.0.0.1")
    envoy = await get_mock_envoy(test_client_session)

    caplog.set_level(logging.DEBUG)

    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}{ENDPOINT_URL_HOME}",
        status=350,
        repeat=True,
        body="<html><body>Not Found</body></html>",
    )
    with pytest.raises(EnvoyHTTPStatusError):
        await envoy._json_request(ENDPOINT_URL_HOME, None)

    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}{ENDPOINT_URL_HOME}",
        status=200,
        repeat=True,
        body=b"<html><body>Not Found</body></html>",
    )

    with pytest.raises(EnvoyCommunicationError):
        await envoy._json_request(ENDPOINT_URL_HOME, None)


@pytest.mark.asyncio
async def test_json_request_data_return(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test _json_request http non-200 and decode errors."""
    start_7_firmware_mock(mock_aioresponse)
    version = "7.6.175"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    full_host = endpoint_path(version, "127.0.0.1")
    envoy = await get_mock_envoy(test_client_session)

    caplog.set_level(logging.DEBUG)

    request_json = '{"test": "for success", "result": "should_be_fine"}'
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}{ENDPOINT_URL_HOME}",
        status=200,
        repeat=True,
        body=request_json,
    )
    request_result = await envoy._json_request(ENDPOINT_URL_HOME, None)
    assert request_result == orjson.loads(request_json)
