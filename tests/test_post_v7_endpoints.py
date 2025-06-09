"""Test specific envoy firmware issues post v7."""

import logging

import aiohttp
import pytest
from aioresponses import aioresponses

from pyenphase.envoy import UPDATERS, Envoy, SupportedFeatures, register_updater
from pyenphase.updaters.api_v1_production_inverters import (
    EnvoyApiV1ProductionInvertersUpdater,
)
from pyenphase.updaters.device_data_inverters import EnvoyDeviceDataInvertersUpdater

from .common import get_mock_envoy, prep_envoy, start_7_firmware_mock, updater_features

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
    """Verify metered without CT production data with pre and post 8.2.4264 firmware."""
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


@pytest.mark.asyncio
async def test_multiple_inverter_sources(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Test that multiple inverters from different sources are handled correctly."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", "8.2.4345_with_device_data")

    envoy = Envoy("127.0.0.1", client=test_client_session)
    await envoy.setup()
    await envoy.authenticate("username", "password")

    # Preserve the original updaters
    original_updaters = UPDATERS.copy()

    # Remove existing inverter updaters
    UPDATERS[:] = [
        updater
        for updater in UPDATERS
        if updater
        not in (EnvoyApiV1ProductionInvertersUpdater, EnvoyDeviceDataInvertersUpdater)
    ]

    # Add the inverter production endpoint updater followed by the device data updater
    prod_remover = register_updater(EnvoyApiV1ProductionInvertersUpdater)
    device_data_remover = register_updater(EnvoyDeviceDataInvertersUpdater)

    # Verify that the production updater is used first
    await envoy.probe()
    assert updater_features(envoy._updaters) == {
        "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
        "EnvoyEnembleUpdater": SupportedFeatures.ENCHARGE | SupportedFeatures.ENPOWER,
        "EnvoyMetersUpdater": SupportedFeatures.CTMETERS,
        "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
        | SupportedFeatures.TOTAL_CONSUMPTION
        | SupportedFeatures.NET_CONSUMPTION
        | SupportedFeatures.PRODUCTION,
        "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
    }

    # Remove both updaters and re-add them in reverse order
    prod_remover()
    device_data_remover()
    device_data_remover = register_updater(EnvoyDeviceDataInvertersUpdater)
    prod_remover = register_updater(EnvoyApiV1ProductionInvertersUpdater)

    # Verify that the device data updater is used first
    await envoy.probe()
    assert updater_features(envoy._updaters) == {
        "EnvoyDeviceDataInvertersUpdater": SupportedFeatures.INVERTERS
        | SupportedFeatures.DETAILED_INVERTERS,
        "EnvoyEnembleUpdater": SupportedFeatures.ENCHARGE | SupportedFeatures.ENPOWER,
        "EnvoyMetersUpdater": SupportedFeatures.CTMETERS,
        "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
        | SupportedFeatures.TOTAL_CONSUMPTION
        | SupportedFeatures.NET_CONSUMPTION
        | SupportedFeatures.PRODUCTION,
        "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
    }

    # Restore the original updaters
    UPDATERS.clear()
    for updater in original_updaters:
        register_updater(updater)
