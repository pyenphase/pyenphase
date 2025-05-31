"""Test auth functions."""

import json
import logging
from os import listdir
from os.path import isfile, join
from unittest.mock import patch

import aiohttp
import jwt
import pytest
from aioresponses import aioresponses

from pyenphase import Envoy, EnvoyTokenAuth
from pyenphase.auth import EnvoyLegacyAuth
from pyenphase.const import URL_AUTH_CHECK_JWT
from pyenphase.exceptions import EnvoyAuthenticationError, EnvoyAuthenticationRequired

from .common import (
    get_mock_envoy,
    load_fixture,
    load_json_fixture,
    mock_response,
    prep_envoy,
    start_7_firmware_mock,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_wrong_auth_order_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Verifies that calling update before authentication on firmware 7.6.175_standard raises EnvoyAuthenticationRequired, and that update succeeds after proper authentication.
    """
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
    """
    Tests that attempting to authenticate with incorrect credentials on Envoy firmware version 3.9.36 results in an EnvoyAuthenticationRequired exception.
    
    This test mocks various HTTP endpoints to simulate failed authentication and verifies that creating a mock Envoy instance raises the expected authentication exception.
    """
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
    """
    Tests that authentication fails with a 401 Unauthorized error on the /api/v1/production endpoint for Envoy firmware version 3.9.36 with bad credentials.
    
    Mocks relevant HTTP endpoints to simulate failed authentication and verifies that attempting to create a mock Envoy instance raises EnvoyAuthenticationRequired.
    """
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
    """
    Tests successful authentication with known usernames on Envoy firmware version 3.9.36.
    
    Verifies that authentication succeeds with provided credentials, no cookies are used,
    the returned authentication object is an instance of EnvoyLegacyAuth, and that forced
    failure of Digest authentication results in the expected state.
    """
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
    """
    Tests that authentication with an unknown username on Envoy firmware version 3.9.36 raises EnvoyAuthenticationRequired.
    """
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
    """
    Tests that authentication with blank passwords fails on Envoy firmware version 7.6.175_standard.
    
    Verifies that attempting to authenticate with a blank password for any username raises EnvoyAuthenticationRequired.
    """
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
    """
    Tests that authentication fails with Envoy firmware 7.6.175_standard when no token can be obtained.
    
    Simulates a failure in the token retrieval process and asserts that attempting to authenticate raises an EnvoyAuthenticationError.
    """
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
    """
    Tests that authentication fails with Envoy firmware 7.6.175_standard when the JWT verification endpoint returns a 404 error, resulting in an EnvoyAuthenticationError.
    """
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
    """
    Tests that authentication fails with Envoy firmware 7.6.175_standard when remote Enlighten login and token endpoints return server errors.
    
    Asserts that attempting to authenticate raises EnvoyAuthenticationError when both the Enlighten login and token endpoints respond with HTTP 500 errors.
    """
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
    """
    Tests that authentication fails with Envoy firmware 7.6.175_standard when the remote token endpoint returns an error.
    
    Simulates a scenario where the Enlighten login endpoint succeeds but the token endpoint returns an HTTP 500 error, causing authentication to raise `EnvoyAuthenticationError`. Also verifies that the resulting auth object is `EnvoyTokenAuth` and that accessing its `token_type` property raises `EnvoyAuthenticationRequired`.
    """
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
    """
    Tests that authentication fails with Envoy firmware 7.6.175_standard when the Enlighten login endpoint returns invalid JSON, raising EnvoyAuthenticationError.
    """
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
    """
    Tests token-based authentication on Envoy firmware version 7.6.175_standard.
    
    Verifies that authentication with a manually created JWT token results in an `EnvoyTokenAuth` object with correct attributes, and that token refresh handles missing serial number or cloud credentials by raising `EnvoyAuthenticationError`.
    """
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
    """
    Tests that authentication on firmware version 7.6.175_standard correctly processes the Enlighten login response, verifying that the resulting EnvoyTokenAuth object contains the expected manager_token and is_consumer attributes.
    """
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()

    await envoy.authenticate("username", "password")
    assert isinstance(envoy.auth, EnvoyTokenAuth)
    assert envoy.auth.manager_token == "1234567890"
    assert envoy.auth.is_consumer
