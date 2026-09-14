"""Test envoy request methods: _json_request"""

import asyncio
import logging
from typing import Any
from unittest.mock import AsyncMock, patch

import aiohttp
import orjson
import pytest
from aioresponses import aioresponses

from pyenphase import (
    EnvoyClientClosedError,
    EnvoyCommunicationError,
    EnvoyHTTPStatusError,
)
from pyenphase.const import ENDPOINT_URL_HOME

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
    ("error", "match", "expected_exception", "close_session"),
    [
        (  # test _request error
            asyncio.TimeoutError("Test _json_request"),
            r"Timeout \(request\) Test _json_request",
            EnvoyCommunicationError,
            False,
        ),
        (  # test _request error
            aiohttp.ClientError("Test _json_request"),
            r"aiohttp ClientError \(request\) Test _json_request",
            EnvoyCommunicationError,
            False,
        ),
        (  # test run time errors are not swallowed
            RuntimeError("Test _json_request runtimerror not closed"),
            "Test _json_request runtimerror not closed",
            RuntimeError,
            False,
        ),
        (  # test _request with session closed (actual error is not relevant)
            RuntimeError("Test _json_request runtimerror closed"),
            "Client closed before request is issued",
            EnvoyClientClosedError,
            True,
        ),
        (  # test _request with session closed is still caught as RuntimeError (actual error is not relevant)
            RuntimeError("Test _json_request runtimerror closed"),
            "Client closed before request is issued",
            RuntimeError,
            True,
        ),
        (  # test task cancellation is not swallowed
            asyncio.CancelledError("Test _json_request runtimerror canceled"),
            r"Test _json_request runtimerror canceled",
            asyncio.CancelledError,
            False,
        ),
    ],
    ids=[
        "timeout",
        "client",
        "runtime_open",
        "envoyclient_closed",
        "runtime_closed",
        "canceled_open",
    ],
)
@pytest.mark.asyncio
async def test_json_request_error_on_request(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    caplog: pytest.LogCaptureFixture,
    error: Exception,
    match: str,
    expected_exception: Any,
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

    with pytest.raises(expected_exception, match=match):
        await envoy._json_request(ENDPOINT_URL_HOME, None)


@pytest.mark.parametrize(
    ("error", "match", "expected_exception"),  # error to test
    [
        (
            asyncio.TimeoutError,
            r"Timeout \(response.read\)",
            EnvoyCommunicationError,
        ),
        (
            aiohttp.ClientError,
            r"aiohttp ClientError \(response.read\)",
            EnvoyCommunicationError,
        ),
        (NotImplementedError("_json_request"), "_json_request", NotImplementedError),
        (RuntimeError("_json_request"), "_json_request", RuntimeError),
        (
            asyncio.CancelledError("_json_request"),
            "_json_request",
            asyncio.CancelledError,
        ),
    ],
    ids=[
        "timeout",
        "client",
        "notimplemented",
        "runtime",
        "canceled",
    ],
)
@pytest.mark.asyncio
async def test_json_request_response_read(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    caplog: pytest.LogCaptureFixture,
    error: Exception,
    match: str,
    expected_exception: Any,
) -> None:
    """Test _json_request error on response.read."""
    # we want to test the response.read errors of _json_request
    # if debug is enabled the debug statement in envoy._request
    # already perform a request.read which preempts our test
    # disable debug here so failures are caught by the
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
            status=200,
            repeat=True,
        )

        # mock clientresponse.read to return error
        error_mock = AsyncMock(side_effect=error)
        with (
            patch.object(aiohttp.ClientResponse, "read", error_mock),
            pytest.raises(expected_exception, match=match),
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
    """Test _json_request json results."""
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
