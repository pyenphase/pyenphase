"""Test endpoint for envoy v7 and newer firmware"""

import logging

import aiohttp
import pytest
from aioresponses import aioresponses
from syrupy.assertion import SnapshotAssertion

from pyenphase.envoy import SupportedFeatures

from .common import (
    get_mock_envoy,
    prep_envoy,
    start_7_firmware_mock,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    (
        "version",
        "supported_features",
        "updaters",
    ),
    [
        (
            "8.3.5167_3rd-pv",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyEnembleUpdater": SupportedFeatures.ENCHARGE,
                "EnvoyMetersUpdater": SupportedFeatures.CTMETERS
                | SupportedFeatures.DUALPHASE,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
        ),
    ],
    ids=[
        "8.3.5167_3rd-pv",
    ],
)
@pytest.mark.asyncio
async def test_with_7_x_firmware(
    version: str,
    snapshot: SnapshotAssertion,
    supported_features: SupportedFeatures,
    updaters: dict[str, SupportedFeatures],
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify with 7.x firmware."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)

    await get_mock_envoy(test_client_session)
