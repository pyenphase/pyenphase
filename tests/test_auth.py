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
from pyenphase.const import (
    URL_AUTH_CHECK_JWT,
    URL_DEVICE_DATA,
    URL_PRODUCTION_INVERTERS,
    SupportedFeatures,
)
from pyenphase.exceptions import EnvoyAuthenticationError, EnvoyAuthenticationRequired

from .common import (
    get_mock_envoy,
    load_fixture,
    load_json_fixture,
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
    mock_aioresponse.get(
        "https://127.0.0.1/info", status=200, body=await load_fixture(version, "info")
    )
    mock_aioresponse.get("https://127.0.0.1/info.xml", status=200, body="")
    mock_aioresponse.get("https://127.0.0.1/production", status=404)
    mock_aioresponse.get("https://127.0.0.1/production.json", status=404)
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production",
        status=401,
        payload=await load_json_fixture(version, "api_v1_production"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production/inverters",
        status=200,
        payload=await load_json_fixture(version, "api_v1_production_inverters"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/ivp/ensemble/inventory", status=200, payload=[]
    )

    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if "admin_lib_tariff" in files:
        try:
            json_data = await load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        mock_aioresponse.get(
            "https://127.0.0.1/admin/lib/tariff", status=200, payload=json_data
        )
    else:
        mock_aioresponse.get("https://127.0.0.1/admin/lib/tariff", status=401)

    mock_aioresponse.get("https://127.0.0.1/ivp/meters", status=200, payload=[])

    # Add the HTTP version of api/v1/production with 401 as well
    mock_aioresponse.get(
        "http://127.0.0.1/api/v1/production",
        status=401,
        payload=await load_json_fixture(version, "api_v1_production"),
    )

    # Add other required endpoints for the probe
    mock_aioresponse.get("https://127.0.0.1/production.json?details=1", status=404)
    mock_aioresponse.get("http://127.0.0.1/production.json?details=1", status=404)
    mock_aioresponse.get(
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
    mock_aioresponse.get(
        "https://127.0.0.1/info", status=200, body=await load_fixture(version, "info")
    )
    mock_aioresponse.get("https://127.0.0.1/info.xml", status=200, body="")
    mock_aioresponse.get("https://127.0.0.1/production", status=404)
    mock_aioresponse.get("https://127.0.0.1/production.json", status=404)
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production",
        status=401,
        payload=await load_json_fixture(version, "api_v1_production"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production/inverters",
        status=200,
        payload=await load_json_fixture(version, "api_v1_production_inverters"),
    )
    mock_aioresponse.get(
        "https://127.0.0.1/ivp/ensemble/inventory", status=200, payload=[]
    )

    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if "admin_lib_tariff" in files:
        try:
            json_data = await load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        mock_aioresponse.get(
            "https://127.0.0.1/admin/lib/tariff", status=200, payload=json_data
        )
    else:
        mock_aioresponse.get("https://127.0.0.1/admin/lib/tariff", status=401)

    mock_aioresponse.get("https://127.0.0.1/ivp/meters", status=200, payload=[])

    # Add the HTTP version of api/v1/production with 401 as well
    mock_aioresponse.get(
        "http://127.0.0.1/api/v1/production",
        status=401,
        payload=await load_json_fixture(version, "api_v1_production"),
    )

    # Add other required endpoints for the probe
    mock_aioresponse.get("https://127.0.0.1/production.json?details=1", status=404)
    mock_aioresponse.get("http://127.0.0.1/production.json?details=1", status=404)
    mock_aioresponse.get(
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

    from .common import override_mock

    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1" + URL_AUTH_CHECK_JWT,
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

    from .common import override_mock

    override_mock(
        mock_aioresponse,
        "post",
        "https://enlighten.enphaseenergy.com/login/login.json?",
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
    override_mock(
        mock_aioresponse,
        "post",
        "https://entrez.enphaseenergy.com/tokens",
        status=500,
        body="token",
    )
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/auth/check_jwt",
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

    from .common import override_mock

    # The login endpoint is already mocked with 200 by start_7_firmware_mock
    # Only override the tokens endpoint to fail
    override_mock(
        mock_aioresponse,
        "post",
        "https://entrez.enphaseenergy.com/tokens",
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

    from .common import override_mock

    # Override the login endpoint to return invalid JSON
    override_mock(
        mock_aioresponse,
        "post",
        "https://enlighten.enphaseenergy.com/login/login.json?",
        status=200,
        body="nojson",
    )

    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    with pytest.raises(EnvoyAuthenticationError):
        await envoy.authenticate("username", "password")


@pytest.mark.asyncio
async def test_enlighten_json_missing_is_consumer_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test response from Enlighten is missing is_consumer and manager keys"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    from .common import override_mock

    # Override the login endpoint to return missing is_consumer and manager keys in JSON
    override_mock(
        mock_aioresponse,
        "post",
        "https://enlighten.enphaseenergy.com/login/login.json?",
        status=200,
        payload={
            "session_id": "1234567890",
            "user_id": "1234567890",
            "user_name": "test",
            "first_name": "Test",
        },
    )

    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    await envoy.authenticate("username", "password")
    assert isinstance(envoy.auth, EnvoyTokenAuth)
    assert not envoy.auth.is_consumer
    assert envoy.auth.manager_token == ""


@pytest.mark.asyncio
async def test_enlighten_json_missing_session_id_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test response from Enlighten is missing session_id"""
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    from .common import override_mock

    # Override the login endpoint to return missing session_id keys in JSON
    override_mock(
        mock_aioresponse,
        "post",
        "https://enlighten.enphaseenergy.com/login/login.json?",
        status=200,
        payload={
            "nosession_id": "1234567890",
            "user_id": "1234567890",
            "user_name": "test",
            "first_name": "Test",
        },
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
async def test_device_data_with_8_2_4345_with_device_data(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test device data fails with no auth"""
    version = "8.2.4345_with_device_data"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    from .common import override_mock, updater_features

    # 401 on device data endpoint and inverters production endpoint
    # This simulates the case where the user does not have access to any inverter data
    for url in [
        "https://127.0.0.1" + URL_DEVICE_DATA,
        "http://127.0.0.1" + URL_DEVICE_DATA,
        "https://127.0.0.1" + URL_PRODUCTION_INVERTERS,
        "http://127.0.0.1" + URL_PRODUCTION_INVERTERS,
    ]:
        override_mock(
            mock_aioresponse,
            "get",
            url,
            status=401,
            body="no device data",
        )

    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    await envoy.authenticate("username", "password")

    await envoy.probe()
    assert SupportedFeatures.INVERTERS not in envoy.supported_features

    # 200 on device data endpoint only
    # This simulates the case where the user has access to device data but not to inverter production data
    for url in [
        "https://127.0.0.1" + URL_DEVICE_DATA,
        "http://127.0.0.1" + URL_DEVICE_DATA,
    ]:
        override_mock(
            mock_aioresponse,
            "get",
            url,
            status=200,
            payload=await load_json_fixture(version, "ivp_pdm_device_data"),
        )

    await envoy.probe()
    assert updater_features(envoy._updaters) == {
        "EnvoyDeviceDataInvertersUpdater": SupportedFeatures.INVERTERS
        | SupportedFeatures.DETAILED_INVERTERS,
        "EnvoyEnembleUpdater": SupportedFeatures.ENCHARGE | SupportedFeatures.ENPOWER,
        "EnvoyMetersUpdater": SupportedFeatures.CTMETERS,
        "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
        | SupportedFeatures.TOTAL_CONSUMPTION
        | SupportedFeatures.NET_CONSUMPTION
        | SupportedFeatures.PRODUCTION,
        "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
    }


# S
