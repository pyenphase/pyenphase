"""Test envoy metered with enabled and disabled CT"""

import logging
from typing import Any

import aiohttp
import jsonpath
import pytest
from aioresponses import aioresponses
from syrupy.assertion import SnapshotAssertion

from pyenphase import register_updater
from pyenphase.const import (
    PHASENAMES,
    SupportedFeatures,
)
from pyenphase.models.meters import (
    CtMeterData,
    CtType,
    EnvoyMeterData,
    EnvoyPhaseMode,
)
from pyenphase.models.system_consumption import EnvoySystemConsumption
from pyenphase.models.system_production import EnvoySystemProduction
from pyenphase.updaters.meters import EnvoyMetersUpdater

from .common import (
    get_mock_envoy,
    load_fixture,
    load_json_fixture,
    load_json_list_fixture,
    override_mock,
    prep_envoy,
    start_7_firmware_mock,
    updater_features,
)

# we're testing, ignore some issue reports
# pyright: reportPrivateUsage=false

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_pr111_with_7_3_466_metered_disabled_cts(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test envoy metered with disabled ct to report from production inverters PR111."""
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
    """Test envoy metered with ct to report from production eim PR111."""
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
        == "Envoy, phases: 1, phase mode: three, production CT, net-consumption CT"
    )


@pytest.mark.asyncio
async def test_pr111_with_7_6_175_standard(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test envoy metered with ct to report from production eim PR111."""
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
    """Test meters model using envoy metered CT with multiple phases"""
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
        == "Envoy, phases: 3, phase mode: three, production CT, net-consumption CT"
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

    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters",
        status=200,
        payload=meters_status,
        repeat=True,
    )
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters/readings",
        status=200,
        payload=meters_readings,
        repeat=True,
    )

    await envoy.update()
    data = envoy.data
    assert data is not None
    # should not have phase data after removing phase data from source
    assert data.ctmeters_phases == {}


@pytest.mark.asyncio
async def test_ct_data_structures_with_7_6_175_with_cts_3phase(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test meters model using envoy metered CT with multiple phases"""
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
        == "Envoy, phases: 3, phase mode: three, production CT, net-consumption CT"
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
    """Test meters model using envoy metered without production CT and total-consumption CT with multiple phases"""
    # start with regular data first
    version = "7.6.175_with_cts_3phase"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    production_json = await load_json_fixture(version, "production.json")
    # remove production data to test COV consumption ct only
    del production_json["production"]
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/production.json",
        status=200,
        payload=production_json,
        repeat=True,
    )
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/production.json?details=1",
        status=200,
        payload=production_json,
        repeat=True,
    )

    # Force ct consumption meter to total consumption for COV
    ivp_Meters = (await load_fixture(version, "ivp_meters")).replace(
        CtType.NET_CONSUMPTION, CtType.TOTAL_CONSUMPTION
    )
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters",
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
        == "Envoy, phases: 3, phase mode: three, production CT, total-consumption CT"
    )


@pytest.mark.asyncio
async def test_ct_storage_with_8_2_127_with_3cts_and_battery_split(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test meters model using envoy metered CT with multiple phases"""
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
        == "Envoy, phases: 2, phase mode: split, production CT, net-consumption CT, storage CT"
    )

    # test exception handling by specifying non-existing phase
    ct_no_phase_data = EnvoyMeterData.from_phase(meters_readings[2], meter_status, 3)
    assert ct_no_phase_data is None

    # test exception handling for missing phase data, remove phase data from mock data
    del meters_readings[2]["channels"]
    ct_no_phase_data = EnvoyMeterData.from_phase(meters_readings[2], meter_status, 0)
    assert ct_no_phase_data is None

    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters",
        status=200,
        payload=meters_status,
        repeat=True,
    )
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters/readings",
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
    """Test meters model with additional meter readings entry not in meters config"""
    # start with regular data first we use this fixture to test issue reported in 8.3.5025
    version = "8.2.127_with_3cts_and_battery_split"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # fw D8.3.5027 has 3th (zero) entry for Storage CT, even if not configured
    # this caused Indexerror crash. Test if extra data is now handled without crash
    readings_data = await load_json_list_fixture(version, "ivp_meters_readings")
    readings_data.append({"eid": 1023410688, "channels": [{}, {}, {}]})
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters/readings",
        status=200,
        payload=readings_data,
        repeat=True,
    )

    # details of this test is done elsewhere already, just check data is returned
    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None


@pytest.mark.asyncio
async def test_yet_unknown_ct_with_8_2_127_with_3cts_and_battery_split(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """Test meters model with yet unknown ct type in meters config and readings"""
    # start with regular data first we use this fixture to test issue reported in 8.3.5025
    version = "8.2.127_with_3cts_and_battery_split"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    yet_unknown_ct_type: str = "this_should_work"

    # change last meter type to one not in CtType
    meters_data = await load_json_list_fixture(version, "ivp_meters")
    meter = meters_data[-1]
    assert meter
    meter["measurementType"] = yet_unknown_ct_type
    del meters_data[-1]
    meters_data.append(meter)

    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters",
        status=200,
        payload=meters_data,
        repeat=True,
    )

    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None

    # verify yet unknown type is now in ct list and has data with this label
    assert yet_unknown_ct_type in envoy.ct_meter_list
    assert data.ctmeters[yet_unknown_ct_type]
    assert data.ctmeters[yet_unknown_ct_type].state == meter["state"]
    assert data.ctmeters[yet_unknown_ct_type].eid == meter["eid"]
    assert envoy.meter_type(yet_unknown_ct_type) == yet_unknown_ct_type

    # last one in original list was storage ct. Should not be there anymore
    assert data.ctmeter_storage is None
    assert CtType.STORAGE not in data.ctmeters
    assert CtType.STORAGE not in data.ctmeters_phases


@pytest.mark.parametrize(
    ("test_properties",),
    [
        pytest.param(
            {
                "ctMeters": 2,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "meter_types": [
                    CtType.NET_CONSUMPTION,
                    CtType.PRODUCTION,
                ],
            },
            id="4.10.35",
        ),
        pytest.param(
            {
                "ctMeters": 1,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "meter_types": [
                    CtType.PRODUCTION,
                ],
            },
            id="7.3.130_no_consumption",
        ),
        pytest.param(
            {
                "ctMeters": 2,
                "phaseCount": 3,
                "phaseMode": EnvoyPhaseMode.THREE,
                "meter_types": [
                    CtType.NET_CONSUMPTION,
                    CtType.PRODUCTION,
                ],
            },
            id="7.3.466_with_cts_3phase",
        ),
        pytest.param(
            {
                "ctMeters": 2,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "meter_types": [
                    CtType.NET_CONSUMPTION,
                    CtType.PRODUCTION,
                ],
            },
            id="7.3.517_system_2",
        ),
        pytest.param(
            {
                "ctMeters": 2,
                "phaseCount": 1,
                "phaseMode": EnvoyPhaseMode.THREE,
                "meter_types": [
                    CtType.NET_CONSUMPTION,
                    CtType.PRODUCTION,
                ],
            },
            id="7.6.175_with_cts",
        ),
        pytest.param(
            {
                "ctMeters": 2,
                "phaseCount": 3,
                "phaseMode": EnvoyPhaseMode.THREE,
                "meter_types": [
                    CtType.NET_CONSUMPTION,
                    CtType.PRODUCTION,
                ],
            },
            id="7.6.175_with_cts_3phase",
        ),
        pytest.param(
            {
                "ctMeters": 2,
                "phaseCount": 1,
                "phaseMode": EnvoyPhaseMode.THREE,
                "meter_types": [
                    CtType.NET_CONSUMPTION,
                    CtType.PRODUCTION,
                ],
            },
            id="7.6.185_with_cts_and_battery_3t",
        ),
        pytest.param(
            {
                "ctMeters": 3,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "meter_types": [
                    CtType.NET_CONSUMPTION,
                    CtType.PRODUCTION,
                    CtType.STORAGE,
                ],
            },
            id="8.2.127_with_3cts_and_battery_split",
        ),
        pytest.param(
            {
                "ctMeters": 2,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "meter_types": [
                    CtType.NET_CONSUMPTION,
                    CtType.PRODUCTION,
                ],
            },
            id="8.2.127_with_generator_running",
        ),
        pytest.param(
            {
                "ctMeters": 3,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "meter_types": [
                    CtType.NET_CONSUMPTION,
                    CtType.PRODUCTION,
                    CtType.STORAGE,
                ],
            },
            id="8.2.4286_with_3cts_and_battery_split",
        ),
        pytest.param(
            {
                "ctMeters": 2,
                "phaseCount": 1,
                "phaseMode": EnvoyPhaseMode.THREE,
                "meter_types": [
                    CtType.NET_CONSUMPTION,
                    CtType.PRODUCTION,
                ],
            },
            id="8.2.4345_with_device_data",
        ),
        pytest.param(
            {
                "ctMeters": 4,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "meter_types": [
                    CtType.NET_CONSUMPTION,
                    CtType.PRODUCTION,
                    CtType.STORAGE,
                    "backfeed",
                ],
            },
            id="8.3.1598_collar",
        ),
    ],
)
@pytest.mark.asyncio
async def test_current_transformers(
    snapshot: SnapshotAssertion,
    caplog: pytest.LogCaptureFixture,
    test_properties: dict[str, Any],
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    request: pytest.FixtureRequest,
) -> None:
    """Test Current transformer data and properties."""
    caplog.set_level(logging.WARNING)
    start_7_firmware_mock(mock_aioresponse)

    # verify test parameter completeness
    assert len(test_properties) == 4

    # get version and fixture folder from test id
    version: Any = request.node.callspec.id
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)

    # load data
    data = envoy.data
    assert data is not None
    assert data == snapshot

    # verify expected properties
    assert envoy.ct_meter_count == test_properties["ctMeters"]
    assert envoy.phase_count == test_properties["phaseCount"]
    assert envoy.phase_mode == test_properties["phaseMode"]

    # if we have ct meters we should have CTMETERS feature and if no meters not
    assert envoy.ct_meter_count == len(envoy.ct_meter_list)
    assert envoy._supported_features
    has_ctmeters = bool(envoy._supported_features & SupportedFeatures.CTMETERS)
    meter_count_not_zero = bool(envoy.ct_meter_count > 0)
    assert has_ctmeters == meter_count_not_zero

    # test if expected meters were found
    for cttype in test_properties["meter_types"]:
        assert envoy.meter_type(cttype)
    # test for unexpected meters showing up
    for cttype in envoy.ct_meter_list:
        assert cttype in test_properties["meter_types"]

    # are all CT types represented correctly in model description
    for cttype in envoy.ct_meter_list:
        assert (cttype in envoy.envoy_model) != (envoy.meter_type(cttype) is None)

    # backward compatibility test, verify individual meter types are still found and in model

    # if no xxx meter is reported then xxx_meter_type should not report one and other way around
    # if no xxx meter is reported then it should not show in modelname and other way around
    has_meter = bool(
        (CtType.TOTAL_CONSUMPTION in envoy.ct_meter_list)
        | (CtType.NET_CONSUMPTION in envoy.ct_meter_list)
    )
    meter_type_present = bool(envoy.consumption_meter_type is not None)
    meter_in_model = bool(str(envoy.consumption_meter_type) in envoy.envoy_model)
    assert has_meter == meter_type_present
    assert has_meter == meter_in_model

    has_meter = bool(CtType.PRODUCTION in envoy.ct_meter_list)
    meter_type_present = bool(envoy.production_meter_type is not None)
    meter_in_model = bool(str(envoy.production_meter_type) in envoy.envoy_model)
    assert has_meter == meter_type_present
    assert has_meter == meter_in_model

    has_meter = bool(CtType.STORAGE in envoy.ct_meter_list)
    meter_type_present = bool(envoy.storage_meter_type is not None)
    meter_in_model = bool(str(envoy.storage_meter_type) in envoy.envoy_model)
    assert has_meter == meter_type_present
    assert has_meter == meter_in_model

    # end backward compatibility test

    # verify meter data
    meter_json = await load_json_fixture(version, "ivp_meters")
    meter_data_json = await load_json_fixture(version, "ivp_meters_readings")

    # get all enabled meters
    enabled_meters: list[Any] = jsonpath.findall("[?(@.state=='enabled')]", meter_json)
    # envoy should have same count
    assert envoy.ct_meter_count == len(enabled_meters)

    # validate each meter data
    for meter in enabled_meters:
        meters_data: list[Any] = jsonpath.findall(
            f"[?(@.eid=={meter['eid']})]", meter_data_json
        )
        assert meters_data[0]
        meter_data = meters_data[0]
        cttype = meter["measurementType"]
        ctdata = data.ctmeters[cttype]
        assert ctdata.energy_delivered == round(meter_data["actEnergyDlvd"])
        assert ctdata.energy_received == round(meter_data["actEnergyRcvd"])
        assert ctdata.active_power == round(meter_data["activePower"])
        assert ctdata.voltage == meter_data["voltage"]
        assert ctdata.current == meter_data["current"]
        assert ctdata.frequency == meter_data["freq"]
        assert ctdata.state == meter["state"]
        assert ctdata.metering_status == meter["meteringStatus"]
        assert ctdata.status_flags == meter["statusFlags"]

        # backward compatibility test
        # specific xxx meter data should match ctmeters[xxx] data
        meter_match = bool(cttype == CtType.PRODUCTION)
        data_match = bool(data.ctmeter_production == data.ctmeters[cttype])
        assert meter_match == data_match

        meter_match = bool(cttype in (CtType.NET_CONSUMPTION, CtType.TOTAL_CONSUMPTION))
        data_match = bool(data.ctmeter_consumption == data.ctmeters[cttype])
        assert meter_match == data_match

        meter_match = bool(cttype == CtType.STORAGE)
        data_match = bool(data.ctmeter_storage == data.ctmeters[cttype])
        assert meter_match == data_match
        # end backward compatibility test

        # test phase data, if phase count is <=1 no phase data should be present
        multiple_phases = bool(envoy.phase_count > 1)
        phase_data_len_equals_count = bool(
            len(data.ctmeters_phases.get(cttype, {})) == envoy.phase_count
        )
        assert multiple_phases == phase_data_len_equals_count
        for i in range(0, envoy.phase_count if envoy.phase_count > 1 else 0):
            phase_data: Any = jsonpath.findall(
                f"[?(@.eid=={meter['eid']})]['channels'][*]", meter_data_json
            )[i]
            assert data.ctmeters_phases[cttype].get(PHASENAMES[i]) is not None
            ctdata_phase = data.ctmeters_phases[cttype][PHASENAMES[i]]
            assert ctdata_phase.energy_delivered == round(phase_data["actEnergyDlvd"])
            assert ctdata_phase.energy_received == round(phase_data["actEnergyRcvd"])
            assert ctdata_phase.active_power == round(phase_data["activePower"])
            assert ctdata_phase.voltage == phase_data["voltage"]
            assert ctdata_phase.frequency == phase_data["freq"]
            assert ctdata_phase.state == meter["state"]
            assert ctdata_phase.metering_status == meter["meteringStatus"]
            assert ctdata_phase.status_flags == meter["statusFlags"]

            # backward compatibility, verify individual phase data matches dict data
            # specific xxx meter should match ctmeters_phases[xxx] data
            meter_match = bool(cttype == CtType.PRODUCTION)
            data_match = bool(
                data.ctmeter_production_phases == data.ctmeters_phases.get(cttype)
            )
            assert meter_match == data_match

            meter_match = bool(
                cttype in (CtType.NET_CONSUMPTION, CtType.TOTAL_CONSUMPTION)
            )
            data_match = bool(
                data.ctmeter_consumption_phases == data.ctmeters_phases.get(cttype)
            )
            assert meter_match == data_match

            meter_match = bool(cttype == CtType.STORAGE)
            data_match = bool(
                data.ctmeter_storage_phases == data.ctmeters_phases.get(cttype)
            )
            assert meter_match == data_match
            # end compatibility


@pytest.mark.parametrize(
    ("test_properties",),
    [
        pytest.param(
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "meter_types": [],
            },
            id="5.0.62",
        ),
        pytest.param(
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "meter_types": [],
            },
            id="7.3.130",
        ),
        pytest.param(
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "meter_types": [],
            },
            id="7.3.466_metered_disabled_cts",
        ),
        pytest.param(
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "meter_types": [],
            },
            id="7.3.517",
        ),
        pytest.param(
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "meter_types": [],
            },
            id="7.3.517_legacy_savings_mode",
        ),
        pytest.param(
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "meter_types": [],
            },
            id="7.6.114_without_cts",
        ),
        pytest.param(
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "meter_types": [],
            },
            id="7.6.175",
        ),
        pytest.param(
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "meter_types": [],
            },
            id="7.6.175_standard",
        ),
        pytest.param(
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "meter_types": [],
            },
            id="7.6.175_total",
        ),
        pytest.param(
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "meter_types": [],
            },
            id="8.1.41",
        ),
        pytest.param(
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "meter_types": [],
            },
            id="8.2.4264_metered_noct",
        ),
    ],
)
@pytest.mark.asyncio
async def test_without_current_transformers(
    snapshot: SnapshotAssertion,
    caplog: pytest.LogCaptureFixture,
    test_properties: dict[str, Any],
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    request: pytest.FixtureRequest,
) -> None:
    """Test Current transformer data when none are installed."""
    caplog.set_level(logging.WARNING)
    start_7_firmware_mock(mock_aioresponse)

    # verify test parameter completeness
    assert len(test_properties) == 4

    # get version and fixture folder from test id
    version: Any = request.node.callspec.id
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)

    # load data
    data = envoy.data
    assert data is not None
    assert data == snapshot

    # verify expected properties
    assert envoy.ct_meter_count == test_properties["ctMeters"]
    assert envoy.phase_count == test_properties["phaseCount"]
    assert envoy.phase_mode == test_properties["phaseMode"]

    # if we have ct meters we should have CTMETERS feature and not if no meters
    assert envoy.ct_meter_count == len(envoy.ct_meter_list)
    assert envoy._supported_features
    has_ctmeters = bool(envoy._supported_features & SupportedFeatures.CTMETERS)
    meter_count_not_zero = bool(envoy.ct_meter_count > 0)
    assert has_ctmeters == meter_count_not_zero

    # backward compatibility test, verify individual meter types are still found and in model

    # if no xxx meter is reported then xxx_meter_type should not report one and other way around
    # if no xxx meter is reported then it should not show in modelname and other way around
    has_meter = bool(
        (CtType.TOTAL_CONSUMPTION in envoy.ct_meter_list)
        | (CtType.NET_CONSUMPTION in envoy.ct_meter_list)
    )
    meter_type_present = bool(envoy.consumption_meter_type is not None)
    meter_in_model = bool(str(envoy.consumption_meter_type) in envoy.envoy_model)
    assert has_meter == meter_type_present
    assert has_meter == meter_in_model

    has_meter = bool(CtType.PRODUCTION in envoy.ct_meter_list)
    meter_type_present = bool(envoy.production_meter_type is not None)
    meter_in_model = bool(str(envoy.production_meter_type) in envoy.envoy_model)
    assert has_meter == meter_type_present
    assert has_meter == meter_in_model

    has_meter = bool(CtType.STORAGE in envoy.ct_meter_list)
    meter_type_present = bool(envoy.storage_meter_type is not None)
    meter_in_model = bool(str(envoy.storage_meter_type) in envoy.envoy_model)
    assert has_meter == meter_type_present
    assert has_meter == meter_in_model

    # end backward compatibility test
