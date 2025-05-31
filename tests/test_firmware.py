"""Test firmware functions."""

import logging

import aiohttp
import pytest
from aioresponses import aioresponses

from pyenphase import Envoy
from pyenphase.exceptions import EnvoyFirmwareCheckError

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
