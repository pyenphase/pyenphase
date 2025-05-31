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
    """
    Tests that the Envoy correctly handles missing serial number information in the device info XML.

    Verifies that the firmware and part number are set, while the serial number is None when the serial number tag is absent from the response.
    """
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
    """
    Verifies that the Envoy correctly handles missing part number information in the device info XML.

    This test mocks the `/info` endpoint to return XML without a part number, then asserts that the firmware and serial number are set while the part number is `None`.
    """
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
    """
    Tests that the Envoy instance handles missing firmware version in device info XML.

    Verifies that when the firmware version is absent from the response, the `firmware`
    property is empty or falsey, while `serial_number` and `part_number` are correctly set.
    """
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
    """
    Tests Envoy firmware parsing when the device XML segment is missing.

    Verifies that when the `<device>` segment is absent from the `/info` XML response, the Envoy instance sets `firmware` to a falsey value and both `serial_number` and `part_number` to `None`.
    """
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
    """
    Verifies that EnvoyFirmwareCheckError is raised when the /info endpoint returns a non-200 HTTP status.
    """
    info = "<?xml version='1.0' encoding='UTF-8'?><envoy_info></envoy_info>"
    mock_aioresponse.get("https://127.0.0.1/info", status=500, body=info)
    envoy = Envoy("127.0.0.1", client=test_client_session)
    with pytest.raises(EnvoyFirmwareCheckError):
        await envoy.setup()


@pytest.mark.asyncio
async def test_firmware_metered_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Verifies that the Envoy correctly identifies a metered device when the XML info includes <imeter>true>.
    """
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
    """
    Verifies that the Envoy device is correctly identified as not metered when the XML info contains `<imeter>false</imeter>`.
    """
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
    """
    Verifies that the Envoy correctly sets `is_metered` to False when the `<imeter>` tag is missing from the device info XML.
    """
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
