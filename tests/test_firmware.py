"""Test firmware functions."""

import logging

import pytest
import respx
from httpx import Response

from pyenphase import Envoy
from pyenphase.exceptions import EnvoyFirmwareCheckError

from .common import prep_envoy, start_7_firmware_mock

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
@respx.mock
async def test_firmware_with_7_6_175_standard():
    """Test firmware is processed ok."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    start_7_firmware_mock()
    prep_envoy(version)
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
    respx.get("/info").mock(return_value=Response(200, text=info))

    envoy = Envoy("127.0.0.1")
    await envoy.setup()

    assert envoy.firmware == "7.8.901"
    assert envoy.serial_number == "123456789012"
    assert envoy.part_number == "800-12345-r99"


@pytest.mark.asyncio
@respx.mock
async def test_firmware_no_sn_with_7_6_175_standard():
    """Test missing serial number in info"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    start_7_firmware_mock()
    prep_envoy(version)
    info = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<envoy_info>"
        "  <device>"
        "    <pn>800-12345-r99</pn>"
        "    <software>D7.8.901</software>"
        "  </device>"
        "</envoy_info>"
    )
    respx.get("/info").mock(return_value=Response(200, text=info))

    envoy = Envoy("127.0.0.1")
    await envoy.setup()

    assert envoy.firmware == "7.8.901"
    assert envoy.serial_number is None
    assert envoy.part_number == "800-12345-r99"


@pytest.mark.asyncio
@respx.mock
async def test_firmware_no_pn_with_7_6_175_standard():
    """Test missing pb in info"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    start_7_firmware_mock()
    prep_envoy(version)
    info = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<envoy_info>"
        "  <device>"
        "    <sn>123456789012</sn>"
        "    <software>D7.8.901</software>"
        "  </device>"
        "</envoy_info>"
    )
    respx.get("/info").mock(return_value=Response(200, text=info))

    envoy = Envoy("127.0.0.1")
    await envoy.setup()

    assert envoy.firmware == "7.8.901"
    assert envoy.serial_number == "123456789012"
    assert envoy.part_number is None


@pytest.mark.asyncio
@respx.mock
async def test_firmware_no_fw_with_7_6_175_standard():
    """Test missing fw in info"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    start_7_firmware_mock()
    prep_envoy(version)
    info = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<envoy_info>"
        "  <device>"
        "    <sn>123456789012</sn>"
        "    <pn>800-12345-r99</pn>"
        "  </device>"
        "</envoy_info>"
    )
    respx.get("/info").mock(return_value=Response(200, text=info))

    envoy = Envoy("127.0.0.1")
    await envoy.setup()

    assert not envoy.firmware
    assert envoy.serial_number == "123456789012"
    assert envoy.part_number == "800-12345-r99"


@pytest.mark.asyncio
@respx.mock
async def test_firmware_no_device_with_7_6_175_standard():
    """Test missing device xml segment in info"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    start_7_firmware_mock()
    prep_envoy(version)
    info = "<?xml version='1.0' encoding='UTF-8'?><envoy_info></envoy_info>"
    respx.get("/info").mock(return_value=Response(200, text=info))

    envoy = Envoy("127.0.0.1")
    await envoy.setup()

    assert not envoy.firmware
    assert envoy.serial_number is None
    assert envoy.part_number is None


@pytest.mark.asyncio
@respx.mock
async def test_firmware_no_200__with_7_6_175_standard():
    """Test other status as 200 returned"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    start_7_firmware_mock()
    prep_envoy(version)
    info = "<?xml version='1.0' encoding='UTF-8'?><envoy_info></envoy_info>"
    respx.get("/info").mock(return_value=Response(500, text=info))

    envoy = Envoy("127.0.0.1")
    with pytest.raises(EnvoyFirmwareCheckError):
        await envoy.setup()
