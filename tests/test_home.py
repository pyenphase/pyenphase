"""Test envoy home endpoint"""

import logging

import httpx
import pytest
import respx
from httpx import Response

from pyenphase.models.home import EnvoyInterfaceInformation

from .common import (
    get_mock_envoy,
    load_json_fixture,
    prep_envoy,
    start_7_firmware_mock,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
@respx.mock
async def test_home_from_api_with_7_6_175():
    """Test home data from api"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)

    # start with regular data first
    version = "7.6.175"
    start_7_firmware_mock()
    await prep_envoy(version)

    # details of this test is done elsewhere already, just check data is returned
    envoy = await get_mock_envoy()
    data = envoy.data
    assert data is not None

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
@respx.mock
async def test_interface_settings_with_7_6_175():
    """Test home interface information data"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)

    # start with regular data first
    version = "7.6.175"
    start_7_firmware_mock()
    await prep_envoy(version)

    # details of this test is done elsewhere already, just check data is returned
    envoy = await get_mock_envoy()
    data = envoy.data
    assert data is not None

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
    respx.get("/home").mock(return_value=Response(200, json=home_json))

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
@respx.mock
async def test_home_endpoint_errors_with_7_6_175(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test home interface information data"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    caplog.set_level(logging.DEBUG)

    # start with regular data first
    version = "7.6.175"
    start_7_firmware_mock()
    await prep_envoy(version)

    # details of this test is done elsewhere already, just check data is returned
    envoy = await get_mock_envoy()
    data = envoy.data
    assert data is not None

    # test not-found error
    respx.get("/home").mock(return_value=Response(404))
    await envoy.interface_settings()
    assert "Failure getting interface information" in caplog.text
    caplog.clear()

    # test server error
    respx.get("/home").mock(return_value=Response(500))
    await envoy.interface_settings()
    assert "Failure getting interface information" in caplog.text
    caplog.clear()

    respx.get("/home").mock(return_value=Response(200, text="")).side_effect = [
        httpx.NetworkError("Test Networkerror"),
    ]
    await envoy.interface_settings()
    assert "Failure getting interface information" in caplog.text
    caplog.clear()

    respx.get("/home").mock(return_value=Response(200, text="")).side_effect = [
        httpx.RemoteProtocolError("Test protocolerror"),
    ]
    with pytest.raises(httpx.RemoteProtocolError):
        await envoy.interface_settings()

    respx.get("/home").mock(return_value=Response(200, text="")).side_effect = [
        httpx.TimeoutException("Test timeoutexception"),
    ]
    await envoy.interface_settings()
    assert "Failure getting interface information" in caplog.text
