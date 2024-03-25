"""Test tenacety retry functioning."""

import logging
from pathlib import Path
from typing import Any

import httpx
import orjson
import pytest
import respx
from httpx import Response
from tenacity import stop_after_attempt, stop_after_delay, wait_none

from pyenphase import Envoy
from pyenphase.exceptions import (
    EnvoyAuthenticationRequired,
    EnvoyFirmwareCheckError,
    EnvoyFirmwareFatalCheckError,
)

LOGGER = logging.getLogger(__name__)


def _fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


def _load_fixture(version: str, name: str) -> str:
    with open(_fixtures_dir() / version / name) as read_in:
        return read_in.read()


def _load_json_fixture(version: str, name: str) -> dict[str, Any]:
    return orjson.loads(_load_fixture(version, name))


def _start_7_firmware_mock():
    respx.post("https://enlighten.enphaseenergy.com/login/login.json?").mock(
        return_value=Response(
            200,
            json={
                "session_id": "1234567890",
                "user_id": "1234567890",
                "user_name": "test",
                "first_name": "Test",
                "is_consumer": True,
                "manager_token": "1234567890",
            },
        )
    )
    respx.post("https://entrez.enphaseenergy.com/tokens").mock(
        return_value=Response(200, text="token")
    )
    respx.get("/auth/check_jwt").mock(return_value=Response(200, json={}))


def prep_envoy(version: str, info: bool = False, meters: bool = True) -> None:
    """Mock envoy replies in correct order"""
    if info:
        respx.get("/info").mock(
            return_value=Response(200, text=_load_fixture(version, "info"))
        )

    if meters:
        respx.get("/ivp/meters").mock(return_value=Response(200, text="[]"))

    respx.get("/production").mock(
        return_value=Response(200, text=_load_fixture(version, "production"))
    )
    respx.get("/production.json").mock(
        return_value=Response(200, text=_load_fixture(version, "production.json"))
    )
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production")
        )
    )
    respx.get("/api/v1/production/inverters").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production_inverters")
        )
    )
    respx.get("/ivp/ensemble/inventory").mock(return_value=Response(200, json=[]))
    respx.get("/admin/lib/tariff").mock(return_value=Response(404))


@pytest.mark.asyncio
@respx.mock
async def test_full_connected_from_start_with_7_6_175_standard():
    """Test envoy connected and replying from start"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    _start_7_firmware_mock()
    prep_envoy(version=version, info=True)

    envoy = Envoy("127.0.0.1")
    # remove the waits between retries for this test and set known retries
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Ensure that there was 1 attempt only.
    stats: dict[str, Any] = envoy._firmware._get_info.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1

    assert envoy.firmware == "7.6.175"
    assert envoy.part_number == "800-00656-r06"

    data = await envoy.update()
    assert data


@pytest.mark.asyncio
@respx.mock
async def test_full_disconnected_from_start_with_7_6_175_standard():
    """Test envoy disconnect at start, should return EnvoyFirmwareFatalCheckError."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    _start_7_firmware_mock()
    envoy = Envoy("127.0.0.1")
    # remove the waits between retries for this test and set known retries
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    respx.get("/info").mock(
        return_value=Response(200, text="")
    ).side_effect = httpx.ConnectError("Test timeoutexception")

    with pytest.raises(EnvoyFirmwareFatalCheckError):
        await envoy.setup()

    # Ensure that there were 3 attempts.
    stats: dict[str, Any] = envoy._firmware._get_info.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 3


@pytest.mark.asyncio
@respx.mock
async def test_2_timeout_from_start_with_7_6_175_standard():
    """Test envoy timeout at start, timeout is not in retry loop."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    _start_7_firmware_mock()
    envoy = Envoy("127.0.0.1")
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    # test if 2 timeouts return failed
    respx.get("/info").mock(return_value=Response(200, text="")).side_effect = [
        httpx.TimeoutException("Test timeoutexception"),
        httpx.TimeoutException("Test timeoutexception"),
    ]

    with pytest.raises(EnvoyFirmwareFatalCheckError):
        await envoy.setup()

    # Ensure that there were no retries.
    stats: dict[str, Any] = envoy._firmware._get_info.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1


@pytest.mark.asyncio
@respx.mock
async def test_httperror_from_start_with_7_6_175_standard():
    """Test envoy httperror at start, is not in retry loop."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    _start_7_firmware_mock()
    prep_envoy(version=version)

    envoy = Envoy("127.0.0.1")
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    # test if 2 timeouts return failed
    respx.get("/info").mock().side_effect = [
        httpx.HTTPError("Test timeoutexception"),
        Response(200, text=_load_fixture(version, "info")),
    ]

    with pytest.raises(EnvoyFirmwareCheckError):
        await envoy.setup()

    # Ensure that there were no retries.
    stats: dict[str, Any] = envoy._firmware._get_info.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1


@pytest.mark.asyncio
@respx.mock
async def test_1_timeout_from_start_with_7_6_175_standard():
    """Test envoy timeout at start, timeout is not in retry loop but tries http after https."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    _start_7_firmware_mock()
    prep_envoy(version=version)

    envoy = Envoy("127.0.0.1")
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    # test if 2 timeouts return failed
    respx.get("/info").mock().side_effect = [
        httpx.TimeoutException("Test timeoutexception"),
        Response(200, text=_load_fixture(version, "info")),
    ]

    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Ensure that there were no retries.
    stats: dict[str, Any] = envoy._firmware._get_info.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1

    assert envoy.firmware == "7.6.175"
    assert envoy.part_number == "800-00656-r06"

    data = await envoy.update()
    assert data


@pytest.mark.asyncio
@respx.mock
async def test_5_not_connected_at_start_with_7_6_175_standard():
    """Test 5 connection failures at start and last one works"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    _start_7_firmware_mock()
    prep_envoy(version)

    envoy = Envoy("127.0.0.1")
    # remove the waits between retries for this test and set known retries
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    # we need 2 side effects for each try as https and then http is attempted
    respx.get("/info").mock().side_effect = [
        httpx.ConnectError("Test timeoutexception"),
        httpx.ConnectError("Test timeoutexception"),
        httpx.ConnectError("Test timeoutexception"),
        httpx.ConnectError("Test timeoutexception"),
        httpx.ConnectError("Test timeoutexception"),
        Response(200, text=_load_fixture(version, "info")),
    ]
    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Ensure that there were no retries.
    stats: dict[str, Any] = envoy._firmware._get_info.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 3

    assert envoy.firmware == "7.6.175"
    assert envoy.part_number == "800-00656-r06"

    data = await envoy.update()
    assert data


@pytest.mark.asyncio
@respx.mock
async def test_2_network_errors_at_start_with_7_6_175_standard():
    """Test 2 network error failures at start and 3th works"""
    logging.getLogger("pyenphase").setLevel(logging.WARN)
    version = "7.6.175_standard"
    _start_7_firmware_mock()
    prep_envoy(version)

    envoy = Envoy("127.0.0.1")
    # remove the waits between retries for this test and set known retries
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    # we need 2 side effects for each try as https and then http is attempted
    respx.get("/info").mock().side_effect = [
        httpx.NetworkError("Test timeoutexception"),
        httpx.RemoteProtocolError("Test timeoutexception"),
        Response(200, text=_load_fixture(version, "info")),
    ]

    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Ensure that there were no retries.
    stats: dict[str, Any] = envoy._firmware._get_info.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 3

    assert envoy.firmware == "7.6.175"
    assert envoy.part_number == "800-00656-r06"

    data = await envoy.update()
    assert data


@pytest.mark.asyncio
@respx.mock
async def test_3_network_errors_at_start_with_7_6_175_standard():
    """Test 3 network error failures at start"""
    logging.getLogger("pyenphase").setLevel(logging.WARN)
    version = "7.6.175_standard"
    _start_7_firmware_mock()
    prep_envoy(version)

    envoy = Envoy("127.0.0.1")
    # remove the waits between retries for this test and set known retries
    envoy._firmware._get_info.retry.wait = wait_none()
    envoy._firmware._get_info.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    # we need 2 side effects for each try as https and then http is attempted
    respx.get("/info").mock().side_effect = [
        httpx.NetworkError("Test timeoutexception"),
        httpx.RemoteProtocolError("Test timeoutexception"),
        httpx.NetworkError("Test timeoutexception"),
    ]

    with pytest.raises(EnvoyFirmwareCheckError):
        await envoy.setup()

    # Ensure that there were no retries.
    stats: dict[str, Any] = envoy._firmware._get_info.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 3


@pytest.mark.asyncio
@respx.mock
async def test_noconnection_at_probe_with_7_6_175_standard():
    """Test 3 network error failures at start"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    _start_7_firmware_mock()
    prep_envoy(version, info=True)

    envoy = Envoy("127.0.0.1")
    # remove the waits between retries for this test and set known retries
    envoy.probe_request.retry.wait = wait_none()
    envoy.probe_request.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Ensure that there were no retries.
    stats: dict[str, Any] = envoy._firmware._get_info.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1

    # Probe is re-calling retried probe_request before returning
    # we can only see stats for the last request done.
    # force 3 retries for last one
    respx.get("/admin/lib/tariff").mock().side_effect = [
        httpx.NetworkError("Test timeoutexception"),
        httpx.RemoteProtocolError("Test timeoutexception"),
        httpx.TimeoutException("Test timeoutexception"),
    ]

    await envoy.setup()
    await envoy.authenticate("username", "password")
    await envoy.probe()
    # assert data

    stats = envoy.probe_request.retry.statistics
    assert "attempt_number" in stats
    print(f"--stats--{stats}")
    assert stats["attempt_number"] == 3

    data = await envoy.update()
    assert data


@pytest.mark.asyncio
@respx.mock
async def test_noconnection_at_update_with_7_6_175_standard():
    """Test 3 network error failures at start"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    _start_7_firmware_mock()
    prep_envoy(version, info=True)

    envoy = Envoy("127.0.0.1")
    # remove the waits between retries for this test and set known retries
    envoy.request.retry.wait = wait_none()
    envoy.request.retry.stop = stop_after_attempt(3) | stop_after_delay(50)

    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Ensure that there were no retries.
    stats: dict[str, Any] = envoy._firmware._get_info.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1

    await envoy.probe()

    stats = envoy.probe_request.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 1

    respx.get("/api/v1/production").mock().side_effect = [
        httpx.TimeoutException("Test timeoutexception"),
        httpx.TimeoutException("Test timeoutexception"),
        httpx.TimeoutException("Test timeoutexception"),
    ]

    with pytest.raises(httpx.TimeoutException):
        await envoy.update()

    stats = envoy.request.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 3

    respx.get("/api/v1/production").mock().side_effect = [
        httpx.RemoteProtocolError("Test timeoutexception"),
        httpx.RemoteProtocolError("Test timeoutexception"),
        httpx.RemoteProtocolError("Test timeoutexception"),
    ]

    with pytest.raises(httpx.RemoteProtocolError):
        await envoy.update()

    stats = envoy.request.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 3

    respx.get("/api/v1/production").mock().side_effect = [
        httpx.NetworkError("Test timeoutexception"),
        httpx.NetworkError("Test timeoutexception"),
        httpx.NetworkError("Test timeoutexception"),
    ]

    with pytest.raises(httpx.NetworkError):
        await envoy.update()

    stats = envoy.request.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 3

    respx.get("/api/v1/production").mock().side_effect = [
        orjson.JSONDecodeError("Test timeoutexception", "that.file", 22),
        orjson.JSONDecodeError("Test timeoutexception", "that.file", 22),
        orjson.JSONDecodeError("Test timeoutexception", "that.file", 22),
    ]

    with pytest.raises(orjson.JSONDecodeError):
        await envoy.update()

    stats = envoy.request.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 3

    # other error EnvoyAuthenticationRequired should end cycle
    respx.get("/api/v1/production").mock().side_effect = [
        httpx.NetworkError("Test timeoutexception"),
        EnvoyAuthenticationRequired("Test timeoutexception"),
        httpx.NetworkError,
    ]

    with pytest.raises(EnvoyAuthenticationRequired):
        await envoy.update()

    stats = envoy.request.retry.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == 2
