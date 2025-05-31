"""Test specific envoy firmware issues post v7."""

import logging

import aiohttp
import pytest
from aioresponses import aioresponses

from pyenphase.envoy import SupportedFeatures

from .common import (
    get_mock_envoy,
    prep_envoy,
    start_7_firmware_mock,
    updater_features,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    (
        "version",
        "part_number",
        "updaters",
        "watts_now",
        "watt_hours_today",
        "watt_hours_last_7_days",
        "watt_hours_lifetime",
    ),
    [
        (
            "8.2.4264_metered_noct",
            "800-00554-r03",
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonFallbackUpdater": SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
            5521,
            70,
            1521,
            32465106,
        ),
        (
            "7.6.114_without_cts",
            "800-00656-r06",
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
            },
            586,
            10363,
            101742,
            1544282,
        ),
        (
            "7.3.466_metered_disabled_cts",
            "800-00654-r08",
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonFallbackUpdater": SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
            751,
            4425,
            111093,
            702919,
        ),
    ],
    ids=[
        "8.2.4264_metered_noct",
        "7.6.114_without_cts",
        "7.3.466_metered_disabled_cts",
    ],
)
@pytest.mark.asyncio
async def test_metered_noct(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    part_number: str,
    updaters: dict[str, SupportedFeatures],
    caplog: pytest.LogCaptureFixture,
    watts_now: int,
    watt_hours_today: int,
    watt_hours_last_7_days: int,
    watt_hours_lifetime: int,
) -> None:
    """
    Tests Envoy metered production data without CTs across firmware versions.
    
    This asynchronous test verifies that Envoy devices without current transformers (CTs) report correct production metrics and feature support for various firmware and hardware configurations. It mocks HTTP responses, prepares the Envoy environment, and asserts that production data and updater features match expected values for each parameterized scenario.
    """
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None

    assert updater_features(envoy._updaters) == updaters
    assert envoy.part_number == part_number
    assert envoy.phase_count == 1

    assert not data.system_consumption
    assert envoy.ct_meter_count == 0
    assert envoy.phase_mode is None
    assert envoy.consumption_meter_type is None
    assert not data.system_consumption_phases
    assert not data.system_production_phases
    assert data.system_production is not None
    assert data.system_production.watts_now == watts_now
    assert data.system_production.watt_hours_today == watt_hours_today
    assert data.system_production.watt_hours_last_7_days == watt_hours_last_7_days
    assert data.system_production.watt_hours_lifetime == watt_hours_lifetime
