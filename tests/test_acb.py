"""Test ACB battery data and combined Encharge/ACB"""

import json
import logging
from os import listdir
from os.path import isfile, join
from typing import Any

import pytest
import respx
from httpx import Response
from syrupy.assertion import SnapshotAssertion

from pyenphase.envoy import SupportedFeatures
from pyenphase.models.envoy import EnvoyData

from .common import (
    get_mock_envoy,
    load_fixture,
    load_json_fixture,
    start_7_firmware_mock,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
@respx.mock
async def test_with_4_2_27_firmware():
    """Verify with 4.2.27 firmware."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "4.2.27"
    respx.get("/info").mock(
        return_value=Response(200, text=load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(return_value=Response(404))
    respx.get("/production.json").mock(
        return_value=Response(200, json=load_json_fixture(version, "production.json"))
    )
    respx.get("/api/v1/production").mock(
        return_value=Response(200, json=load_json_fixture(version, "api_v1_production"))
    )
    respx.get("/api/v1/production/inverters").mock(return_value=Response(404))

    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if "admin_lib_tariff" in files:
        try:
            json_data = load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/admin/lib/tariff").mock(return_value=Response(404))

    if "ivp_ss_gen_config" in files:
        try:
            json_data = load_json_fixture(version, "ivp_ss_gen_config")
        except json.decoder.JSONDecodeError:
            json_data = {}
        respx.get("/ivp/ss/gen_config").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/ivp/ss/gen_config").mock(return_value=Response(200, json={}))

    respx.get("/ivp/meters").mock(return_value=Response(200, json=[]))

    envoy = await get_mock_envoy()
    data: EnvoyData | None = envoy.data
    assert data is not None
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
@respx.mock
async def test_with_7_x_firmware(
    version: str,
    snapshot: SnapshotAssertion,
    supported_features: SupportedFeatures,
    caplog: pytest.LogCaptureFixture,
    acb_count: int,
    battery_aggregate: dict[str, Any],
    acb_power: dict[str, dict[str, Any]],
) -> None:
    """Verify with 7.x firmware.

    Test with fixture that have SupportedFeatures.METERING

    """
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    start_7_firmware_mock()
    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    respx.get("/info").mock(
        return_value=Response(200, text=load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))

    if "production" in files:
        try:
            json_data = load_json_fixture(version, "production")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/production").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/production").mock(return_value=Response(404))

    if "production.json" in files:
        respx.get("/production.json").mock(
            return_value=Response(
                200, json=load_json_fixture(version, "production.json")
            )
        )
        respx.get("/production.json?details=1").mock(
            return_value=Response(
                200, json=load_json_fixture(version, "production.json")
            )
        )
    else:
        respx.get("/production.json").mock(return_value=Response(404))
        respx.get("/production.json?details=1").mock(return_value=Response(404))

    respx.get("/api/v1/production").mock(
        return_value=Response(200, json=load_json_fixture(version, "api_v1_production"))
    )
    respx.get("/api/v1/production/inverters").mock(
        return_value=Response(
            200, json=load_json_fixture(version, "api_v1_production_inverters")
        )
    )
    respx.get("/ivp/ensemble/inventory").mock(
        return_value=Response(
            200, json=load_json_fixture(version, "ivp_ensemble_inventory")
        )
    )

    if "ivp_ensemble_dry_contacts" in files:
        try:
            json_data = load_json_fixture(version, "ivp_ensemble_dry_contacts")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/ivp/ensemble/dry_contacts").mock(
            return_value=Response(200, json=json_data)
        )
        respx.post("/ivp/ensemble/dry_contacts").mock(
            return_value=Response(200, json=json_data)
        )

    if "ivp_ss_dry_contact_settings" in files:
        try:
            json_data = load_json_fixture(version, "ivp_ss_dry_contact_settings")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/ivp/ss/dry_contact_settings").mock(
            return_value=Response(200, json=json_data)
        )
        respx.post("/ivp/ss/dry_contact_settings").mock(
            return_value=Response(200, json=json_data)
        )

    if "ivp_ensemble_power" in files:
        try:
            json_data = load_json_fixture(version, "ivp_ensemble_power")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/ivp/ensemble/power").mock(
            return_value=Response(200, json=json_data)
        )

    if "ivp_ensemble_secctrl" in files:
        try:
            json_data = load_json_fixture(version, "ivp_ensemble_secctrl")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/ivp/ensemble/secctrl").mock(
            return_value=Response(200, json=json_data)
        )

    if "admin_lib_tariff" in files:
        try:
            json_data = load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
        respx.put("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/admin/lib/tariff").mock(return_value=Response(404))

    if "ivp_meters" in files:
        respx.get("/ivp/meters").mock(
            return_value=Response(200, json=load_json_fixture(version, "ivp_meters"))
        )
    else:
        respx.get("/ivp/meters").mock(return_value=Response(404))

    if "ivp_meters_readings" in files:
        respx.get("/ivp/meters/readings").mock(
            return_value=Response(
                200, json=load_json_fixture(version, "ivp_meters_readings")
            )
        )
    else:
        respx.get("/ivp/meters/readings").mock(return_value=Response(404))

    if "ivp_ss_gen_config" in files:
        try:
            json_data = load_json_fixture(version, "ivp_ss_gen_config")
        except json.decoder.JSONDecodeError:
            json_data = {}
        respx.get("/ivp/ss/gen_config").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/ivp/ss/gen_config").mock(return_value=Response(200, json={}))

    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy()
    assert (data := envoy.data)
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
        assert battery_aggregate[key] == getattr(envoy.data.battery_aggregate, key)

    # test ACB battery values
    for key in acb_power:
        assert acb_power[key] == getattr(envoy.data.acb_power, key)

    # test for code coverage if no storage section is available
    # use fixtures with METERING in supported_features:
    production_data = data.raw["/production.json?details=1"]

    acb_data = production_data["storage"][0]
    assert acb_data["activeCount"] == acb_count

    # test with missing storage section
    prod_json = load_json_fixture(version, "production.json")
    del prod_json["storage"]
    respx.get("/production.json").mock(return_value=Response(200, json=prod_json))
    envoy = await get_mock_envoy()
    assert (data := envoy.data)
    assert envoy.acb_count == 0
