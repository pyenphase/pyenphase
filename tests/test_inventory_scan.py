"""Test Envoy inventory scan"""

import logging
from typing import Any

import aiohttp
import pytest
from aioresponses import aioresponses

from pyenphase.const import URL_INVENTORY

from .common import (
    endpoint_path,
    get_mock_envoy,
    override_mock,
    prep_envoy,
    start_7_firmware_mock,
)


@pytest.mark.asyncio
async def test_inventory_scan_with_acb(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Verify inverter and AC Battery firmware on a system with AC Batteries."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", "8.3.5169_ACB_inventory")
    envoy = await get_mock_envoy(test_client_session, update=False)

    assert await envoy.inventory_scan() == {
        "122013000000": "520-00082-r01-v04.30.32",
        "122012100000": "520-00082-r01-v04.30.32",
        "121917000000": "520-00092-r01-v02.13.02",
        "122047000000": "520-00092-r01-v02.13.02",
    }


@pytest.mark.asyncio
async def test_inventory_scan_skips_entries(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Verify the scan reads only active PCU and ACB devices that report a serial
    number and firmware.
    """
    version = "8.3.5169_ACB_inventory"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    envoy = await get_mock_envoy(test_client_session, update=False)
    override_mock(
        mock_aioresponse,
        "get",
        f"{endpoint_path(version, '127.0.0.1')}{URL_INVENTORY}",
        status=200,
        payload=[
            {
                "type": "PCU",
                "devices": [
                    {"serial_num": "1", "img_pnum_running": "fw-1"},
                    {"serial_num": "2", "img_pnum_running": "fw-2", "admin_state": 0},
                    {"serial_num": "3"},
                    {"img_pnum_running": "fw-4"},
                    "5",
                ],
            },
            {
                "type": "NSRB",
                "devices": [{"serial_num": "6", "img_pnum_running": "fw-6"}],
            },
        ],
    )

    assert await envoy.inventory_scan() == {"1": "fw-1"}


@pytest.mark.parametrize(
    "reply",
    [{"status": 404}, {"status": 200, "payload": {"error": "404 - Not Found"}}],
    ids=["not_found", "unusable"],
)
@pytest.mark.asyncio
async def test_inventory_scan_failure(
    reply: dict[str, Any],
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Verify the scan logs a failed request or an unusable reply and returns an
    empty dict.
    """
    caplog.set_level(logging.DEBUG)
    version = "8.3.5169_with_generator"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    envoy = await get_mock_envoy(test_client_session, update=False)
    override_mock(
        mock_aioresponse,
        "get",
        f"{endpoint_path(version, '127.0.0.1')}{URL_INVENTORY}",
        **reply,
    )

    assert await envoy.inventory_scan() == {}
    assert "Failure getting inventory firmware" in caplog.text
