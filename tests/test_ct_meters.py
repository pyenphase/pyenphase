"""Test envoy metered with enabled and disabled CT"""

import copy
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
    PhaseNames,
    SupportedFeatures,
)
from pyenphase.envoy import UPDATERS
from pyenphase.models.meters import (
    CtMeterData,
    CtType,
    EnvoyMeterData,
    EnvoyPhaseMode,
)
from pyenphase.models.system_consumption import EnvoySystemConsumption
from pyenphase.models.system_production import EnvoySystemProduction
from pyenphase.updaters.meters import (
    EnvoyMetersUpdater,
    _find_zero_phase_for_storage_anomaly,
)

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

    # Preserve the original updaters
    original_updaters = UPDATERS.copy()
    try:
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
        assert str(ct_data.eid) == "704643328"
        assert ct_data.measurement_type == "production"

        # test meters.from_phase method
        ct_phase_data: EnvoyMeterData | None = EnvoyMeterData.from_phase(
            meters_readings[0], meter_status, 0
        )
        assert ct_phase_data is not None
        assert str(ct_phase_data.eid) == "1778385169"
        assert ct_phase_data.measurement_type == "production"
        assert ct_phase_data.energy_delivered == 3183794

        assert (
            envoy.envoy_model
            == "Envoy, phases: 3, phase mode: three, production CT, net-consumption CT"
        )

        # test exception handling by specifying non-existing phase
        ct_no_phase_data = EnvoyMeterData.from_phase(
            meters_readings[0], meter_status, 3
        )
        assert ct_no_phase_data is None

        # test exception handling for missing phase data, remove phase data from mock data
        del meters_readings[0]["channels"]
        ct_no_phase_data = EnvoyMeterData.from_phase(
            meters_readings[0], meter_status, 0
        )
        assert ct_no_phase_data is None

        # test exception handling for phase data in production using wrong phase
        production_data = data.raw["/production.json?details=1"]
        production_no_phase_data = EnvoySystemProduction.from_production_phase(
            production_data, 3, True
        )
        assert production_no_phase_data is None

        # test exception handling for phase data if key is missing
        del production_data["production"][1]["type"]
        with pytest.raises(ValueError):
            EnvoySystemProduction.from_production_phase(production_data, 0, True)

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
    finally:
        # Restore the original updaters
        UPDATERS.clear()
        for updater in original_updaters:
            register_updater(updater)


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

    # Preserve the original updaters
    original_updaters = UPDATERS.copy()
    try:
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
        assert str(ct_data.eid) == "704643328"
        assert ct_data.measurement_type == "production"

        # test meters.from_phase method
        ct_phase_data: EnvoyMeterData | None = EnvoyMeterData.from_phase(
            meters_readings[0], meter_status, 0
        )
        assert ct_phase_data is not None
        assert str(ct_phase_data.eid) == "1778385169"
        assert ct_phase_data.measurement_type == "production"
        assert ct_phase_data.energy_delivered == 3183794

        assert (
            envoy.envoy_model
            == "Envoy, phases: 3, phase mode: three, production CT, net-consumption CT"
        )

        # test exception handling by specifying non-existing phase
        ct_no_phase_data = EnvoyMeterData.from_phase(
            meters_readings[0], meter_status, 3
        )
        assert ct_no_phase_data is None

        # test exception handling for missing phase data, remove phase data from mock data
        del meters_readings[0]["channels"]
        ct_no_phase_data = EnvoyMeterData.from_phase(
            meters_readings[0], meter_status, 0
        )
        assert ct_no_phase_data is None

        # test exception handling for phase data if key is missing
        production_data = data.raw["/production.json?details=1"]
        del production_data["production"][1]["type"]
        with pytest.raises(ValueError):
            EnvoySystemProduction.from_production_phase(production_data, 0, True)
    finally:
        # Restore the original updaters
        UPDATERS.clear()
        for updater in original_updaters:
            register_updater(updater)


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
    ivp_meters = (await load_fixture(version, "ivp_meters")).replace(
        CtType.NET_CONSUMPTION, CtType.TOTAL_CONSUMPTION
    )
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters",
        status=200,
        body=ivp_meters,
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
    assert str(ct_data.eid) == "704643840"
    assert ct_data.measurement_type == "storage"

    # test meters.from_phase method
    ct_phase_data: EnvoyMeterData | None = EnvoyMeterData.from_phase(
        meters_readings[2], meter_status, 0
    )
    assert ct_phase_data is not None
    assert str(ct_phase_data.eid) == "1778385681"
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
    yet_unknown_ct = data.ctmeters[yet_unknown_ct_type]
    assert yet_unknown_ct
    assert yet_unknown_ct.state == meter["state"]
    assert yet_unknown_ct.eid == meter["eid"]
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
        assert (cttype in envoy.envoy_model) == (envoy.meter_type(cttype) is not None)

    # backward compatibility test, verify individual meter types are still found and in model

    # if no xxx meter is reported then xxx_meter_type should not report one and other way around
    # if no xxx meter is reported then it should not show in modelname and other way around
    has_meter = bool(
        (CtType.TOTAL_CONSUMPTION in envoy.ct_meter_list)
        or (CtType.NET_CONSUMPTION in envoy.ct_meter_list)
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
        assert ctdata
        assert ctdata.energy_delivered == round(meter_data["actEnergyDlvd"])
        assert ctdata.energy_received == round(meter_data["actEnergyRcvd"])
        assert ctdata.active_power == round(meter_data["activePower"])
        assert ctdata.voltage == meter_data["voltage"]
        assert ctdata.current == meter_data["current"]
        assert ctdata.frequency == meter_data["freq"]
        assert ctdata.state == meter["state"]
        assert ctdata.metering_status == meter["meteringStatus"]
        assert ctdata.status_flags == meter.get("statusFlags")

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
            assert ctdata_phase
            assert ctdata_phase.energy_delivered == round(phase_data["actEnergyDlvd"])
            assert ctdata_phase.energy_received == round(phase_data["actEnergyRcvd"])
            assert ctdata_phase.active_power == round(phase_data["activePower"])
            assert ctdata_phase.voltage == phase_data["voltage"]
            assert ctdata_phase.frequency == phase_data["freq"]
            assert ctdata_phase.state == meter["state"]
            assert ctdata_phase.metering_status == meter["meteringStatus"]
            assert ctdata_phase.status_flags == meter.get("statusFlags")

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
        or (CtType.NET_CONSUMPTION in envoy.ct_meter_list)
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


@pytest.mark.asyncio
async def test_intermittent_activeCount(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Test envoy metered with ct reporting intermitted activeCount 0 in /production.

    As of fw 5.3.5528 (and maybe earlier) metered envoy with CT intermittently
    report bogus data in /production type=eim, recognizable by activeCount: 0.
    A silent fallback from production to inverters data of /production happens
    because activecount (and potentially other values as well) being 0. The
    inverter segment data for this and others firmwares has different values
    as the eim segment and would result in step changes in the value.

    The inverter segment data has different values as the eim segment and would
    result in step changes in the value. Test there's no fallback to the inverters
    section for metered with production ct. Test return of None instead of faulty data
    if activeCount 0 is received in the midst of normal operation.
    """
    # pick a version with CT's enabled, we'll patch the data for testing
    # there's no FW version guard in the code, so any will do
    version = "7.6.175_with_cts_3phase"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

    # production and consumption data to be provided by the EnvoyProductionJsonUpdater
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
        "EnvoyMetersUpdater": SupportedFeatures.CTMETERS | SupportedFeatures.THREEPHASE,
        "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
    }
    assert (
        envoy.envoy_model
        == "Envoy, phases: 3, phase mode: three, production CT, net-consumption CT"
    )

    # With CT active /production data should be from type=eim and not from type=inverters
    assert data.system_production is not None
    assert data.system_production.watts_now == -6
    assert data.system_production.watt_hours_today == 5113
    assert data.system_production.watt_hours_last_7_days == 69492
    assert data.system_production.watt_hours_lifetime == 4351113

    # No fallback for phase data, verify if present and not None
    assert data.system_production_phases is not None
    assert len(data.system_production_phases) == 3
    for phase in PHASENAMES:
        assert data.system_production_phases[phase] is not None

    # Test intermittent activeCount = 0 case during regular operation
    production_json = await load_json_fixture(version, "production.json")
    production_json["production"][1]["activeCount"] = 0
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
    await envoy.update()

    # if activeCount is 0 and Production CT present, None should return for production data
    data = envoy.data
    assert data
    assert data.system_production is None
    assert data.system_production_phases is None


@pytest.mark.asyncio
async def test_intermittent_activeCount_at_probe(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Test envoy metered with ct and intermitted activeCount 0 in /production not
    falling back to type=inverters when activeCount is zero at probe.

    As of fw 5.3.5528 (and maybe earlier) metered envoy with CT intermittently
    report bogus data in /production type=eim, recognizable by activeCount: 0.
    A silent fallback from production to inverters data of /production happens
    because activecount (and potentially other values as well) being 0. The
    inverter segment data for this and others firmwares has different values
    as the eim segment and would result in step changes in the value.

    The inverter segment data has different values as the eim segment and would
    result in step changes in the value. Test there's no fallback to the inverters
    section for metered with ct at probe and data is restored when activeCount is
    non-zero again during update.
    """
    # pick a version with CT's enabled, we'll patch the data for testing
    # there's no FW version guard in the code, so any will do
    version = "7.6.175_with_cts_3phase"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # Test intermittent activeCount = 0 case during probe and update
    production_json = await load_json_fixture(version, "production.json")
    production_json["production"][1]["activeCount"] = 0
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

    envoy = await get_mock_envoy(test_client_session)

    data = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

    # production and consumption data to be provided by the EnvoyProductionJsonUpdater
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
        "EnvoyMetersUpdater": SupportedFeatures.CTMETERS | SupportedFeatures.THREEPHASE,
        "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
    }

    # if activeCount is 0 and Production CT present, None should return for production data
    assert data.system_production is None
    assert data.system_production_phases is None

    # test update of envoy with activeCount back to 1. Should restore production data
    production_json["production"][1]["activeCount"] = 1
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
    await envoy.update()
    data = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

    # With CT active /production data should be from type=eim and not from type=inverters
    assert data.system_production is not None
    assert data.system_production.watts_now == -6
    assert data.system_production.watt_hours_today == 5113
    assert data.system_production.watt_hours_last_7_days == 69492
    assert data.system_production.watt_hours_lifetime == 4351113

    # Verify phase data is available again
    assert data.system_production_phases is not None
    assert len(data.system_production_phases) == 3
    for phase in data.system_production_phases:
        assert data.system_production_phases[phase] is not None


@pytest.mark.asyncio
async def test_intermittent_activecount_regression_total_is_net_consumption(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Test envoy metered with ct and intermitted activeCount 0 in /production not
    falling back to type=inverters when activeCount becomes zero during update
    and the earlier fix for total_consumption = net_consumption remains active
    """
    # pick a version beyond fw guard of total_is_net_consumption issue
    version = "8.3.5433_tot_is_net_cons"

    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)

    data = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

    # production and consumption data to be provided by the EnvoyProductionJsonUpdater
    assert envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION
    assert envoy._supported_features & SupportedFeatures.NET_CONSUMPTION
    assert envoy._supported_features & SupportedFeatures.PRODUCTION
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert envoy._supported_features & SupportedFeatures.METERING
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert envoy._supported_features & SupportedFeatures.CTMETERS
    assert updater_features(envoy._updaters) == {
        "EnvoyDeviceDataInvertersUpdater": SupportedFeatures.INVERTERS
        | SupportedFeatures.DETAILED_INVERTERS,
        "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
        | SupportedFeatures.TOTAL_CONSUMPTION
        | SupportedFeatures.NET_CONSUMPTION
        | SupportedFeatures.PRODUCTION,
        "EnvoyMetersUpdater": SupportedFeatures.CTMETERS | SupportedFeatures.DUALPHASE,
        "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
    }
    assert (
        envoy.envoy_model
        == "Envoy, phases: 2, phase mode: split, production CT, total-consumption CT"
    )

    # With CT active /production data should be from type=eim and not from type=inverters
    assert data.system_production is not None
    assert data.system_production_phases is not None
    assert data.system_production.watts_now == 357
    assert data.system_production.watt_hours_today == 14405465
    assert data.system_production.watt_hours_last_7_days == 14405465
    assert data.system_production.watt_hours_lifetime == 14405465

    # consumption data should be corrected for total=net consumption issue
    assert data.system_consumption is not None
    assert data.system_consumption.watts_now == 428 + 357
    assert data.system_consumption.watt_hours_today == 5649402
    assert data.system_consumption.watt_hours_last_7_days == 5649402
    assert data.system_consumption.watt_hours_lifetime == 5649402 + 14405465

    # Test intermittent activeCount = 0 case during regular operation
    production_json = await load_json_fixture(version, "production.json")
    production_json["production"][1]["activeCount"] = 0
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

    await envoy.update()

    data = envoy.data
    assert data is not None

    # if activeCount is 0 and Production CT present, None should return for production data
    assert data.system_production is None
    assert data.system_production_phases is None

    # consumption data should be none as we have no reliable production values to use for correction
    assert data.system_consumption is None
    assert data.system_consumption_phases is None

    # test restore activeCount back to 1. Should restore production and consumption data
    production_json["production"][1]["activeCount"] = 1
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
    await envoy.update()
    data = envoy.data
    assert data is not None

    # With CT active /production data should be from type=eim and not from type=inverters
    assert data.system_production is not None
    assert data.system_production_phases is not None
    assert data.system_production.watts_now == 357
    assert data.system_production.watt_hours_today == 14405465
    assert data.system_production.watt_hours_last_7_days == 14405465
    assert data.system_production.watt_hours_lifetime == 14405465

    # consumption data should be corrected for total=net consumption issue
    assert data.system_consumption is not None
    assert data.system_consumption.watts_now == 428 + 357
    assert data.system_consumption.watt_hours_today == 5649402
    assert data.system_consumption.watt_hours_last_7_days == 5649402
    assert data.system_consumption.watt_hours_lifetime == 5649402 + 14405465


@pytest.mark.asyncio
async def test_intermittent_activeCount_without_production_ct(
    mock_aioresponse: aioresponses, test_client_session: aiohttp.ClientSession
) -> None:
    """
    Test envoy metered with ct but no production ct and intermitted activeCount 0
    in /production not falling back to type=inverters when activeCount is zero

    As of fw 5.3.5528 (and maybe earlier) metered envoy with CT intermittently
    report bogus data in /production type=eim, recognizable by activeCount: 0.
    A silent fallback from production to inverters data of /production happens
    because activecount (and potentially other values as well) being 0. The
    inverter segment data for this and others firmwares has different values
    as the eim segment and would result in step changes in the value.

    Without an enabled production CT the previous behavior must remain: the
    values are taken from a mix of the inverters and eim sections when
    activeCount is zero during update.

    Note that this test case is somewhat artifcial. No reports are available for
    metered Envoy installations with just a consumption CT and no Production CT.
    We have no definive information which data to use for such a case.
    """
    # pick a version with CT's enabled, we'll patch the data for testing
    # there's no FW version guard in the code, so any will do
    version = "7.6.175_with_cts_3phase"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # patch meters so production CT is not active
    meters_json = await load_json_list_fixture(version, "ivp_meters")
    meters_json[0]["state"] = "disabled"
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters",
        status=200,
        payload=meters_json,
        repeat=True,
    )

    envoy = await get_mock_envoy(test_client_session)

    data = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

    # production and consumption data to be provided by the EnvoyProductionJsonUpdater
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
        "EnvoyMetersUpdater": SupportedFeatures.CTMETERS | SupportedFeatures.THREEPHASE,
        "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
    }
    assert (
        envoy.envoy_model == "Envoy, phases: 3, phase mode: three, net-consumption CT"
    )

    # data assumed be from type=eim and not from type=inverters
    # we have no real world example of this, it might
    # very well be data has to come from inverters segment
    # for now, this is consistent with previous library versions
    assert data.system_production is not None
    assert data.system_production_phases is not None
    assert data.system_production.watts_now == -6
    assert data.system_production.watt_hours_today == 5113
    assert data.system_production.watt_hours_last_7_days == 69492
    assert data.system_production.watt_hours_lifetime == 4351113

    assert data.system_production_phases is not None
    assert len(data.system_production_phases) == 3
    for phase in data.system_production_phases:
        assert data.system_production_phases[phase] is not None

    # Test intermittent activeCount = 0 case during regular operation
    production_json = await load_json_fixture(version, "production.json")
    production_json["production"][1]["activeCount"] = 0
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

    await envoy.update()
    data = envoy.data
    assert data is not None

    # data is now mixed from inverters and production section.
    # watts_now and watt_hours_lifetime is from inverters
    # other two from production section but are bogus anyway
    # No production CT and activeCount = 0 is the old metered no ct case
    assert data.system_production is not None
    assert data.system_production.watts_now == 0
    assert data.system_production.watt_hours_today == 5113
    assert data.system_production.watt_hours_last_7_days == 69492
    assert data.system_production.watt_hours_lifetime == 4339764

    assert data.system_production_phases is not None
    assert len(data.system_production_phases) == 3
    for phase in data.system_production_phases:
        assert data.system_production_phases[phase] is not None

    # Test intermittent activeCount = 0 case during probe and update
    envoy = await get_mock_envoy(test_client_session)

    data = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

    # production data now falls back to EnvoyProductionUpdater
    # remember this is not a known real world installation
    # library has always fallen back to EnvoyProductionUpdater
    # and its not clear what this data is worth. Just verifying
    # consistency to previous behavior, but NOne may be better case
    assert envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION
    assert envoy._supported_features & SupportedFeatures.NET_CONSUMPTION
    assert envoy._supported_features & SupportedFeatures.PRODUCTION
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert envoy._supported_features & SupportedFeatures.METERING
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert envoy._supported_features & SupportedFeatures.CTMETERS
    assert updater_features(envoy._updaters) == {
        "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
        "EnvoyProductionUpdater": SupportedFeatures.METERING
        | SupportedFeatures.PRODUCTION,
        "EnvoyProductionJsonUpdater": SupportedFeatures.TOTAL_CONSUMPTION
        | SupportedFeatures.NET_CONSUMPTION,
        "EnvoyMetersUpdater": SupportedFeatures.CTMETERS | SupportedFeatures.THREEPHASE,
        "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
    }

    assert (
        envoy.envoy_model == "Envoy, phases: 3, phase mode: three, net-consumption CT"
    )
    # data assumed be from type=eim and not from type=inverters
    # if is an actual real-world case it be might better return None
    assert data.system_production is not None
    assert data.system_production.watts_now == -6
    assert data.system_production.watt_hours_today == 5113
    assert data.system_production.watt_hours_last_7_days == 69492
    assert data.system_production.watt_hours_lifetime == 4351113


@pytest.mark.parametrize(
    (
        "version",  # firmware version pyenphase gets passed
        "aggregate_data",  # aggregate storage CT values to expect for active_power, energy_received and energy_delivered
        "phase_l1_data",  # L1 phase storage CT values to expect
        "phase_l2_data",  # L2 phase storage CT values to expect
        "block_zero",  # firmware will detect zero values and return None for aggregate and phase
    ),
    [
        (
            "8.3.6087_storage_ct_drops",
            {
                "active_power": 0,
                "energy_received": 2425361,
                "energy_delivered": 343300,
            },
            {
                "active_power": 0,
                "energy_received": 1212681,
                "energy_delivered": 171650,
            },
            {
                "active_power": 0,
                "energy_received": 1212681,
                "energy_delivered": 171650,
            },
            True,
        ),
        (
            "8.2.4286_with_3cts_and_battery_split",
            {
                "active_power": -7084,
                "energy_received": 5409935,
                "energy_delivered": 4073871,
            },
            {
                "active_power": -3538,
                "energy_received": 2703734,
                "energy_delivered": 2036140,
            },
            {
                "active_power": -3545,
                "energy_received": 2706201,
                "energy_delivered": 2037731,
            },
            False,
        ),
    ],
    ids=[
        "8.3.6087",
        "8.2.4286",
    ],
)
@pytest.mark.asyncio
async def test_intermittent_zero_storageCT_Phase_asof_8_3_6087(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    aggregate_data: dict[str, Any],
    phase_l1_data: dict[str, Any],
    phase_l2_data: dict[str, Any],
    block_zero: bool,
) -> None:
    """
    Test envoy metered with storage ct and intermitted 1 phase zero values.

    Envoy firmware D8.3.6087, /ivp/meters/readings for split, 2 phase storage CT
    intermittently reports zero values on one phase. Aggregated data then
    drops to the other phase values resulting in incorrect storage data.
    Test meters updates return None in the storage CT and storage CT L1 Phase data
    if this scenario applies.
    """
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

    # Verify storage CT data is present
    assert envoy._supported_features & SupportedFeatures.CTMETERS
    assert envoy.meter_type(CtType.STORAGE) == CtType.STORAGE
    assert data.ctmeters is not None
    assert (agg_data := data.ctmeters[CtType.STORAGE]) is not None
    assert data.ctmeters_phases is not None

    # Test without phase data zero issue
    assert agg_data.active_power == aggregate_data["active_power"]
    assert agg_data.energy_received == aggregate_data["energy_received"]
    assert agg_data.energy_delivered == aggregate_data["energy_delivered"]
    assert (
        l1_data := data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_1]
    ) is not None
    assert l1_data.active_power == phase_l1_data["active_power"]
    assert l1_data.energy_received == phase_l1_data["energy_received"]
    assert l1_data.energy_delivered == phase_l1_data["energy_delivered"]
    assert (
        l2_data := data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_2]
    ) is not None
    assert l2_data.active_power == phase_l2_data["active_power"]
    assert l2_data.energy_received == phase_l2_data["energy_received"]
    assert l2_data.energy_delivered == phase_l2_data["energy_delivered"]

    # start backward compatibility test
    assert data.ctmeter_storage is data.ctmeters[CtType.STORAGE]
    assert data.ctmeter_storage_phases is data.ctmeters_phases[CtType.STORAGE]
    # end backward compatibility test

    # Test storagect intermittent one phase zero anomaly detection function
    # operational data without zero phase, should return None
    assert data is not None
    result = _find_zero_phase_for_storage_anomaly(data)
    assert result is None

    # no aggregate data for storage, should get None
    save_agg_data = copy.deepcopy(data.ctmeters[CtType.STORAGE])
    data.ctmeters[CtType.STORAGE] = None
    result = _find_zero_phase_for_storage_anomaly(data)
    assert result is None
    data.ctmeters[CtType.STORAGE] = save_agg_data

    # no phase data for storage, should get None
    phase_data = copy.deepcopy(data.ctmeters_phases[CtType.STORAGE])
    del data.ctmeters_phases[CtType.STORAGE]
    result = _find_zero_phase_for_storage_anomaly(data)
    assert result is None
    data.ctmeters_phases[CtType.STORAGE] = phase_data

    # only phase 1 to none, should get None
    phase1_data = copy.deepcopy(
        data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_1]
    )
    data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_1] = None
    result = _find_zero_phase_for_storage_anomaly(data)
    assert result is None
    data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_1] = phase1_data

    # only phase 2 to none, should get None
    phase2_data = copy.deepcopy(
        data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_2]
    )
    data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_2] = None
    result = _find_zero_phase_for_storage_anomaly(data)
    assert result is None
    data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_2] = phase2_data

    # one phase zero but aggregate is not equal to non-zero phase, should get None
    assert data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_2] is not None
    data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_2].active_power = 0  # type: ignore[union-attr]
    data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_2].energy_delivered = 0  # type: ignore[union-attr]
    data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_2].energy_received = 0  # type: ignore[union-attr]

    result = _find_zero_phase_for_storage_anomaly(data)
    assert result is None

    # set aggregate data equal to non-zero phase, should get zero phase 2 reported
    p1_data = data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_1]
    data.ctmeters[CtType.STORAGE].active_power = p1_data.active_power  # type: ignore[union-attr]
    data.ctmeters[CtType.STORAGE].energy_delivered = p1_data.energy_delivered  # type: ignore[union-attr]
    data.ctmeters[CtType.STORAGE].energy_received = p1_data.energy_received  # type: ignore[union-attr]

    result = _find_zero_phase_for_storage_anomaly(data)
    assert result == PhaseNames.PHASE_2

    # both phases to zero, but aggregate not, should get None
    data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_1].active_power = 0  # type: ignore[union-attr]
    data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_1].energy_delivered = 0  # type: ignore[union-attr]
    data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_1].energy_received = 0  # type: ignore[union-attr]

    result = _find_zero_phase_for_storage_anomaly(data)
    assert result is None

    # both phases and aggregate to zero,all zero, should get None
    data.ctmeters[CtType.STORAGE].active_power = 0  # type: ignore[union-attr]
    data.ctmeters[CtType.STORAGE].energy_delivered = 0  # type: ignore[union-attr]
    data.ctmeters[CtType.STORAGE].energy_received = 0  # type: ignore[union-attr]

    result = _find_zero_phase_for_storage_anomaly(data)
    assert result is None

    # For D8.3.6087, /ivp/meters/readings started intermittently reporting incorrect storage
    # CT lifetime energy values on split-phase system.  One storage channel reports all
    # zeros and the aggregate value becomes equal to the remaining non-zero channel.

    # test with zero l1 channel and aggregate equal to L2 data
    # for D8.3.6087 and newer, should have None for aggregate and L1.
    # For older fw aggregate has L2 values and L1 zeros.

    meter_data_json = await load_json_list_fixture(version, "ivp_meters_readings")
    items = [
        item
        for item in meter_data_json[2]["channels"][1]
        if item not in ("eid", "timestamp")
    ]
    for item in items:
        # patch 3th entry which is the storage CT, first phase value to zero
        meter_data_json[2]["channels"][0][item] = 0
        # patch aggregate values of storage CT to second phase values
        meter_data_json[2][item] = meter_data_json[2]["channels"][1][item]

    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters/readings",
        status=200,
        payload=meter_data_json,
        repeat=True,
    )
    await envoy.update()
    data = envoy.data

    # block_zero true is signal to expect Aggregate and L1 data not be reported
    # L2 regular if applicable.
    # If False expect zero in L1 and Aggretae == L2
    assert data
    assert data.ctmeters is not None
    assert data.ctmeters_phases is not None
    # Storage data should have been set to None if fw is eligible for correction
    assert (data.ctmeters[CtType.STORAGE] is None) == block_zero
    # Storage CT L1 phase should have been set to None if fw is eligible for correction
    # otherwise l1 phase data should have zeros set in the test
    zeroed_l1 = data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_1]
    assert (zeroed_l1 is None) == block_zero
    if not block_zero:
        assert zeroed_l1 is not None
        assert zeroed_l1.active_power == 0
        assert zeroed_l1.energy_delivered == 0
        assert zeroed_l1.energy_received == 0

    # In this test Storage CT L2 data should be returned as usual
    assert (
        l2_data := data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_2]
    ) is not None
    assert l2_data.active_power == phase_l2_data["active_power"]
    assert l2_data.energy_received == phase_l2_data["energy_received"]
    assert l2_data.energy_delivered == phase_l2_data["energy_delivered"]

    # start backward compatibility test
    assert data.ctmeter_storage is data.ctmeters[CtType.STORAGE]
    assert data.ctmeter_storage_phases is data.ctmeters_phases[CtType.STORAGE]
    # end backward compatibility test

    # same test for other phase being 0
    meter_data_json = await load_json_list_fixture(version, "ivp_meters_readings")
    items = [
        item
        for item in meter_data_json[2]["channels"][1]
        if item not in ("eid", "timestamp")
    ]
    for item in items:
        # patch 3th entry which is the storage CT, second phase value to zero
        meter_data_json[2]["channels"][1][item] = 0
        # patch aggregate values of storage CT to second phase values
        meter_data_json[2][item] = meter_data_json[2]["channels"][0][item]

    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters/readings",
        status=200,
        payload=meter_data_json,
        repeat=True,
    )
    await envoy.update()
    data = envoy.data

    # Aggregate and L2 data should be None, L1 regular if applicable
    assert data
    assert data.ctmeters is not None
    # Storage data should have been set to None if fw is eligible for correction
    assert (data.ctmeters[CtType.STORAGE] is None) == block_zero

    # In this test Storage CT L1 data should be returned as usual
    assert data.ctmeters_phases is not None
    assert (
        l1_data := data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_1]
    ) is not None
    assert l1_data.active_power == phase_l1_data["active_power"]
    assert l1_data.energy_received == phase_l1_data["energy_received"]
    assert l1_data.energy_delivered == phase_l1_data["energy_delivered"]

    # Storage CT L2 phase should have been set to None if fw is eligible for correction
    # otherwise l2 phase data should show zeros set in the test
    zeroed_l2 = data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_2]
    assert (zeroed_l2 is None) == block_zero
    if not block_zero:
        assert zeroed_l2 is not None
        assert zeroed_l2.active_power == 0
        assert zeroed_l2.energy_received == 0
        assert zeroed_l2.energy_delivered == 0

    # start backward compatibility test
    assert data.ctmeter_storage is data.ctmeters[CtType.STORAGE]
    assert data.ctmeter_storage_phases is data.ctmeters_phases[CtType.STORAGE]
    # end backward compatibility test

    # Test with issue at probe time
    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data

    # Verify storage CT data is present
    assert envoy._supported_features is not None
    assert envoy._supported_features & SupportedFeatures.CTMETERS
    assert envoy.meter_type(CtType.STORAGE) == CtType.STORAGE

    # Aggregate and L2 data should be None, L1 regular if applicable
    assert data
    assert data.ctmeters is not None
    # Storage data should have been set to None if fw is eligible for correction
    assert (data.ctmeters[CtType.STORAGE] is None) == block_zero

    # In this test Storage CT L1 data should be returned as usual
    assert data.ctmeters_phases is not None
    assert (
        l1_data := data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_1]
    ) is not None
    assert l1_data.active_power == phase_l1_data["active_power"]
    assert l1_data.energy_received == phase_l1_data["energy_received"]
    assert l1_data.energy_delivered == phase_l1_data["energy_delivered"]

    # Storage CT L2 phase should have been set to None if fw is eligible for correction
    # otherwise l2 phase data should show zeros set in the test
    zeroed_l2 = data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_2]
    assert (zeroed_l2 is None) == block_zero
    if not block_zero:
        assert zeroed_l2 is not None
        assert zeroed_l2.active_power == 0
        assert zeroed_l2.energy_received == 0
        assert zeroed_l2.energy_delivered == 0

    # start backward compatibility test
    assert data.ctmeter_storage is data.ctmeters[CtType.STORAGE]
    assert data.ctmeter_storage_phases is data.ctmeters_phases[CtType.STORAGE]
    # end backward compatibility test

    # restore zero L2 and aggregate to original values
    meter_data_json = await load_json_list_fixture(version, "ivp_meters_readings")
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/ivp/meters/readings",
        status=200,
        payload=meter_data_json,
        repeat=True,
    )
    await envoy.update()
    data = envoy.data

    assert data is not None
    assert data.ctmeters is not None
    assert (agg_data := data.ctmeters[CtType.STORAGE]) is not None
    assert agg_data is not None
    assert data.ctmeters_phases is not None

    # All data should be available again
    assert agg_data.active_power == aggregate_data["active_power"]
    assert agg_data.energy_received == aggregate_data["energy_received"]
    assert agg_data.energy_delivered == aggregate_data["energy_delivered"]
    assert (
        l1_data := data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_1]
    ) is not None
    assert l1_data.active_power == phase_l1_data["active_power"]
    assert l1_data.energy_received == phase_l1_data["energy_received"]
    assert l1_data.energy_delivered == phase_l1_data["energy_delivered"]
    assert (
        l2_data := data.ctmeters_phases[CtType.STORAGE][PhaseNames.PHASE_2]
    ) is not None
    assert l2_data.active_power == phase_l2_data["active_power"]
    assert l2_data.energy_received == phase_l2_data["energy_received"]
    assert l2_data.energy_delivered == phase_l2_data["energy_delivered"]

    # start backward compatibility test
    assert data.ctmeter_storage is data.ctmeters[CtType.STORAGE]
    assert data.ctmeter_storage_phases is data.ctmeters_phases[CtType.STORAGE]
    # end backward compatibility test
