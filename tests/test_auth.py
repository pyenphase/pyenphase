"""Test auth functions."""

import json
import logging
from os import listdir
from os.path import isfile, join
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import jwt
import pytest
from aioresponses import aioresponses

from pyenphase import Envoy, EnvoyTokenAuth
from pyenphase.auth import CloseConnectionNotOKMiddleware, EnvoyLegacyAuth
from pyenphase.const import URL_AUTH_CHECK_JWT
from pyenphase.exceptions import EnvoyAuthenticationError, EnvoyAuthenticationRequired

from .common import (
    get_mock_envoy,
    load_fixture,
    load_json_fixture,
    mock_response,
    prep_envoy,
    start_7_firmware_mock,
    temporary_log_level,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_wrong_auth_order_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test data collected fails before auth is done"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()

    with pytest.raises(EnvoyAuthenticationRequired):
        await envoy.update()

    # now in correct order
    await envoy.authenticate("username", "password")
    data = await envoy.update()
    assert data


@pytest.mark.asyncio
async def test_with_3_9_36_firmware_bad_auth(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Verify with 3.9.36 firmware with incorrect auth."""
    version = "3.9.36_bad_auth"
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/info",
        status=200,
        body=await load_fixture(version, "info"),
    )
    mock_response(
        mock_aioresponse, "get", "https://127.0.0.1/info.xml", status=200, body=""
    )
    mock_response(mock_aioresponse, "get", "https://127.0.0.1/production", status=404)
    mock_response(
        mock_aioresponse, "get", "https://127.0.0.1/production.json", status=404
    )
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production",
        status=401,
        payload=await load_json_fixture(version, "api_v1_production"),
    )
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production/inverters",
        status=200,
        payload=await load_json_fixture(version, "api_v1_production_inverters"),
    )
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/ensemble/inventory",
        status=200,
        payload=[],
    )

    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if "admin_lib_tariff" in files:
        try:
            json_data = await load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        mock_response(
            mock_aioresponse,
            "get",
            "https://127.0.0.1/admin/lib/tariff",
            status=200,
            payload=json_data,
        )
    else:
        mock_response(
            mock_aioresponse, "get", "https://127.0.0.1/admin/lib/tariff", status=401
        )

    mock_response(
        mock_aioresponse, "get", "https://127.0.0.1/ivp/meters", status=200, payload=[]
    )

    # Add the HTTP version of api/v1/production with 401 as well
    mock_response(
        mock_aioresponse,
        "get",
        "http://127.0.0.1/api/v1/production",
        status=401,
        payload=await load_json_fixture(version, "api_v1_production"),
    )

    # Add other required endpoints for the probe
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/production.json?details=1",
        status=404,
    )
    mock_response(
        mock_aioresponse,
        "get",
        "http://127.0.0.1/production.json?details=1",
        status=404,
    )
    mock_response(
        mock_aioresponse,
        "get",
        "http://127.0.0.1/production",
        status=200,
        body=await load_fixture(version, "production"),
    )

    with pytest.raises(EnvoyAuthenticationRequired):
        await get_mock_envoy(test_client_session)


@pytest.mark.asyncio
async def test_production_with_3_9_36_firmware_bad_auth(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test Authentication failed for http://127.0.0.1/api/v1/production."""
    version = "3.9.36_bad_auth"
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/info",
        status=200,
        body=await load_fixture(version, "info"),
    )
    mock_response(
        mock_aioresponse, "get", "https://127.0.0.1/info.xml", status=200, body=""
    )
    mock_response(mock_aioresponse, "get", "https://127.0.0.1/production", status=404)
    mock_response(
        mock_aioresponse, "get", "https://127.0.0.1/production.json", status=404
    )
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production",
        status=401,
        payload=await load_json_fixture(version, "api_v1_production"),
    )
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production/inverters",
        status=200,
        payload=await load_json_fixture(version, "api_v1_production_inverters"),
    )
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/ensemble/inventory",
        status=200,
        payload=[],
    )

    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if "admin_lib_tariff" in files:
        try:
            json_data = await load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        mock_response(
            mock_aioresponse,
            "get",
            "https://127.0.0.1/admin/lib/tariff",
            status=200,
            payload=json_data,
        )
    else:
        mock_response(
            mock_aioresponse, "get", "https://127.0.0.1/admin/lib/tariff", status=401
        )

    mock_response(
        mock_aioresponse, "get", "https://127.0.0.1/ivp/meters", status=200, payload=[]
    )

    # Add the HTTP version of api/v1/production with 401 as well
    mock_response(
        mock_aioresponse,
        "get",
        "http://127.0.0.1/api/v1/production",
        status=401,
        payload=await load_json_fixture(version, "api_v1_production"),
    )

    # Add other required endpoints for the probe
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/production.json?details=1",
        status=404,
    )
    mock_response(
        mock_aioresponse,
        "get",
        "http://127.0.0.1/production.json?details=1",
        status=404,
    )
    mock_response(
        mock_aioresponse,
        "get",
        "http://127.0.0.1/production",
        status=200,
        body=await load_fixture(version, "production"),
    )

    with pytest.raises(EnvoyAuthenticationRequired):
        await get_mock_envoy(test_client_session)


@pytest.mark.parametrize(
    (
        "username",
        "password",
    ),
    [
        ("installer", ""),
        ("envoy", ""),
    ],
)
@pytest.mark.asyncio
async def test_known_users_with_3_9_36_firmware(
    username: str,
    password: str,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Test successful login with known usernames."""
    version = "3.9.36"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    await envoy.authenticate(username, password)

    # test cookies function now cookies are not on request
    assert envoy.auth
    used_cookies = envoy.auth.cookies
    assert used_cookies == {}

    data = await envoy.update()
    assert data

    # cov: force test failure of Digest authentication for local Envoy.
    assert isinstance(envoy.auth, EnvoyLegacyAuth)
    envoy.auth.local_password = ""
    assert envoy.auth.auth is None


@pytest.mark.asyncio
async def test_unknown_user_with_3_9_36_firmware(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test Could not setup authentication object with 3.9.x"""
    version = "3.9.36"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    with pytest.raises(EnvoyAuthenticationRequired):
        await envoy.authenticate("unknown", None)


@pytest.mark.parametrize(
    (
        "username",
        "password",
    ),
    [
        ("installer", ""),
        ("envoy", ""),
        ("unknown", ""),
    ],
)
@pytest.mark.asyncio
async def test_blank_passwords_with_7_6_175_standard(
    username: str,
    password: str,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Test Could not setup authentication object with 7.6.x"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = Envoy("127.0.0.1", client=test_client_session)

    await envoy.setup()

    with pytest.raises(EnvoyAuthenticationRequired):
        await envoy.authenticate(username, password)


@pytest.mark.asyncio
async def test_no_token_obtained_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test Unable to obtain token for Envoy authentication"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    with patch("pyenphase.EnvoyTokenAuth._obtain_token", return_value=None):
        envoy = Envoy("127.0.0.1", client=test_client_session)
        await envoy.setup()
        with pytest.raises(EnvoyAuthenticationError):
            await envoy.authenticate("username", "password")


@pytest.mark.asyncio
async def test_jwt_failure_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test Unable to verify token for Envoy authentication"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1" + URL_AUTH_CHECK_JWT,
        reset=True,
        status=404,
        body="no jwt",
    )

    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    with pytest.raises(EnvoyAuthenticationError):
        await envoy.authenticate("username", "password")


@pytest.mark.asyncio
async def test_no_remote_login_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test Unable to login to Enlighten to obtain session ID from https://enlighten.enphaseenergy.com/login/login.json?"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    mock_response(
        mock_aioresponse,
        "post",
        "https://enlighten.enphaseenergy.com/login/login.json?",
        reset=True,
        status=500,
        payload={
            "session_id": "1234567890",
            "user_id": "1234567890",
            "user_name": "test",
            "first_name": "Test",
            "is_consumer": True,
            "manager_token": "1234567890",
        },
    )
    mock_response(
        mock_aioresponse,
        "post",
        "https://entrez.enphaseenergy.com/tokens",
        reset=True,
        status=500,
        body="token",
    )
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/auth/check_jwt",
        reset=True,
        status=200,
        payload={},
    )

    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    with pytest.raises(EnvoyAuthenticationError):
        await envoy.authenticate("username", "password")


@pytest.mark.asyncio
async def test_no_remote_token_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test Unable to obtain token for Envoy authentication from https://entrez.enphaseenergy.com/tokens"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # The login endpoint is already mocked with 200 by start_7_firmware_mock
    # Only override the tokens endpoint to fail
    mock_response(
        mock_aioresponse,
        "post",
        "https://entrez.enphaseenergy.com/tokens",
        reset=True,
        status=500,
        body="token",
    )

    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    with pytest.raises(EnvoyAuthenticationError):
        await envoy.authenticate("username", "password")

    assert isinstance(envoy.auth, EnvoyTokenAuth)
    with pytest.raises(EnvoyAuthenticationRequired):
        assert envoy.auth.token_type == "owner"


@pytest.mark.asyncio
async def test_enlighten_json_error_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test Unable to decode response from Enlighten"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # Override the login endpoint to return invalid JSON
    mock_response(
        mock_aioresponse,
        "post",
        "https://enlighten.enphaseenergy.com/login/login.json?",
        reset=True,
        status=200,
        body="nojson",
    )

    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    with pytest.raises(EnvoyAuthenticationError):
        await envoy.authenticate("username", "password")


@pytest.mark.asyncio
async def test_token_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test auth using token"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()

    token = jwt.encode(
        payload={"name": "envoy", "exp": 1707837780, "enphaseUser": "owner"},
        key="secret",
        algorithm="HS256",
    )

    await envoy.authenticate("username", "password", token)
    assert isinstance(envoy.auth, EnvoyTokenAuth)
    assert envoy.auth.expire_timestamp == 1707837780
    assert envoy.auth.token == token
    assert envoy.auth.token_type == "owner"

    # test cookies function now cookies are not on request
    assert envoy.auth.cookies == {}

    # execute refresh code cov
    await envoy.auth.refresh()

    # cov: test force no serial error
    # Your firmware requires token authentication,
    # but no envoy serial number was provided to obtain the token
    used_serial = envoy.auth.envoy_serial
    envoy.auth.envoy_serial = None
    with pytest.raises(EnvoyAuthenticationError):
        await envoy.auth.refresh()
    envoy.auth.envoy_serial = used_serial

    # cov: test force no cloud credentials error
    # Your firmware requires token authentication
    # but no cloud credentials were provided to obtain the token
    envoy.auth.cloud_password = None
    with pytest.raises(EnvoyAuthenticationError):
        await envoy.auth.refresh()


@pytest.mark.asyncio
async def test_remote_login_response_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test enlighten login response for is_consumer and manager_token"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # set log level to info 1 time for GET and 1 time for POST to improve COV
    with temporary_log_level("pyenphase", logging.INFO):
        envoy = Envoy("127.0.0.1", client=test_client_session)
        await envoy.setup()
        await envoy.authenticate("username", "password")

    assert isinstance(envoy.auth, EnvoyTokenAuth)
    assert envoy.auth.manager_token == "1234567890"
    assert envoy.auth.is_consumer

    # read unused auth from EnvoyTokenAuth to improve COV
    assert envoy.auth.auth is None


@pytest.mark.asyncio
async def test_close_connection_not_ok_middleware_non_200() -> None:
    """Test CloseConnectionNotOKMiddleware closes connection on non-200 status."""
    middleware = CloseConnectionNotOKMiddleware()

    # Test with 401 response - should close the connection
    mock_response_401 = MagicMock(spec=aiohttp.ClientResponse)
    mock_response_401.status = 401
    mock_response_401.close = MagicMock()

    mock_request = MagicMock(spec=aiohttp.ClientRequest)
    mock_handler = AsyncMock(return_value=mock_response_401)

    response = await middleware(mock_request, mock_handler)

    assert response == mock_response_401
    mock_handler.assert_called_once_with(mock_request)
    mock_response_401.close.assert_called_once()


@pytest.mark.asyncio
async def test_close_connection_not_ok_middleware_200() -> None:
    """Test CloseConnectionNotOKMiddleware doesn't close on 200 status."""
    middleware = CloseConnectionNotOKMiddleware()

    # Test with 200 response - should NOT close the connection
    mock_response_200 = MagicMock(spec=aiohttp.ClientResponse)
    mock_response_200.status = 200
    mock_response_200.close = MagicMock()

    mock_request = MagicMock(spec=aiohttp.ClientRequest)
    mock_handler = AsyncMock(return_value=mock_response_200)

    response = await middleware(mock_request, mock_handler)

    assert response == mock_response_200
    mock_handler.assert_called_once_with(mock_request)
    mock_response_200.close.assert_not_called()


@pytest.mark.asyncio
async def test_close_connection_not_ok_middleware_various_statuses() -> None:
    """Test CloseConnectionNotOKMiddleware with various HTTP status codes."""
    middleware = CloseConnectionNotOKMiddleware()

    # Test various status codes
    test_cases = [
        (200, False),  # OK - should not close
        (201, True),  # Created - should close
        (204, True),  # No Content - should close
        (401, True),  # Unauthorized - should close
        (403, True),  # Forbidden - should close
        (404, True),  # Not Found - should close
        (500, True),  # Internal Server Error - should close
    ]

    for status_code, should_close in test_cases:
        mock_response = MagicMock(spec=aiohttp.ClientResponse)
        mock_response.status = status_code
        mock_response.close = MagicMock()

        mock_request = MagicMock(spec=aiohttp.ClientRequest)
        mock_handler = AsyncMock(return_value=mock_response)

        response = await middleware(mock_request, mock_handler)

        assert response == mock_response
        mock_handler.assert_called_once_with(mock_request)

        if should_close:
            mock_response.close.assert_called_once()
        else:
            mock_response.close.assert_not_called()


@pytest.mark.asyncio
async def test_legacy_auth_middleware_chain() -> None:
    """Test that EnvoyLegacyAuth properly sets up the middleware chain."""
    legacy_auth = EnvoyLegacyAuth("127.0.0.1", "envoy", "password")

    # Test that middlewares property returns the correct chain
    middlewares = legacy_auth.middlewares
    assert middlewares is not None
    assert len(middlewares) == 2
    assert isinstance(middlewares[0], CloseConnectionNotOKMiddleware)
    assert isinstance(middlewares[1], aiohttp.DigestAuthMiddleware)


@pytest.mark.asyncio
async def test_legacy_auth_middleware_chain_no_auth() -> None:
    """Test that EnvoyLegacyAuth returns None for middleware when no credentials."""
    # Test with missing username
    legacy_auth = EnvoyLegacyAuth("127.0.0.1", "", "password")
    assert legacy_auth.middlewares is None

    # Test with missing password
    legacy_auth = EnvoyLegacyAuth("127.0.0.1", "envoy", "")
    assert legacy_auth.middlewares is None

    # Test with both missing
    legacy_auth = EnvoyLegacyAuth("127.0.0.1", "", "")
    assert legacy_auth.middlewares is None
