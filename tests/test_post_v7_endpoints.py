"""Test specific envoy firmware issues post v7."""

import logging

import pytest
import respx

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
@respx.mock
async def test_metered_noct(
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
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    start_7_firmware_mock()
    await prep_envoy(version)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy()
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
    assert data.system_production.watts_now == watts_now
    assert data.system_production.watt_hours_today == watt_hours_today
    assert data.system_production.watt_hours_last_7_days == watt_hours_last_7_days
    assert data.system_production.watt_hours_lifetime == watt_hours_lifetime
