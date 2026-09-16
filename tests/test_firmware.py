"""Test firmware functions."""

import logging

import aiohttp
import pytest
from aioresponses import CallbackResult, aioresponses

from pyenphase import Envoy
from pyenphase.exceptions import EnvoyClientClosedError, EnvoyFirmwareCheckError

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_firmware_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test firmware is processed ok."""
    info = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<envoy_info>"
        "  <device>"
        "    <sn>123456789012</sn>"
        "    <pn>800-12345-r99</pn>"
        "    <software>D7.8.901</software>"
        "  </device>"
        "</envoy_info>"
    )
    mock_aioresponse.get("https://127.0.0.1/info", status=200, body=info)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    assert envoy.firmware == "7.8.901"
    assert envoy.serial_number == "123456789012"
    assert envoy.part_number == "800-12345-r99"


@pytest.mark.asyncio
async def test_firmware_no_sn_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test missing serial number in info"""
    info = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<envoy_info>"
        "  <device>"
        "    <pn>800-12345-r99</pn>"
        "    <software>D7.8.901</software>"
        "  </device>"
        "</envoy_info>"
    )
    mock_aioresponse.get("https://127.0.0.1/info", status=200, body=info)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    assert envoy.firmware == "7.8.901"
    assert envoy.serial_number is None
    assert envoy.part_number == "800-12345-r99"


@pytest.mark.asyncio
async def test_firmware_no_pn_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test missing pb in info"""
    info = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<envoy_info>"
        "  <device>"
        "    <sn>123456789012</sn>"
        "    <software>D7.8.901</software>"
        "  </device>"
        "</envoy_info>"
    )
    mock_aioresponse.get("https://127.0.0.1/info", status=200, body=info)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    assert envoy.firmware == "7.8.901"
    assert envoy.serial_number == "123456789012"
    assert envoy.part_number is None


@pytest.mark.asyncio
async def test_firmware_no_fw_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test missing fw in info"""
    info = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<envoy_info>"
        "  <device>"
        "    <sn>123456789012</sn>"
        "    <pn>800-12345-r99</pn>"
        "  </device>"
        "</envoy_info>"
    )
    mock_aioresponse.get("https://127.0.0.1/info", status=200, body=info)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    assert not envoy.firmware
    assert envoy.serial_number == "123456789012"
    assert envoy.part_number == "800-12345-r99"


@pytest.mark.asyncio
async def test_firmware_no_device_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test missing device xml segment in info"""
    info = "<?xml version='1.0' encoding='UTF-8'?><envoy_info></envoy_info>"
    mock_aioresponse.get("https://127.0.0.1/info", status=200, body=info)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    assert not envoy.firmware
    assert envoy.serial_number is None
    assert envoy.part_number is None


@pytest.mark.asyncio
async def test_firmware_no_200__with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test other status as 200 returned"""
    info = "<?xml version='1.0' encoding='UTF-8'?><envoy_info></envoy_info>"
    mock_aioresponse.get("https://127.0.0.1/info", status=500, body=info)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    with pytest.raises(EnvoyFirmwareCheckError):
        await envoy.setup()


@pytest.mark.asyncio
async def test_firmware_metered_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test firmware is processed ok."""
    info = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<envoy_info>"
        "  <device>"
        "    <sn>123456789012</sn>"
        "    <pn>800-12345-r99</pn>"
        "    <software>D7.8.901</software>"
        "    <imeter>true</imeter>"
        "  </device>"
        "</envoy_info>"
    )
    mock_aioresponse.get("https://127.0.0.1/info", status=200, body=info)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    assert envoy.is_metered


@pytest.mark.asyncio
async def test_firmware_not_metered_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test firmware is processed ok."""
    info = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<envoy_info>"
        "  <device>"
        "    <sn>123456789012</sn>"
        "    <pn>800-12345-r99</pn>"
        "    <software>D7.8.901</software>"
        "    <imeter>false</imeter>"
        "  </device>"
        "</envoy_info>"
    )
    mock_aioresponse.get("https://127.0.0.1/info", status=200, body=info)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    assert not envoy.is_metered


@pytest.mark.asyncio
async def test_firmware_missing_metered_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test firmware is processed ok."""
    info = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<envoy_info>"
        "  <device>"
        "    <sn>123456789012</sn>"
        "    <pn>800-12345-r99</pn>"
        "    <software>D7.8.901</software>"
        "  </device>"
        "</envoy_info>"
    )
    mock_aioresponse.get("https://127.0.0.1/info", status=200, body=info)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    assert not envoy.is_metered


@pytest.mark.asyncio
async def test_firmware_https_client_closed(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test firmware signals client closed."""
    info = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<envoy_info>"
        "  <device>"
        "    <sn>123456789012</sn>"
        "    <pn>800-12345-r99</pn>"
        "    <software>D7.8.901</software>"
        "  </device>"
        "</envoy_info>"
    )
    mock_aioresponse.get("https://127.0.0.1/info", status=200, body=info)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    # close client to force client closed
    await envoy._client.close()
    with pytest.raises(
        EnvoyClientClosedError, match="Client closed before request is issued"
    ):
        await envoy.setup()


async def fail_request_and_close_session(
    url: str,
    client: aiohttp.ClientSession,
    body: str = "",
) -> CallbackResult:
    """Close session and return result"""
    await client.close()
    return CallbackResult(status=200, body=body)


@pytest.mark.asyncio
async def test_firmware_http_client_closed(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test firmware signals client closed."""
    caplog.set_level(logging.DEBUG)
    info = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<envoy_info>"
        "  <device>"
        "    <sn>123456789012</sn>"
        "    <pn>800-12345-r99</pn>"
        "    <software>D7.8.901</software>"
        "  </device>"
        "</envoy_info>"
    )
    envoy = Envoy("127.0.0.1", client=test_client_session)

    # to test client closed during the failed https request we
    # need soething that will not close it before the https request
    # but right after it, so the closed test in the http fallback
    # catches it. Using callback fails, it closes but the https closed
    # checks picks it up already.
    # DEBUG    pyenphase.firmware:firmware.py:87 Requesting https://127.0.0.1/info with timeout ...
    # ERROR    pyenphase.utilities:utilities.py:15 Request to https://127.0.0.1/info aborted because client is closed.
    # for now leave as is till a way to do this is clear
    mock_aioresponse.get(
        "https://127.0.0.1/info",
        status=200,
        exception=aiohttp.ClientConnectionError("Test https to http"),
        callback=await fail_request_and_close_session(
            url="/info",
            client=envoy._client,
            body=info,
        ),
    )

    mock_aioresponse.get(
        "http://127.0.0.1/info",
        status=200,
        body=info,
    )

    with (
        pytest.raises(
            EnvoyClientClosedError,
            match="Client closed before request is issued",
        ),
    ):
        await envoy.setup()
    assert "Requesting https://127.0.0.1/info" in caplog.text
    assert (
        "Request to https://127.0.0.1/info aborted because client is closed."
        in caplog.text
    )
    # if we could test http fallback with closed then we need to test for this
    # assert "Requesting https://127.0.0.1/info" in caplog.text
    # assert "Request to http://127.0.0.1/info aborted because client is closed." in caplog.text
