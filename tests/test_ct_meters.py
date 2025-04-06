"""Test envoy metered with enabled and disabled CT"""

import logging

import pytest
import respx
from httpx import Response

from pyenphase import register_updater
from pyenphase.envoy import SupportedFeatures
from pyenphase.models.meters import CtMeterData, CtType, EnvoyMeterData
from pyenphase.models.system_consumption import EnvoySystemConsumption
from pyenphase.models.system_production import EnvoySystemProduction
from pyenphase.updaters.meters import EnvoyMetersUpdater

from .common import (
    get_mock_envoy,
    load_fixture,
    load_json_fixture,
    load_json_list_fixture,
    prep_envoy,
    start_7_firmware_mock,
    updater_features,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
@respx.mock
async def test_pr111_with_7_3_466_metered_disabled_cts():
    """Test envoy metered with disabled ct to report from production inverters PR111."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.3.466_metered_disabled_cts"
    start_7_firmware_mock()
    await prep_envoy(version)

    envoy = await get_mock_envoy()
    data = envoy.data
    assert data is not None

    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert envoy._supported_features & SupportedFeatures.PRODUCTION
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert envoy._supported_features & SupportedFeatures.PRODUCTION
    assert updater_features(envoy._updaters) == {
        "EnvoyProductionJsonFallbackUpdater": SupportedFeatures.PRODUCTION,
        "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
        "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
    }
    assert envoy.part_number == "800-00654-r08"

    assert not data.system_consumption
    assert data.system_production.watts_now == 751
    assert data.system_production.watt_hours_today == 4425
    assert data.system_production.watt_hours_last_7_days == 111093
    assert data.system_production.watt_hours_lifetime == 702919


@pytest.mark.asyncio
@respx.mock
async def test_pr111_with_7_6_175_with_cts():
    """Test envoy metered with ct to report from production eim PR111."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_with_cts"
    start_7_firmware_mock()
    await prep_envoy(version)

    envoy = await get_mock_envoy()
    data = envoy.data
    assert data is not None

    assert envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION
    assert envoy._supported_features & SupportedFeatures.NET_CONSUMPTION
    assert envoy._supported_features & SupportedFeatures.PRODUCTION
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert envoy._supported_features & SupportedFeatures.METERING
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert envoy._supported_features & SupportedFeatures.CTMETERS
    assert updater_features(envoy._updaters) == {
        "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
        "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
        | SupportedFeatures.TOTAL_CONSUMPTION
        | SupportedFeatures.NET_CONSUMPTION
        | SupportedFeatures.PRODUCTION,
        "EnvoyMetersUpdater": SupportedFeatures.CTMETERS,
        "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
    }

    assert envoy.part_number == "800-00654-r08"

    assert data.system_consumption
    assert data.system_production.watts_now == 488
    assert data.system_production.watt_hours_today == 4425
    assert data.system_production.watt_hours_last_7_days == 111093
    assert data.system_production.watt_hours_lifetime == 3183793
    assert (
        envoy.envoy_model
        == "Envoy, phases: 1, phase mode: three, net-consumption CT, production CT"
    )


@pytest.mark.asyncio
@respx.mock
async def test_pr111_with_7_6_175_standard():
    """Test envoy metered with ct to report from production eim PR111."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    start_7_firmware_mock()
    await prep_envoy(version)

    envoy = await get_mock_envoy()
    data = envoy.data
    assert data is not None

    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert envoy._supported_features & SupportedFeatures.PRODUCTION
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert updater_features(envoy._updaters) == {
        "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
        "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
    }

    assert envoy.part_number == "800-00656-r06"

    assert not data.system_consumption
    assert data.system_production.watts_now == 5740
    assert data.system_production.watt_hours_today == 36462
    assert data.system_production.watt_hours_last_7_days == 189712
    assert data.system_production.watt_hours_lifetime == 6139406
    assert envoy.envoy_model == "Envoy"


@pytest.mark.asyncio
@respx.mock
async def test_ct_data_structures_with_7_3_466_with_cts_3phase():
    """Test meters model using envoy metered CT with multiple phases"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)

    # start with regular data first
    version = "7.3.466_with_cts_3phase"
    start_7_firmware_mock()
    await prep_envoy(version)

    # details of this test is done elsewhere already, just check data is returned
    envoy = await get_mock_envoy()
    data = envoy.data
    assert data is not None

    # Test prior similar updater active
    remove_2nd_metersupdater = register_updater(EnvoyMetersUpdater)
    await envoy.probe()
    remove_2nd_metersupdater()

    # load mock data for meters and their readings
    meters_status = await load_json_list_fixture(version, "ivp_meters")
    meters_readings = await load_json_list_fixture(version, "ivp_meters_readings")

    meter_status: CtMeterData = {
        "eid": meters_status[0]["eid"],
        "state": meters_status[0]["state"],
        "measurementType": meters_status[0]["measurementType"],
        "phaseMode": meters_status[0]["phaseMode"],
        "phaseCount": meters_status[0]["phaseCount"],
        "meteringStatus": meters_status[0]["meteringStatus"],
        "statusFlags": meters_status[0]["statusFlags"],
    }

    # test meters.from_api method
    ct_data: EnvoyMeterData = EnvoyMeterData.from_api(
        meters_readings[0],
        meter_status,
    )
    assert ct_data.eid == 704643328
    assert ct_data.measurement_type == "production"

    # test meters.from_phase method
    ct_phase_data: EnvoyMeterData | None = EnvoyMeterData.from_phase(
        meters_readings[0], meter_status, 0
    )
    assert ct_phase_data is not None
    assert ct_phase_data.eid == 1778385169
    assert ct_phase_data.measurement_type == "production"
    assert ct_phase_data.energy_delivered == 3183794

    assert (
        envoy.envoy_model
        == "Envoy, phases: 3, phase mode: three, net-consumption CT, production CT"
    )

    # test exception handling by specifying non-existing phase
    ct_no_phase_data = EnvoyMeterData.from_phase(meters_readings[0], meter_status, 3)
    assert ct_no_phase_data is None

    # test exception handling for missing phase data, remove phase data from mock data
    del meters_readings[0]["channels"]
    ct_no_phase_data = EnvoyMeterData.from_phase(meters_readings[0], meter_status, 0)
    assert ct_no_phase_data is None

    # test exception handling for phase data in production using wrong phase
    production_data = data.raw["/production.json?details=1"]
    production_no_phase_data = EnvoySystemProduction.from_production_phase(
        production_data, 3
    )
    assert production_no_phase_data is None

    # test exception handling for phase data if key is missing
    del production_data["production"][1]["type"]
    try:
        production_no_phase_data = EnvoySystemProduction.from_production_phase(
            production_data, 0
        )
    except ValueError:
        production_no_phase_data = None
    assert production_no_phase_data is None

    # test exception handling for phase data in consumption using wrong phase
    consumption_data = data.raw["/production.json?details=1"]
    consumption_no_phase_data = EnvoySystemConsumption.from_production_phase(
        consumption_data, 3
    )
    assert consumption_no_phase_data is None

    # test handling missing phases when expected in ct readings
    meters_status = await load_json_list_fixture(version, "ivp_meters")
    meters_readings = await load_json_list_fixture(version, "ivp_meters_readings")

    # remove phase data from CT readings
    del meters_readings[0]["channels"]
    del meters_readings[1]["channels"]

    respx.get("/ivp/meters").mock(return_value=Response(200, json=meters_status))
    respx.get("/ivp/meters/readings").mock(
        return_value=Response(200, json=meters_readings)
    )

    await envoy.update()
    assert envoy.data.ctmeter_production_phases is None
    assert envoy.data.ctmeter_consumption_phases is None


@pytest.mark.asyncio
@respx.mock
async def test_ct_data_structures_with_7_6_175_with_cts_3phase():
    """Test meters model using envoy metered CT with multiple phases"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)

    # start with regular data first
    version = "7.6.175_with_cts_3phase"
    start_7_firmware_mock()
    await prep_envoy(version)

    # details of this test is done elsewhere already, just check data is returned
    envoy = await get_mock_envoy()
    data = envoy.data
    assert data is not None

    # Test prior similar updater active
    remove_2nd_metersupdater = register_updater(EnvoyMetersUpdater)
    await envoy.probe()
    remove_2nd_metersupdater()

    # load mock data for meters and their readings
    meters_status = await load_json_list_fixture(version, "ivp_meters")
    meters_readings = await load_json_list_fixture(version, "ivp_meters_readings")

    meter_status: CtMeterData = {
        "eid": meters_status[0]["eid"],
        "state": meters_status[0]["state"],
        "measurementType": meters_status[0]["measurementType"],
        "phaseMode": meters_status[0]["phaseMode"],
        "phaseCount": meters_status[0]["phaseCount"],
        "meteringStatus": meters_status[0]["meteringStatus"],
        "statusFlags": meters_status[0]["statusFlags"],
    }

    # test meters.from_api method
    ct_data: EnvoyMeterData = EnvoyMeterData.from_api(
        meters_readings[0],
        meter_status,
    )
    assert ct_data.eid == 704643328
    assert ct_data.measurement_type == "production"

    # test meters.from_phase method
    ct_phase_data: EnvoyMeterData | None = EnvoyMeterData.from_phase(
        meters_readings[0], meter_status, 0
    )
    assert ct_phase_data is not None
    assert ct_phase_data.eid == 1778385169
    assert ct_phase_data.measurement_type == "production"
    assert ct_phase_data.energy_delivered == 3183794

    assert (
        envoy.envoy_model
        == "Envoy, phases: 3, phase mode: three, net-consumption CT, production CT"
    )

    # test exception handling by specifying non-existing phase
    ct_no_phase_data = EnvoyMeterData.from_phase(meters_readings[0], meter_status, 3)
    assert ct_no_phase_data is None

    # test exception handling for missing phase data, remove phase data from mock data
    del meters_readings[0]["channels"]
    ct_no_phase_data = EnvoyMeterData.from_phase(meters_readings[0], meter_status, 0)
    assert ct_no_phase_data is None

    # test exception handling for phase data if key is missing
    production_data = data.raw["/production.json?details=1"]
    del production_data["production"][1]["type"]
    with pytest.raises(ValueError):
        EnvoySystemProduction.from_production_phase(production_data, 0)


@pytest.mark.asyncio
@respx.mock
async def test_ct_data_structures_with_7_6_175_with_total_cts_3phase():
    """Test meters model using envoy metered without production CT and total-consumption CT with multiple phases"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)

    # start with regular data first
    version = "7.6.175_with_cts_3phase"
    start_7_firmware_mock()
    await prep_envoy(version)
    production_json = await load_json_fixture(version, "production.json")
    # remove production data to test COV consumption ct only
    del production_json["production"]
    respx.get("/production.json").mock(return_value=Response(200, json=production_json))
    respx.get("/production.json?details=1").mock(
        return_value=Response(200, json=production_json)
    )

    # Force ct consumption meter to total consumption for COV
    ivp_Meters = (await load_fixture(version, "ivp_meters")).replace(
        CtType.NET_CONSUMPTION, CtType.TOTAL_CONSUMPTION
    )
    respx.get("/ivp/meters").mock(return_value=Response(200, text=ivp_Meters))

    # details of this test is done elsewhere already, just check data is returned
    envoy = await get_mock_envoy()
    data = envoy.data
    assert data is not None

    assert (
        envoy.envoy_model
        == "Envoy, phases: 3, phase mode: three, total-consumption CT, production CT"
    )


@pytest.mark.asyncio
@respx.mock
async def test_ct_storage_with_8_2_127_with_3cts_and_battery_split():
    """Test meters model using envoy metered CT with multiple phases"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)

    # start with regular data first
    version = "8.2.127_with_3cts_and_battery_split"
    start_7_firmware_mock()
    await prep_envoy(version)

    # details of this test is done elsewhere already, just check data is returned
    envoy = await get_mock_envoy()
    data = envoy.data
    assert data is not None

    # load mock data for meters and their readings
    meters_status = await load_json_list_fixture(version, "ivp_meters")
    meters_readings = await load_json_list_fixture(version, "ivp_meters_readings")

    meter_status: CtMeterData = {
        "eid": meters_status[2]["eid"],
        "state": meters_status[2]["state"],
        "measurementType": meters_status[2]["measurementType"],
        "phaseMode": meters_status[2]["phaseMode"],
        "phaseCount": meters_status[2]["phaseCount"],
        "meteringStatus": meters_status[2]["meteringStatus"],
        "statusFlags": meters_status[2]["statusFlags"],
    }

    # test meters.from_api method
    ct_data: EnvoyMeterData = EnvoyMeterData.from_api(
        meters_readings[2],
        meter_status,
    )
    assert ct_data.eid == 704643840
    assert ct_data.measurement_type == "storage"

    # test meters.from_phase method
    ct_phase_data: EnvoyMeterData | None = EnvoyMeterData.from_phase(
        meters_readings[2], meter_status, 0
    )
    assert ct_phase_data is not None
    assert ct_phase_data.eid == 1778385681
    assert ct_phase_data.measurement_type == "storage"
    assert ct_phase_data.energy_delivered == 1136860

    assert (
        envoy.envoy_model
        == "Envoy, phases: 2, phase mode: split, net-consumption CT, production CT, storage CT"
    )

    # test exception handling by specifying non-existing phase
    ct_no_phase_data = EnvoyMeterData.from_phase(meters_readings[2], meter_status, 3)
    assert ct_no_phase_data is None

    # test exception handling for missing phase data, remove phase data from mock data
    del meters_readings[2]["channels"]
    ct_no_phase_data = EnvoyMeterData.from_phase(meters_readings[2], meter_status, 0)
    assert ct_no_phase_data is None

    respx.get("/ivp/meters").mock(return_value=Response(200, json=meters_status))
    respx.get("/ivp/meters/readings").mock(
        return_value=Response(200, json=meters_readings)
    )

    await envoy.update()
    assert envoy.data.ctmeter_storage_phases is None


@pytest.mark.asyncio
@respx.mock
async def test_ct_storage_data_without_meter_entry_with_8_2_127_with_3cts_and_battery_split():
    """Test meters model with additional meter readings entry not in meters config"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)

    # start with regular data first we use this fixture to test issue reported in 8.3.5025
    version = "8.2.127_with_3cts_and_battery_split"
    start_7_firmware_mock()
    await prep_envoy(version)

    # fw D8.3.5027 has 3th (zero) entry for Storage CT, even if not configured
    # this caused Indexerror crash. Test if extra data is now handled without crash
    readings_data = await load_json_list_fixture(version, "ivp_meters_readings")
    readings_data.append({"eid": 1023410688, "channels": [{}, {}, {}]})
    respx.get("/ivp/meters/readings").mock(
        return_value=Response(200, json=readings_data)
    )

    # details of this test is done elsewhere already, just check data is returned
    envoy = await get_mock_envoy()
    data = envoy.data
    assert data is not None
