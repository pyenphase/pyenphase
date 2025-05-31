"""Test envoy metered with enabled and disabled CT"""

import logging

import aiohttp
import pytest
from aioresponses import aioresponses

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
    mock_response,
    prep_envoy,
    start_7_firmware_mock,
    updater_features,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_pr111_with_7_3_466_metered_disabled_cts(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Tests Envoy firmware 7.3.466 with metered disabled CTs, verifying that only production and inverter features are supported and that system consumption data is absent while production data is present and correct.
    """
    version = "7.3.466_metered_disabled_cts"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

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
    assert data.system_production is not None
    assert data.system_production.watts_now == 751
    assert data.system_production.watt_hours_today == 4425
    assert data.system_production.watt_hours_last_7_days == 111093
    assert data.system_production.watt_hours_lifetime == 702919


@pytest.mark.asyncio
async def test_pr111_with_7_6_175_with_cts(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Validates Envoy firmware 7.6.175 with CT meters enabled for correct feature support and data reporting.

    This test asserts that the Envoy instance supports total and net consumption, production, inverters, metering, and CT meter features. It verifies correct updater registration, part number, and ensures that system consumption and production data are present and accurate. The Envoy model string is also checked for expected configuration details.
    """
    version = "7.6.175_with_cts"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

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
    assert data.system_production is not None
    assert data.system_production.watts_now == 488
    assert data.system_production.watt_hours_today == 4425
    assert data.system_production.watt_hours_last_7_days == 111093
    assert data.system_production.watt_hours_lifetime == 3183793
    assert (
        envoy.envoy_model
        == "Envoy, phases: 1, phase mode: three, net-consumption CT, production CT"
    )


@pytest.mark.asyncio
async def test_pr111_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Validates Envoy firmware 7.6.175 standard (without CTs) for correct feature support and production data.

    This test ensures that total and net consumption features are not supported, while production and inverters features are present. It verifies updater registrations, part number, absence of system consumption data, correctness of system production values, and the Envoy model string.
    """
    version = "7.6.175_standard"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

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
    assert data.system_production is not None
    assert data.system_production.watts_now == 5740
    assert data.system_production.watt_hours_today == 36462
    assert data.system_production.watt_hours_last_7_days == 189712
    assert data.system_production.watt_hours_lifetime == 6139406
    assert envoy.envoy_model == "Envoy"


@pytest.mark.asyncio
async def test_ct_data_structures_with_7_3_466_with_cts_3phase(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Tests CT meter data structures and exception handling for Envoy firmware 7.3.466 with CTs and three phases.

    This test verifies correct parsing and construction of CT meter data from API responses, including handling of multiple phases, missing phase data, and invalid phase indices. It asserts the integrity of EnvoyMeterData and EnvoySystemProduction/Consumption objects, and ensures that missing or malformed phase data is handled gracefully without causing crashes.
    """
    # start with regular data first
    version = "7.3.466_with_cts_3phase"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # details of this test is done elsewhere already, just check data is returned
    envoy = await get_mock_envoy(test_client_session)
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

    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters",
        reset=True,
        status=200,
        payload=meters_status,
        repeat=True,
    )
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters/readings",
        reset=True,
        status=200,
        payload=meters_readings,
        repeat=True,
    )

    await envoy.update()
    data = envoy.data
    assert data is not None
    assert data.ctmeter_production_phases is None
    assert data.ctmeter_consumption_phases is None


@pytest.mark.asyncio
async def test_ct_data_structures_with_7_6_175_with_cts_3phase(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Tests Envoy firmware 7.6.175 with CT meters and three phases, verifying correct parsing and handling of CT meter data structures, including multi-phase support and error handling for missing or invalid phase data.

    This test loads mock meter status and readings, constructs meter data objects using from_api and from_phase methods, and asserts their properties. It also checks that the Envoy model string is correct and verifies that appropriate exceptions or None values are returned when phase data is missing or invalid.
    """
    # start with regular data first
    version = "7.6.175_with_cts_3phase"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # details of this test is done elsewhere already, just check data is returned
    envoy = await get_mock_envoy(test_client_session)
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
async def test_ct_data_structures_with_7_6_175_with_total_cts_3phase(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Tests Envoy firmware 7.6.175 with three-phase CTs, simulating absence of production CT and presence of total-consumption CT.

    Removes production data from the fixture and modifies the CT meter type to total consumption, then verifies that Envoy data is returned and the model string reflects the correct CT configuration.
    """
    # start with regular data first
    version = "7.6.175_with_cts_3phase"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    production_json = await load_json_fixture(version, "production.json")
    # remove production data to test COV consumption ct only
    del production_json["production"]
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/production.json",
        reset=True,
        status=200,
        payload=production_json,
        repeat=True,
    )
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/production.json?details=1",
        reset=True,
        status=200,
        payload=production_json,
        repeat=True,
    )

    # Force ct consumption meter to total consumption for COV
    ivp_Meters = (await load_fixture(version, "ivp_meters")).replace(
        CtType.NET_CONSUMPTION, CtType.TOTAL_CONSUMPTION
    )
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters",
        reset=True,
        status=200,
        body=ivp_Meters,
        repeat=True,
    )

    # details of this test is done elsewhere already, just check data is returned
    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None

    assert (
        envoy.envoy_model
        == "Envoy, phases: 3, phase mode: three, total-consumption CT, production CT"
    )


@pytest.mark.asyncio
async def test_ct_storage_with_8_2_127_with_3cts_and_battery_split(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Tests Envoy firmware 8.2.127 with three CTs and battery split configuration, verifying correct handling of storage CT meter data across multiple phases.

    This test loads meter status and readings fixtures, constructs CT meter data using both the full API and individual phase methods, and asserts their properties. It checks for correct Envoy model identification, validates exception handling for invalid or missing phase data, and ensures that after updating with incomplete readings, the storage CT meter phases are set to None.
    """
    # start with regular data first
    version = "8.2.127_with_3cts_and_battery_split"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # details of this test is done elsewhere already, just check data is returned
    envoy = await get_mock_envoy(test_client_session)
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

    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters",
        reset=True,
        status=200,
        payload=meters_status,
        repeat=True,
    )
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters/readings",
        reset=True,
        status=200,
        payload=meters_readings,
        repeat=True,
    )

    await envoy.update()
    data = envoy.data
    assert data is not None
    assert data.ctmeter_storage_phases is None


@pytest.mark.asyncio
async def test_ct_storage_data_without_meter_entry_with_8_2_127_with_3cts_and_battery_split(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Verifies that Envoy firmware 8.2.127 with 3 CTs and battery split handles extra meter readings entries not present in the meters configuration without crashing.

    This test simulates a firmware issue where an additional meter reading entry is returned by the API, ensuring that the Envoy data remains accessible and no IndexError occurs.
    """
    # start with regular data first we use this fixture to test issue reported in 8.3.5025
    version = "8.2.127_with_3cts_and_battery_split"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # fw D8.3.5027 has 3th (zero) entry for Storage CT, even if not configured
    # this caused Indexerror crash. Test if extra data is now handled without crash
    readings_data = await load_json_list_fixture(version, "ivp_meters_readings")
    readings_data.append({"eid": 1023410688, "channels": [{}, {}, {}]})
    mock_response(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters/readings",
        reset=True,
        status=200,
        payload=readings_data,
        repeat=True,
    )

    # details of this test is done elsewhere already, just check data is returned
    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None
