"""Test envoy home endpoint"""

import asyncio
import logging

import aiohttp
import pytest
from aioresponses import aioresponses

from pyenphase import Envoy
from pyenphase.models.home import EnvoyInterfaceInformation

from .common import (
    get_mock_envoy,
    load_fixture,
    load_json_fixture,
    override_mock,
    prep_envoy,
    start_7_firmware_mock,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_home_from_api_with_7_6_175(mock_aioresponse: aioresponses) -> None:
    """Test home data from api"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    # start with regular data first
    version = "7.6.175"

    # load mock data for home endpoint
    home_json = await load_json_fixture(version, "home")

    # test from_api method with eth0 interface
    home_data: EnvoyInterfaceInformation | None = EnvoyInterfaceInformation.from_api(
        home_json
    )

    # verify common data
    assert home_data
    assert home_data.software_build_epoch == 1719503966
    assert home_data.dhcp
    assert home_data.timezone == "Europe/Amsterdam"

    # verify interface data
    assert home_data.mac == "00:1D:C0:7F:B6:3B"
    assert home_data.primary_interface == "eth0"
    assert home_data.interface_type == "ethernet"

    # force wifi interface
    home_json["network"]["primary_interface"] = "wlan0"
    home_data = EnvoyInterfaceInformation.from_api(home_json)

    # verify interface data
    assert home_data
    assert home_data.mac == "60:E8:5B:AB:9D:64"
    assert home_data.primary_interface == "wlan0"
    assert home_data.interface_type == "wifi"

    # test missing interface key
    home_json["network"]["primary_interface"] = "missing"
    home_data = EnvoyInterfaceInformation.from_api(home_json)
    assert home_data is None

    # test handling missing interfaces part
    del home_json["network"]["interfaces"]
    home_data = EnvoyInterfaceInformation.from_api(home_json)
    assert not home_data

    # test handling missing network part
    del home_json["network"]
    home_data = EnvoyInterfaceInformation.from_api(home_json)
    assert not home_data


@pytest.mark.asyncio
async def test_interface_settings_with_7_6_175(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test home interface information data"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)

    # start with regular data first
    version = "7.6.175"

    # Use prep_envoy to set up all required mocks
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # Create envoy using get_mock_envoy which handles all the setup
    envoy = await get_mock_envoy(version, test_client_session, update=False)

    # test interface_settings method
    home_data: EnvoyInterfaceInformation | None = await envoy.interface_settings()

    # validate common data
    assert home_data
    assert home_data.software_build_epoch == 1719503966
    assert home_data.dhcp
    assert home_data.timezone == "Europe/Amsterdam"

    # validate interface data
    assert home_data.mac == "00:1D:C0:7F:B6:3B"
    assert home_data.primary_interface == "eth0"
    assert home_data.interface_type == "ethernet"

    # load mock data for home endpoint
    home_json = await load_json_fixture(version, "home")
    # Change mock to use wlan interface
    home_json["network"]["primary_interface"] = "wlan0"
    # and mock new data
    override_mock(
        mock_aioresponse, "get", "https://127.0.0.1/home", status=200, payload=home_json
    )

    # get interface data, subsequent call data is returned from cache
    home_data = await envoy.interface_settings()

    # interface data should come from cache and still be the same
    assert home_data
    assert home_data.mac == "00:1D:C0:7F:B6:3B"
    assert home_data.primary_interface == "eth0"
    assert home_data.interface_type == "ethernet"

    # call setup to invalidate cached interface data
    await envoy.setup()

    # now interface data should be reflect latest mocked data and reflect wlan interface
    home_data = await envoy.interface_settings()
    assert home_data
    assert home_data.mac == "60:E8:5B:AB:9D:64"
    assert home_data.primary_interface == "wlan0"
    assert home_data.interface_type == "wifi"


@pytest.mark.asyncio
async def test_home_endpoint_errors_with_7_6_175(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test home interface information data"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    caplog.set_level(logging.DEBUG)

    # start with regular data first
    version = "7.6.175"

    # Set up auth mocks
    start_7_firmware_mock(mock_aioresponse)

    # Set up info endpoint for setup
    info_data = await load_fixture(version, "info")
    mock_aioresponse.get(
        "https://127.0.0.1/info", status=200, body=info_data, repeat=True
    )

    # Create and setup envoy
    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    await envoy.authenticate("username", "password")

    # test not-found error
    mock_aioresponse.get("https://127.0.0.1/home", status=404)
    await envoy.interface_settings()
    assert "Failure getting interface information" in caplog.text
    caplog.clear()

    # test server error
    mock_aioresponse.get("https://127.0.0.1/home", status=500)
    await envoy.interface_settings()
    assert "Failure getting interface information" in caplog.text
    caplog.clear()

    mock_aioresponse.get(
        "https://127.0.0.1/home", exception=aiohttp.ClientError("Test Networkerror")
    )
    await envoy.interface_settings()
    assert "Failure getting interface information" in caplog.text
    caplog.clear()

    mock_aioresponse.get(
        "https://127.0.0.1/home", exception=aiohttp.ClientError("Test protocolerror")
    )
    # interface_settings catches and logs exceptions, doesn't re-raise
    await envoy.interface_settings()
    assert "Failure getting interface information" in caplog.text
    caplog.clear()

    mock_aioresponse.get(
        "https://127.0.0.1/home",
        exception=asyncio.TimeoutError("Test timeoutexception"),
    )
    await envoy.interface_settings()
    assert "Failure getting interface information" in caplog.text
