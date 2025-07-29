"""Test endpoint for envoy v7 and newer firmware"""

import logging

import aiohttp
import pytest
from aioresponses import aioresponses
from syrupy.assertion import SnapshotAssertion

from pyenphase.models.dry_contacts import DryContactType

from .common import (
    get_mock_envoy,
    prep_envoy,
    start_7_firmware_mock,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    (
        "version",
        "dry_contacts",
    ),
    [
        (
            "8.3.5167_3rd-pv",
            {
                "NC1": DryContactType.THRDPV,
                "NC2": DryContactType.NONE,
                "NO1": DryContactType.NONE,
                "NO2": DryContactType.NONE,
            },
        ),
        (
            "8.2.127_with_generator_running",
            {
                "NC1": DryContactType.NONE,
                "NC2": DryContactType.NONE,
                "NO1": DryContactType.LOAD,
                "NO2": DryContactType.LOAD,
            },
        ),
    ],
    ids=[
        "8.3.5167_3rd-pv",
        "8.2.127_with_generator_running",
    ],
)
@pytest.mark.asyncio
async def test_dry_contact_type(
    version: str,
    snapshot: SnapshotAssertion,
    dry_contacts: dict[str, DryContactType],
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify with 7.x firmware."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)

    data = envoy.data
    assert data is not None

    for contact, type in dry_contacts.items():
        assert data.dry_contact_settings[contact].type == type
