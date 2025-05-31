"""Test endpoint for envoy v7 and newer firmware"""

import logging
from typing import Any

import aiohttp
import pytest
from aioresponses import aioresponses
from syrupy.assertion import SnapshotAssertion

from pyenphase.const import PhaseNames
from pyenphase.envoy import SupportedFeatures
from pyenphase.models.envoy import EnvoyData

from .common import (
    get_mock_envoy,
    prep_envoy,
    start_7_firmware_mock,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_with_4_2_27_firmware(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Tests Envoy integration with firmware version 4.2.27 to ensure net and total consumption features are not reported.
    
    Verifies that the Envoy instance does not support total or net consumption features and that system net consumption data is absent.
    """
    version = "4.2.27"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)
    data: EnvoyData | None = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert not data.system_net_consumption
    assert not data.system_net_consumption_phases


@pytest.mark.parametrize(
    (
        "version",
        "supported_features",
        "phase_count",
        "net_consumption",
        "net_consumption_phases",
    ),
    [
        (
            "5.0.62",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            1,
            {},
            {},
        ),
        (
            "4.10.35",
            SupportedFeatures.METERING
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.CTMETERS,
            2,
            {},
            {},
        ),
        (
            "7.3.130",
            SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION,
            1,
            {},
            {},
        ),
        (
            "7.3.130_no_consumption",
            SupportedFeatures.METERING
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.CTMETERS,
            2,
            {},
            {},
        ),
        (
            "7.3.517",
            SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            1,
            {},
            {},
        ),
        (
            "7.3.517_legacy_savings_mode",
            SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            1,
            {},
            {},
        ),
        (
            "7.3.517_system_2",
            SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.CTMETERS,
            2,
            {
                "watt_hours_lifetime": -2662919,
                "watt_hours_last_7_days": 0,
                "watt_hours_today": 0,
                "watts_now": 48,
            },
            {},
        ),
        (
            "7.3.466_metered_disabled_cts",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            1,
            {},
            {},
        ),
        (
            "7.6.114_without_cts",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            1,
            {},
            {},
        ),
        (
            "7.6.175",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            1,
            {},
            {},
        ),
        (
            "7.6.175_total",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            1,
            {},
            {},
        ),
        (
            "7.6.175_standard",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            1,
            {
                "watt_hours_lifetime": 1961513,
                "watt_hours_last_7_days": 0,
                "watt_hours_today": 0,
                "watts_now": -11,
            },
            {},
        ),
        (
            "7.6.175_with_cts",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.CTMETERS,
            1,
            {},
            {},
        ),
        (
            "7.6.175_with_cts_3phase",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.THREEPHASE
            | SupportedFeatures.CTMETERS,
            3,
            {
                "watt_hours_lifetime": 2886562,
                "watt_hours_last_7_days": 29891,
                "watt_hours_today": 2200,
                "watts_now": 216,
            },
            {
                PhaseNames.PHASE_1: {
                    "watt_hours_lifetime": 1625201,
                    "watt_hours_last_7_days": 0,
                    "watt_hours_today": 0,
                    "watts_now": 91,
                },
                PhaseNames.PHASE_2: {
                    "watt_hours_lifetime": 629892,
                    "watt_hours_last_7_days": 0,
                    "watt_hours_today": 0,
                    "watts_now": 123,
                },
                PhaseNames.PHASE_3: {
                    "watt_hours_lifetime": 631469,
                    "watt_hours_last_7_days": 0,
                    "watt_hours_today": 0,
                    "watts_now": 1,
                },
            },
        ),
        (
            "7.3.466_with_cts_3phase",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.THREEPHASE
            | SupportedFeatures.CTMETERS,
            3,
            {
                "watt_hours_lifetime": 2886562,
                "watt_hours_last_7_days": 0,
                "watt_hours_today": 0,
                "watts_now": 216,
            },
            {
                PhaseNames.PHASE_1: {
                    "watt_hours_lifetime": 1625201,
                    "watt_hours_last_7_days": 0,
                    "watt_hours_today": 0,
                    "watts_now": 91,
                },
                PhaseNames.PHASE_2: {
                    "watt_hours_lifetime": 629892,
                    "watt_hours_last_7_days": 0,
                    "watt_hours_today": 0,
                    "watts_now": 123,
                },
                PhaseNames.PHASE_3: {
                    "watt_hours_lifetime": 631469,
                    "watt_hours_last_7_days": 0,
                    "watt_hours_today": 0,
                    "watts_now": 1,
                },
            },
        ),
        (
            "7.6.185_with_cts_and_battery_3t",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.TARIFF
            | SupportedFeatures.CTMETERS,
            1,
            {
                "watt_hours_lifetime": 1279038,
                "watt_hours_last_7_days": 0,
                "watt_hours_today": 0,
                "watts_now": 525,
            },
            {},
        ),
        (
            "8.1.41",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.PRODUCTION,
            1,
            {
                "watt_hours_lifetime": 1279038,
                "watt_hours_last_7_days": 0,
                "watt_hours_today": 0,
                "watts_now": -7812,
            },
            {},
        ),
        (
            "8.2.127_with_3cts_and_battery_split",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.TARIFF
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.CTMETERS,
            2,
            {
                "watt_hours_lifetime": 4744550,
                "watt_hours_last_7_days": 0,
                "watt_hours_today": 0,
                "watts_now": 129,
            },
            {},
        ),
        (
            "8.2.127_with_generator_running",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.TARIFF
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.CTMETERS
            | SupportedFeatures.GENERATOR,
            2,
            {
                "watt_hours_lifetime": 7298714,
                "watt_hours_last_7_days": 0,
                "watt_hours_today": 0,
                "watts_now": 240,
            },
            {},
        ),
    ],
    ids=[
        "5.0.62",
        "4.10.35",
        "7.3.130",
        "7.3.130_no_consumption",
        "7.3.517",
        "7.3.517_legacy_savings_mode",
        "7.3.517_system_2",
        "7.3.466_metered_disabled_cts",
        "7.6.114_without_cts",
        "7.6.175",
        "7.6.175_total",
        "7.6.175_standard",
        "7.6.175_with_cts",
        "7.6.175_with_cts_3phase",
        "7.3.466_with_cts_3phase",
        "7.6.185_with_cts_and_battery_3t",
        "8.1.41",
        "8.2.127_with_3cts_and_battery_split",
        "8.2.127_with_generator_running",
    ],
)
@pytest.mark.asyncio
async def test_with_7_x_firmware(
    version: str,
    snapshot: SnapshotAssertion,
    supported_features: SupportedFeatures,
    caplog: pytest.LogCaptureFixture,
    phase_count: int,
    net_consumption: dict[str, Any],
    net_consumption_phases: dict[str, dict[str, Any]],
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """
    Tests Envoy integration with 7.x and newer firmware versions for correct net consumption reporting.
    
    Verifies that the Envoy instance correctly reports supported features, phase count, and net consumption data—including per-phase metrics—according to the provided firmware version and expected values. Asserts that the retrieved data matches the expected snapshot and that all net consumption phases are accurately reported.
    """
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data
    assert data == snapshot

    assert envoy.phase_count == phase_count

    # are all net consumption phases reported
    expected_phases = net_consumption_phases == {}
    actual_phases = data.system_net_consumption_phases is None
    assert not (expected_phases ^ actual_phases)

    reported_phase_count = envoy.active_phase_count
    # are all net consumption phases reported
    expected_phase_count = len(net_consumption_phases)
    assert expected_phase_count == reported_phase_count

    # are all consumption phases reported
    assert (
        envoy.active_phase_count == 0
        if data.system_net_consumption_phases is None
        else len(data.system_net_consumption_phases)
    )
    # Test each consumption phase
    for phase in net_consumption_phases:
        assert data.system_net_consumption_phases
        assert (consdata := data.system_net_consumption_phases[phase])
        modeldata = net_consumption_phases[phase]

        # test each element of the phase data
        assert consdata.watt_hours_lifetime == modeldata["watt_hours_lifetime"]
        assert consdata.watt_hours_last_7_days == modeldata["watt_hours_last_7_days"]
        assert consdata.watt_hours_today == modeldata["watt_hours_today"]
        assert consdata.watts_now == modeldata["watts_now"]
