"""Test ACB battery data and combined Encharge/ACB"""

import logging
from typing import Any

import aiohttp
import pytest
from aioresponses import aioresponses
from syrupy.assertion import SnapshotAssertion

from pyenphase.envoy import SupportedFeatures
from pyenphase.models.envoy import EnvoyData

from .common import (
    endpoint_path,
    get_mock_envoy,
    load_json_fixture,
    override_mock,
    prep_envoy,
    start_7_firmware_mock,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_with_4_2_27_firmware(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Verify with 4.2.27 firmware."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "4.2.27"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(version, test_client_session)
    data: EnvoyData | None = envoy.data
    assert data is not None
    assert envoy._supported_features is not None
    assert not (envoy._supported_features & SupportedFeatures.ACB)
    assert not (envoy._supported_features & SupportedFeatures.ENCHARGE)
    assert not (envoy._supported_features & SupportedFeatures.ENPOWER)
    assert envoy.acb_count == 0


@pytest.mark.parametrize(
    (
        "version",
        "supported_features",
        "acb_count",
        "battery_aggregate",
        "acb_power",
    ),
    [
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
            0,
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
            0,
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
            0,
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
            0,
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
            0,
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
            0,
            {},
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
            0,
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
            0,
            {},
            {},
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
            0,
            {},
            {},
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
            0,
            {},
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
            0,
            {},
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
            0,
            {},
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
            0,
            {},
            {},
        ),
        (
            "8.2.4382_ACB",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.TARIFF
            | SupportedFeatures.CTMETERS
            | SupportedFeatures.ACB,
            3,
            {
                "available_energy": 2820,
                "max_available_capacity": 7220,
                "state_of_charge": 39,
            },
            {
                "power": 260,
                "charge_wh": 930,
                "state_of_charge": 25,
                "state": "discharging",
                "batteries": 3,
            },
        ),
    ],
    ids=[
        "4.10.35",
        "7.3.130",
        "7.3.130_no_consumption",
        "7.3.517",
        "7.3.517_legacy_savings_mode",
        "7.3.517_system_2",
        "7.6.175_with_cts",
        "7.6.175_with_cts_3phase",
        "7.3.466_with_cts_3phase",
        "7.6.185_with_cts_and_battery_3t",
        "8.1.41",
        "8.2.127_with_3cts_and_battery_split",
        "8.2.127_with_generator_running",
        "8.2.4382_ACB",
    ],
)
@pytest.mark.asyncio
async def test_with_7_x_firmware(
    version: str,
    snapshot: SnapshotAssertion,
    supported_features: SupportedFeatures,
    caplog: pytest.LogCaptureFixture,
    acb_count: int,
    battery_aggregate: dict[str, Any],
    acb_power: dict[str, dict[str, Any]],
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """
    Verify with 7.x firmware.

    Test with fixture that have SupportedFeatures.METERING

    """
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(version, test_client_session)
    full_host = endpoint_path(version, envoy.host)
    data = envoy.data
    assert data
    assert data == snapshot

    assert envoy.acb_count == acb_count

    # verify both have ACB or both don't have it
    assert not (
        (SupportedFeatures.ACB in envoy.supported_features)
        ^ (SupportedFeatures.ACB in supported_features)
    )
    # verify if acb_power andACB feature are both present or not
    assert not (acb_power != {}) ^ (SupportedFeatures.ACB in envoy.supported_features)

    # verify both are empty/None or both have values
    assert not (acb_power != {}) ^ (envoy.data.acb_power is not None)
    assert not (battery_aggregate != {}) ^ (envoy.data.battery_aggregate is not None)

    # test battery aggregate values
    for key in battery_aggregate:
        assert data.battery_aggregate is not None
        assert battery_aggregate[key] == getattr(data.battery_aggregate, key)

    # test ACB battery values
    for key in acb_power:
        assert data.acb_power is not None
        assert acb_power[key] == getattr(data.acb_power, key)

    # test for code coverage if no storage section is available
    # use fixtures with METERING in supported_features:
    production_data = data.raw["/production.json?details=1"]

    acb_data = production_data["storage"][0]
    assert acb_data["activeCount"] == acb_count

    # test with missing storage section
    prod_json = await load_json_fixture(version, "production.json")
    del prod_json["storage"]
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/production.json?details=1",
        status=200,
        payload=prod_json,
        repeat=True,
    )
    envoy = await get_mock_envoy(version, test_client_session)
    data = envoy.data
    assert data
    assert envoy.acb_count == 0
