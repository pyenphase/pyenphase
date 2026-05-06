"""Test ACB battery data and combined Encharge/ACB"""

import logging
from typing import Any

import aiohttp
import pytest
from aioresponses import aioresponses
from syrupy.assertion import SnapshotAssertion

from pyenphase.envoy import SupportedFeatures
from pyenphase.models.acb import EnvoyACB
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
    version = "4.2.27"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)
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
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
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
    assert not (acb_power != {}) ^ (data.acb_power is not None)
    assert not (battery_aggregate != {}) ^ (data.battery_aggregate is not None)

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
    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data
    assert envoy.acb_count == 0

    # test with activeCount  = 1 and missing percentFull key
    prod_json = await load_json_fixture(version, "production.json")
    prod_json["storage"][0].pop("percentFull", None)
    prod_json["storage"][0]["activeCount"] = 1
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/production.json?details=1",
        status=200,
        payload=prod_json,
        repeat=True,
    )
    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data
    assert envoy.acb_count == 0
    assert data.acb_power is None


@pytest.mark.asyncio
async def test_acb_per_device_inventory(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Test per-device ACB inventory parsing from ivp_ensemble_inventory type ACB."""
    version = "8.2.4382_ACB_2"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None

    # ACB feature detected from inventory
    assert envoy.supported_features & SupportedFeatures.ACB
    assert envoy.acb_count == 2

    # Aggregate ACB power from production.json storage segment
    assert data.acb_power is not None
    assert data.acb_power.power == 0
    assert data.acb_power.charge_wh == 446
    assert data.acb_power.state_of_charge == 18
    assert data.acb_power.state == "idle"
    assert data.acb_power.batteries == 2

    # Per-device inventory available
    assert data.acb_inventory is not None
    assert envoy.acb_inventory is not None
    assert len(data.acb_inventory) == 2
    assert "122000000001" in data.acb_inventory
    assert "122000000002" in data.acb_inventory

    # Verify first device fields
    acb0 = data.acb_inventory["122000000001"]
    assert acb0.serial_num == "122000000001"
    assert acb0.part_num == "800-00930-r03"
    assert acb0.sleep_enabled is False
    assert acb0.charge_status == "discharging"
    assert acb0.device_status == ["envoy.global.ok"]
    assert acb0.sleep_state == "awake"
    assert acb0.percent_full == 0
    assert acb0.max_cell_temp == 18
    assert acb0.communicating is True
    assert acb0.operating is True
    assert acb0.producing is True
    assert acb0.sleep_min_soc == 25
    assert acb0.sleep_max_soc == 30
    assert acb0.last_report_date == 1778091218
    # Per-device power from inverters endpoint (devType=11)
    assert acb0.last_report_watts == 0
    assert acb0.max_report_watts == 140

    # Verify second device fields
    acb1 = data.acb_inventory["122000000002"]
    assert acb1.serial_num == "122000000002"
    assert acb1.device_status == ["envoy.global.ok"]
    assert acb1.sleep_state == "awake"
    assert acb1.last_report_date == 1778091219
    assert acb1.percent_full == 1
    assert acb1.max_cell_temp == 27
    assert acb1.last_report_watts == 0
    assert acb1.max_report_watts == 272

    # Solar inverters (devType=1) should NOT appear in acb_inventory
    assert "122000010001" not in data.acb_inventory

    # Solar inverters still available in inverters dict
    assert "122000010001" in data.inverters
    assert "122000010002" in data.inverters
    assert "122000010003" in data.inverters


@pytest.mark.asyncio
async def test_acb_per_device_missing_optional_fields(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Test EnvoyACB.from_api handles missing optional fields gracefully."""
    version = "8.2.4382_ACB_2"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # Override inventory with a device missing optional fields (simulates faulted device)
    full_host = endpoint_path(version, "127.0.0.1")
    minimal_inventory = [
        {
            "type": "ACB",
            "devices": [
                {
                    "serial_num": "122000000001",
                    "device_status": ["envoy.cond_flags.pcu_ctrl.sleep-mode"],
                    # intentionally omit: part_num, sleep_enabled, charge_status,
                    # percentFull, maxCellTemp, sleep_min_soc, sleep_max_soc,
                    # communicating, operating, producing
                }
            ],
        }
    ]
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/ivp/ensemble/inventory",
        status=200,
        payload=minimal_inventory,
        repeat=True,
    )
    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None
    assert data.acb_inventory is not None

    acb = data.acb_inventory["122000000001"]
    assert acb.serial_num == "122000000001"
    assert acb.part_num == ""
    assert acb.sleep_enabled is False
    assert acb.charge_status == "unknown"
    assert acb.device_status == ["envoy.cond_flags.pcu_ctrl.sleep-mode"]
    assert acb.sleep_state == "waking"
    assert acb.percent_full == 0
    assert acb.max_cell_temp is None
    assert acb.communicating is False
    assert acb.operating is False
    assert acb.producing is False
    assert acb.sleep_min_soc is None
    assert acb.sleep_max_soc is None
    assert acb.last_report_date == 1778091218


@pytest.mark.asyncio
async def test_set_acb_sleep(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Test set_acb_sleep sends correct PUT to /admin/lib/acb_config.json."""
    import orjson

    from .common import latest_request

    version = "8.2.4382_ACB_2"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    full_host = endpoint_path(version, "127.0.0.1")
    mock_aioresponse.put(
        f"{full_host}/admin/lib/acb_config.json",
        status=200,
        payload={
            "acb_sleep": [
                {"serial_num": "122000000001", "sleep_min_soc": 10, "sleep_max_soc": 20}
            ]
        },
        repeat=True,
    )

    envoy = await get_mock_envoy(test_client_session)

    configs = [{"serial_num": "122000000001", "sleep_min_soc": 10, "sleep_max_soc": 20}]
    result = await envoy.set_acb_sleep(configs)
    assert result is not None

    _cnt, request_data = latest_request(
        mock_aioresponse, "PUT", "/admin/lib/acb_config.json"
    )
    assert orjson.loads(request_data) == {
        "acb_sleep": [
            {"serial_num": "122000000001", "sleep_min_soc": 10, "sleep_max_soc": 20}
        ]
    }


@pytest.mark.asyncio
async def test_set_acb_sleep_validation(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Test set_acb_sleep raises ValueError on invalid inputs."""
    version = "8.2.4382_ACB_2"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)

    # Empty configs
    with pytest.raises(ValueError, match="empty"):
        await envoy.set_acb_sleep([])

    # Missing serial_num
    with pytest.raises(ValueError, match="serial_num"):
        await envoy.set_acb_sleep([{"sleep_min_soc": 10, "sleep_max_soc": 20}])

    # Empty serial_num
    with pytest.raises(ValueError, match="must not be empty"):
        await envoy.set_acb_sleep(
            [{"serial_num": "", "sleep_min_soc": 10, "sleep_max_soc": 20}]
        )

    # Blank serial_num
    with pytest.raises(ValueError, match="must not be empty"):
        await envoy.set_acb_sleep(
            [{"serial_num": "   ", "sleep_min_soc": 10, "sleep_max_soc": 20}]
        )

    # Missing sleep_min_soc
    with pytest.raises(ValueError, match="sleep_min_soc"):
        await envoy.set_acb_sleep([{"serial_num": "122000000001", "sleep_max_soc": 20}])

    # Missing sleep_max_soc
    with pytest.raises(ValueError, match="sleep_max_soc"):
        await envoy.set_acb_sleep([{"serial_num": "122000000001", "sleep_min_soc": 10}])

    # Out-of-range sleep_min_soc
    with pytest.raises(ValueError, match="sleep_min_soc"):
        await envoy.set_acb_sleep(
            [{"serial_num": "122000000001", "sleep_min_soc": -1, "sleep_max_soc": 20}]
        )

    # Out-of-range sleep_max_soc
    with pytest.raises(ValueError, match="sleep_max_soc"):
        await envoy.set_acb_sleep(
            [{"serial_num": "122000000001", "sleep_min_soc": 10, "sleep_max_soc": 101}]
        )

    # Non-numeric SOC values
    with pytest.raises(ValueError, match="must be numeric integers"):
        await envoy.set_acb_sleep(
            [
                {
                    "serial_num": "122000000001",
                    "sleep_min_soc": "not-a-number",
                    "sleep_max_soc": 20,
                }
            ]
        )

    # sleep_min_soc must be <= sleep_max_soc
    with pytest.raises(ValueError, match="must be <= sleep_max_soc"):
        await envoy.set_acb_sleep(
            [{"serial_num": "122000000001", "sleep_min_soc": 80, "sleep_max_soc": 20}]
        )


@pytest.mark.asyncio
async def test_set_acb_sleep_not_available(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Test set_acb_sleep raises EnvoyFeatureNotAvailable when ACB not supported."""
    from pyenphase.exceptions import EnvoyFeatureNotAvailable

    version = "7.3.517"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)
    assert not (envoy.supported_features & SupportedFeatures.ACB)

    with pytest.raises(EnvoyFeatureNotAvailable):
        await envoy.set_acb_sleep(
            [{"serial_num": "122000000001", "sleep_min_soc": 10, "sleep_max_soc": 20}]
        )


@pytest.mark.asyncio
async def test_clear_acb_sleep(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Test clear_acb_sleep sends correct DELETE to /admin/lib/acb_config.json."""
    import orjson

    from .common import latest_request

    version = "8.2.4382_ACB_2"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    full_host = endpoint_path(version, "127.0.0.1")
    mock_aioresponse.delete(
        f"{full_host}/admin/lib/acb_config.json",
        status=200,
        payload={"message": "success"},
        repeat=True,
    )

    envoy = await get_mock_envoy(test_client_session)

    result = await envoy.clear_acb_sleep(["122000000001", "122000000002"])
    assert result == {"message": "success"}

    _cnt, request_data = latest_request(
        mock_aioresponse, "DELETE", "/admin/lib/acb_config.json"
    )
    assert orjson.loads(request_data) == {
        "acb_sleep": [
            {"serial_num": "122000000001"},
            {"serial_num": "122000000002"},
        ]
    }


@pytest.mark.asyncio
async def test_clear_acb_sleep_validation(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Test clear_acb_sleep validation."""
    version = "8.2.4382_ACB_2"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)

    with pytest.raises(ValueError, match="empty"):
        await envoy.clear_acb_sleep([])

    with pytest.raises(ValueError, match="must not be empty"):
        await envoy.clear_acb_sleep([""])


@pytest.mark.asyncio
async def test_clear_acb_sleep_not_available(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Test clear_acb_sleep raises EnvoyFeatureNotAvailable when ACB unsupported."""
    from pyenphase.exceptions import EnvoyFeatureNotAvailable

    version = "7.3.517"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)
    with pytest.raises(EnvoyFeatureNotAvailable):
        await envoy.clear_acb_sleep(["122000000001"])


def test_acb_sleep_state_variants_and_from_api_without_inverter() -> None:
    """Cover sleep_state branches and from_api path without inverter data."""
    asleep = EnvoyACB.from_api(
        {
            "serial_num": "122000000010",
            "sleep_enabled": True,
            "device_status": ["envoy.cond_flags.pcu_ctrl.sleep-mode"],
        }
    )
    assert asleep.sleep_state == "asleep"
    assert asleep.last_report_date is None
    assert asleep.last_report_watts is None
    assert asleep.max_report_watts is None

    going_to_sleep = EnvoyACB.from_api(
        {
            "serial_num": "122000000011",
            "sleep_enabled": True,
            "device_status": [],
        }
    )
    assert going_to_sleep.sleep_state == "going_to_sleep"


@pytest.mark.asyncio
async def test_acb_inventory_property_without_data(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Cover Envoy.acb_inventory when no data has been loaded yet."""
    version = "8.2.4382_ACB_2"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)
    envoy.data = None

    assert envoy.acb_inventory is None
