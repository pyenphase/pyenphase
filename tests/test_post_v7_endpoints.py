"""Test specific envoy firmware issues post v7."""

import logging
from typing import Any

import aiohttp
import pytest
from aioresponses import aioresponses

from pyenphase.const import URL_DEVICE_DATA, PhaseNames
from pyenphase.envoy import UPDATERS, Envoy, SupportedFeatures, register_updater
from pyenphase.exceptions import EnvoyAuthenticationRequired
from pyenphase.updaters.api_v1_production_inverters import (
    EnvoyApiV1ProductionInvertersUpdater,
)
from pyenphase.updaters.device_data_inverters import (
    RESIGNAL_INTERVAL,
    EnvoyDeviceDataInvertersUpdater,
)

from .common import (
    endpoint_path,
    get_mock_envoy,
    load_json_fixture,
    override_mock,
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
        (
            "8.3.5422_standard-no-eim",
            "800-00656-r06",
            {
                "EnvoyDeviceDataInvertersUpdater": SupportedFeatures.INVERTERS
                | SupportedFeatures.DETAILED_INVERTERS,
                "EnvoyProductionJsonFallbackUpdater": SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
            51,
            0,
            0,
            651725,
        ),
    ],
    ids=[
        "8.2.4264_metered_noct",
        "7.6.114_without_cts",
        "7.3.466_metered_disabled_cts",
        "8.3.5422_standard-no-eim",
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


@pytest.mark.parametrize(
    ("version", "inverter_count", "device_to_test"),
    [
        (
            "8.2.4345_with_device_data",
            15,
            "553648384",
        ),
        (
            "8.3.5289_modGone",
            12,
            "553649152",
        ),
    ],
    ids=[
        "8.2.4345_with_device_data",
        "8.3.5289_modGone",
    ],
)
@pytest.mark.asyncio
async def test_removed_inverter_devices(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    inverter_count: int,
    device_to_test: str,
) -> None:
    """Test removed inverters in device data still allow use of device data and set SupportedFeatures.DETAILED_INVERTERS"""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None

    # verify found inverter count
    assert len(data.inverters) == inverter_count
    # we should use DETAILED_INVERTERS data
    assert envoy.supported_features & SupportedFeatures.DETAILED_INVERTERS

    # verify data of device ended up in sn entry
    payload = await load_json_fixture(version, "ivp_pdm_device_data")
    sn = payload[device_to_test]["sn"]
    assert sn in data.inverters


@pytest.mark.parametrize(
    ("version", "inverter_count", "device_to_test"),
    [
        (
            "8.2.4345_with_device_data",
            15,
            "553648384",
        ),
        (
            "8.3.5289_modGone",
            12,
            "553649152",
        ),
    ],
    ids=[
        "8.2.4345_with_device_data",
        "8.3.5289_modGone",
    ],
)
@pytest.mark.asyncio
async def test_incomplete_inverter_devices_data(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    caplog: pytest.LogCaptureFixture,
    inverter_count: int,
    device_to_test: str,
) -> None:
    """Test handling of missing inverter data fields in device data"""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None

    # verify found inverter count
    assert len(data.inverters) == inverter_count

    # verify data of device ended up in sn entry
    payload = await load_json_fixture(version, "ivp_pdm_device_data")
    sn = payload[device_to_test]["sn"]
    assert sn in data.inverters

    # verify inverters with missing required keys at update
    # note that in each step we delete higher level data or
    # keys tested earlier in the code so we don't need to
    # reload the fixture file. If that changes reload may be needed

    caplog.clear()

    # without watts now we should not have device_to_test sn in inverters result
    # first warning of lost inverter data should be present
    del payload[device_to_test]["channels"][0]["watts"]["now"]
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters
    assert sn not in data.inverters
    assert len(data.inverters) == inverter_count - 1
    assert (
        f"Envoy returned incomplete inverter data, no data reported for: {sn}"
        in caplog.text
    )
    assert "Envoy returned complete inverter data for:" not in caplog.text
    caplog.clear()

    # without lastReadings endDate we should not have device_to_test sn in inverters result
    # no warning as that is suppressed after previous test
    del payload[device_to_test]["channels"][0]["lastReading"]["endDate"]
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters
    assert sn not in data.inverters
    assert len(data.inverters) == inverter_count - 1
    assert (
        "Envoy returned incomplete inverter data, no data reported for:"
        not in caplog.text
    )
    assert "Envoy returned complete inverter data for:" not in caplog.text
    caplog.clear()

    # without lastReadings we should not have device_to_test sn in inverters result
    # no warning as that is suppressed after previous test
    del payload[device_to_test]["channels"][0]["lastReading"]
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters
    assert sn not in data.inverters
    assert len(data.inverters) == inverter_count - 1
    assert (
        "Envoy returned incomplete inverter data, no data reported for:"
        not in caplog.text
    )
    assert "Envoy returned complete inverter data for:" not in caplog.text
    caplog.clear()

    # without channel[0] (there's only one) we should not have device_to_test sn in inverters result
    # no warning as that is suppressed after previous test
    del payload[device_to_test]["channels"][0]
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters
    assert sn not in data.inverters
    assert len(data.inverters) == inverter_count - 1
    assert (
        "Envoy returned incomplete inverter data, no data reported for:"
        not in caplog.text
    )
    assert "Envoy returned complete inverter data for:" not in caplog.text
    caplog.clear()

    # without serialnumber we should not have inverter data at all
    # debug log for incomplete data
    del payload[device_to_test]["sn"]
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters == {}
    assert (
        "Invalid device data detected: 'sn', skipping inverter data extraction"
        in caplog.text
    )
    assert (
        "Envoy returned incomplete inverter data, no data reported for:"
        not in caplog.text
    )
    assert "Envoy returned complete inverter data for:" not in caplog.text
    caplog.clear()

    # without any data we should get repeated warning after previous test but for devName
    empty_payload: dict[str, Any] = {device_to_test: {}}
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=empty_payload,
    )
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters == {}
    assert (
        "Repeated invalid device data detected: 'devName', skipping inverter data extraction"
        in caplog.text
    )
    assert (
        "Envoy returned incomplete inverter data, no data reported for:"
        not in caplog.text
    )
    assert "Envoy returned complete inverter data for:" not in caplog.text
    caplog.clear()

    # the repeated message shows as debug next time
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters == {}
    assert (
        "Repeated invalid device data detected: 'devName', skipping inverter data extraction"
        in caplog.text
    )
    assert (
        "Envoy returned incomplete inverter data, no data reported for:"
        not in caplog.text
    )
    assert "Envoy returned complete inverter data for:" not in caplog.text
    caplog.clear()

    # restore original mock to test reset
    payload = await load_json_fixture(version, "ivp_pdm_device_data")
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    await envoy.update()
    data = envoy.data
    assert data
    assert len(data.inverters) == inverter_count
    assert sn in data.inverters
    assert (
        "Repeated invalid device data detected: 'devName', skipping inverter data extraction"
        not in caplog.text
    )
    assert (
        "Invalid device data detected: 'devName', skipping inverter data extraction"
        not in caplog.text
    )
    assert (
        "Envoy returned incomplete inverter data, no data reported for:"
        not in caplog.text
    )
    assert f"Envoy returned complete inverter data for: {sn}" in caplog.text
    caplog.clear()

    # without lastReadings we should not have device_to_test sn in inverters result
    # warning should show again after restore in previous test
    del payload[device_to_test]["channels"][0]["lastReading"]
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters
    assert sn not in data.inverters
    assert len(data.inverters) == inverter_count - 1
    assert "Invalid device data detected:" not in caplog.text
    assert (
        f"Envoy returned incomplete inverter data, no data reported for: {sn}"
        in caplog.text
    )
    assert "Envoy returned complete inverter data for:" not in caplog.text
    caplog.clear()

    # all bad has been reset by previous restore and warning should show again
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=empty_payload,
    )
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters == {}
    assert (
        "Invalid device data detected: 'devName', skipping inverter data extraction"
        in caplog.text
    )
    assert (
        "Envoy returned incomplete inverter data, no data reported for:"
        not in caplog.text
    )
    assert "Envoy returned complete inverter data for:" not in caplog.text
    caplog.clear()


@pytest.mark.parametrize(
    ("version", "inverter_count", "device_to_test"),
    [
        (
            "8.2.4345_with_device_data",
            15,
            "553648384",
        ),
        (
            "8.3.5289_modGone",
            12,
            "553649152",
        ),
    ],
    ids=[
        "8.2.4345_with_device_data",
        "8.3.5289_modGone",
    ],
)
@pytest.mark.asyncio
async def test_no_active_inverter_devices_data(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    caplog: pytest.LogCaptureFixture,
    inverter_count: int,
    device_to_test: str,
) -> None:
    """Test handling of no active inverter in update"""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None

    # verify found inverter count
    assert len(data.inverters) == inverter_count

    # verify data of device ended up in sn entry
    payload = await load_json_fixture(version, "ivp_pdm_device_data")
    sn = payload[device_to_test]["sn"]
    assert sn in data.inverters

    # test handling of all inverters with active False at update
    for id, device in payload.items():
        if id not in ("deviceCount", "deviceDataLimit") and device["devName"] == "pcu":
            device["active"] = False

    caplog.clear()

    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters == {}
    assert "No active inverter devices detected, skipping" in caplog.text
    assert "nvalid device data detected:" not in caplog.text
    caplog.clear()

    # on repeated problems it should be debug, no warning
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters == {}
    assert "No active inverter devices detected repeat" in caplog.text
    assert "nvalid device data detected:" not in caplog.text
    caplog.clear()

    # on restore debug entry should show restored inverters
    payload = await load_json_fixture(version, "ivp_pdm_device_data")
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters
    assert sn in data.inverters
    assert "No active inverter devices detected repeat" not in caplog.text
    assert "nvalid device data detected:" not in caplog.text
    assert "Envoy returned complete inverter data for:" in caplog.text
    caplog.clear()

    # test single inactive and rering of warn
    sn = payload[device_to_test]["sn"]
    payload[device_to_test]["active"] = False
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters
    assert sn not in data.inverters
    assert f"Envoy did not provide previously reported inverters, no data reported for: {sn}"
    caplog.clear()

    caplog.set_level(logging.WARN)
    for _ in range(RESIGNAL_INTERVAL - 1):
        await envoy.update()
        data = envoy.data
        assert data
        assert data.inverters
        assert sn not in data.inverters
        assert (
            "Envoy did not provide previously reported inverters, no data reported for"
            not in caplog.text
        )
        assert (
            "Invalid device data detected: 'devName', skipping inverter data extraction"
            not in caplog.text
        )
        assert (
            "Envoy returned incomplete inverter data, no data reported for:"
            not in caplog.text
        )
        assert "Envoy returned complete inverter data for:" not in caplog.text
        assert (
            "Envoy did not provide all inverters or inverter data, no data reported for:"
            not in caplog.text
        )
        assert "Envoy returned complete inverter data for:" not in caplog.text
        caplog.clear()

    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters
    assert sn not in data.inverters
    assert f"Envoy did not provide previously reported inverters, no data reported for: {sn}"
    caplog.clear()


@pytest.mark.parametrize(
    ("version", "inverter_count", "device_to_test"),
    [
        (
            "8.2.4345_with_device_data",
            15,
            "553648384",
        ),
        (
            "8.3.5289_modGone",
            12,
            "553649152",
        ),
    ],
    ids=[
        "8.2.4345_with_device_data",
        "8.3.5289_modGone",
    ],
)
@pytest.mark.asyncio
async def test_disappearing_and_returning_inverter_devices(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    caplog: pytest.LogCaptureFixture,
    inverter_count: int,
    device_to_test: str,
) -> None:
    """Test handling of inverters completely disappearing and returning during update"""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)
    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None

    # verify found inverter count
    assert len(data.inverters) == inverter_count

    # verify data of device ended up in sn entry
    payload = await load_json_fixture(version, "ivp_pdm_device_data")
    sn = payload[device_to_test]["sn"]
    assert sn in data.inverters

    # test handling of disappearing inverter device
    del payload[device_to_test]
    caplog.clear()

    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters
    assert sn not in data.inverters
    assert (
        f"Envoy did not provide previously reported inverters, no data reported for: {sn}"
        in caplog.text
    )
    assert "nvalid device data detected:" not in caplog.text
    assert "incomplete inverter data" not in caplog.text
    caplog.clear()

    # on RESIGNAL_INTERVAL - 1 repeats no warning
    # set log level to warn to reduce log output, can't detect debug now
    caplog.set_level(logging.WARN)
    for _ in range(RESIGNAL_INTERVAL - 1):
        await envoy.update()
    assert (
        "Envoy did not provide previously reported inverters, no data reported for:"
        not in caplog.text
    )
    assert "nvalid device data detected:" not in caplog.text
    assert "incomplete inverter data" not in caplog.text
    assert "Envoy returned complete inverter data for:" not in caplog.text
    assert (
        "Envoy did not provide all inverters or inverter data, no data reported for:"
        not in caplog.text
    )

    # repeat message on RESIGNAL_INTERVAL
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters
    assert sn not in data.inverters
    assert (
        "Envoy did not provide previously reported inverters, no data reported for:"
        not in caplog.text
    )
    assert "nvalid device data detected:" not in caplog.text
    assert "incomplete inverter data" not in caplog.text
    assert (
        f"Envoy did not provide all inverters or inverter data, no data reported for: {sn}"
        in caplog.text
    )
    caplog.clear()
    # restore debug level for next test
    caplog.set_level(logging.DEBUG)

    # on restore the missed one should report
    payload = await load_json_fixture(version, "ivp_pdm_device_data")
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters
    assert sn in data.inverters
    assert (
        "Envoy did not provide previously reported inverters, no data reported for:"
        not in caplog.text
    )
    assert "nvalid device data detected:" not in caplog.text
    assert "incomplete inverter data" not in caplog.text
    assert f"Envoy returned complete inverter data for: {sn}" in caplog.text
    caplog.clear()


@pytest.mark.parametrize(
    ("version", "inverter_count", "device_to_test"),
    [
        (
            "8.2.4345_with_device_data",
            15,
            "553648384",
        ),
        (
            "8.3.5289_modGone",
            12,
            "553649152",
        ),
    ],
    ids=[
        "8.2.4345_with_device_data",
        "8.3.5289_modGone",
    ],
)
@pytest.mark.asyncio
async def test_rering_of_incomplete_inverter_devices(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    caplog: pytest.LogCaptureFixture,
    inverter_count: int,
    device_to_test: str,
) -> None:
    """Test rering of inverters with incomplete data during update"""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)
    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None

    # verify found inverter count
    assert len(data.inverters) == inverter_count

    # verify data of device ended up in sn entry
    payload = await load_json_fixture(version, "ivp_pdm_device_data")
    sn = payload[device_to_test]["sn"]
    assert sn in data.inverters

    # without lastReadings we should not have device_to_test sn in inverters result
    # no warning as that is suppressed after previous test
    del payload[device_to_test]["devName"]
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters == {}
    assert (
        "Invalid device data detected: 'devName', skipping inverter data extraction"
        in caplog.text
    )
    assert (
        "Envoy returned incomplete inverter data, no data reported for:"
        not in caplog.text
    )
    assert "Envoy returned complete inverter data for:" not in caplog.text
    assert (
        "Envoy did not provide all inverters or inverter data, no data reported for:"
        not in caplog.text
    )
    assert "Envoy returned complete inverter data for:" not in caplog.text
    caplog.clear()

    # next updates should not signal warnings
    caplog.set_level(logging.WARN)
    for _ in range(RESIGNAL_INTERVAL):
        await envoy.update()
        data = envoy.data
        assert data
        assert data.inverters == {}
        assert (
            "Invalid device data detected: 'devName', skipping inverter data extraction"
            not in caplog.text
        )
        assert (
            "Envoy returned incomplete inverter data, no data reported for:"
            not in caplog.text
        )
        assert "Envoy returned complete inverter data for:" not in caplog.text
        assert (
            "Envoy did not provide all inverters or inverter data, no data reported for:"
            not in caplog.text
        )
        assert "Envoy returned complete inverter data for:" not in caplog.text
        caplog.clear()

    caplog.set_level(logging.DEBUG)
    # Now we should see rering for skipped inverters
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters == {}
    assert (
        "Invalid device data detected: 'devName', skipping inverter data extraction"
        in caplog.text
    )
    assert (
        "Envoy returned incomplete inverter data, no data reported for:"
        not in caplog.text
    )
    assert "Envoy returned complete inverter data for:" not in caplog.text
    assert (
        "Envoy did not provide all inverters or inverter data, no data reported for:"
        not in caplog.text
    )
    assert "Envoy returned complete inverter data for:" not in caplog.text
    caplog.clear()

    # Now we should see no rering for skipped inverters
    await envoy.update()
    data = envoy.data
    assert data
    assert data.inverters == {}
    assert (
        "Invalid device data detected: 'devName', skipping inverter data extraction"
        not in caplog.text
    )
    assert (
        "Envoy returned incomplete inverter data, no data reported for:"
        not in caplog.text
    )
    assert "Envoy returned complete inverter data for:" not in caplog.text
    assert (
        "Envoy did not provide all inverters or inverter data, no data reported for:"
        not in caplog.text
    )
    assert "Envoy returned complete inverter data for:" not in caplog.text
    caplog.clear()


@pytest.mark.parametrize(
    ("version", "inverter_count", "device_to_test"),
    [
        (
            "8.2.4345_with_device_data",
            15,
            "553648384",
        ),
        (
            "8.3.5289_modGone",
            12,
            "553649152",
        ),
    ],
    ids=[
        "8.2.4345_with_device_data",
        "8.3.5289_modGone",
    ],
)
@pytest.mark.asyncio
async def test_inverter_devices_divide_by_zero(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    inverter_count: int,
    device_to_test: str,
) -> None:
    """Test divide by zero is handled by inverter from_device_data."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    payload = await load_json_fixture(version, "ivp_pdm_device_data")
    sn = payload[device_to_test]["sn"]

    # force lastReading duration to zero
    # inverter should be in data with None for energy_produced
    payload[device_to_test]["channels"][0]["lastReading"]["duration"] = 0
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None
    assert data.inverters is not None
    assert sn in data.inverters
    assert len(data.inverters) == inverter_count
    assert data.inverters[sn].last_report_duration == 0
    assert data.inverters[sn].energy_produced is None

    # test with duration key missing, should return none again
    # reuse payload already read
    del payload[device_to_test]["channels"][0]["lastReading"]["duration"]
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    await envoy.update()
    data = envoy.data
    assert data is not None
    assert data.inverters is not None
    assert len(data.inverters) == inverter_count
    assert sn in data.inverters
    assert data.inverters[sn].last_report_duration is None
    assert data.inverters[sn].energy_produced is None


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


@pytest.mark.parametrize(
    "version",
    [
        "8.2.4264_metered_noct",
        "7.6.114_without_cts",
        "7.3.466_metered_disabled_cts",
    ],
    ids=[
        "8.2.4264_metered_noct",
        "7.6.114_without_cts",
        "7.3.466_metered_disabled_cts",
    ],
)
@pytest.mark.asyncio
async def test_client_session_close(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test client session close code COV."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)

    # pass aiohttp client session for envoy to use
    envoy = await get_mock_envoy(client_session=test_client_session)
    data = envoy.data
    assert data is not None
    assert envoy._client is not None
    assert not envoy._client.closed
    await envoy.close()
    # it's our client, pyenphase will not close it on close
    assert not envoy._client.closed

    # test with pyenphase internal created client
    envoy2 = await get_mock_envoy(client_session=None)
    data = envoy2.data
    assert data is not None
    assert envoy2._client is not None
    assert not envoy2._client.closed
    await envoy2.close()
    # it's pyenphase's client, will close it on close
    assert envoy2._client.closed

    envoy3 = await get_mock_envoy(client_session=None)
    data = envoy3.data
    assert data is not None
    assert not envoy3._client.closed

    # force close internal envoy client for cov test
    await envoy3._client.close()
    assert envoy3._client.closed
    await envoy3.close()
    # was closed already, should still be closed.
    assert envoy3._client.closed


@pytest.mark.parametrize(
    "version",
    [
        "7.3.130_no_consumption",
    ],
    ids=[
        "7.3.130_no_consumption",
    ],
)
@pytest.mark.asyncio
async def test_early_v7_with_all_401(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
) -> None:
    """Test early v7 startup where several probe endpoints return auth-required."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # endpoints return 401 on early v7 firmwares
    for endpoint in [
        "production.json?details=1",
        "production",
        "ivp/pdm/device_data",
        "api/v1/production/inverters",
        "ivp/ensemble/inventory",
        "admin/lib/tariff",
    ]:
        override_mock(
            mock_aioresponse,
            "get",
            f"https://127.0.0.1/{endpoint}",
            exception=EnvoyAuthenticationRequired("Test early v7 401"),
            repeat=True,
            payload=[],
        )

    envoy = await get_mock_envoy(client_session=test_client_session)
    assert updater_features(envoy._updaters) == {
        "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
        "EnvoyMetersUpdater": SupportedFeatures.DUALPHASE | SupportedFeatures.CTMETERS,
    }


@pytest.mark.parametrize(
    (
        "version",
        "cons_watts_now",
        "cons_watt_hours_today",
        "cons_watt_hours_last_7_days",
        "cons_watt_hours_lifetime",
    ),
    [
        (
            "8.3.5433_tot_is_net_cons",
            428 + 357,
            5649402,
            5649402,
            5649402 + 14405465,
        ),
        (
            "8.3.5167_3rd-pv",
            325,
            8958,
            0,
            253002,
        ),
        (
            "8.2.4345_with_device_data",
            1009,
            14567,
            136896,
            1008081,
        ),
        (
            "8.2.4286_with_3cts_and_battery_split",
            8885,
            0,
            0,
            15113474,
        ),
        (
            "7.6.175_with_cts",
            477,
            19904,
            5,
            5145154,
        ),
    ],
    ids=[
        "8.3.5433_tot_is_net_cons",
        "8.3.5167_3rd-pv",
        "8.2.4345_with_device_data",
        "8.2.4286_with_3cts_and_battery_split",
        "7.6.175_with_cts",
    ],
)
@pytest.mark.asyncio
async def test_metered_cons_is_not_net(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    cons_watts_now: int,
    cons_watt_hours_today: int,
    cons_watt_hours_last_7_days: int,
    cons_watt_hours_lifetime: int,
) -> None:
    """Verify consumption data is correct, 8.3.5433 needs correction. Phase data is tested in test_endpoints."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None

    assert data.system_consumption
    assert envoy.consumption_meter_type
    assert data.system_production
    assert data.system_consumption.watts_now == cons_watts_now
    assert data.system_consumption.watt_hours_today == cons_watt_hours_today
    assert data.system_consumption.watt_hours_last_7_days == cons_watt_hours_last_7_days
    assert data.system_consumption.watt_hours_lifetime == cons_watt_hours_lifetime


@pytest.mark.parametrize(
    "version",
    [
        "8.3.5433_tot_is_net_cons",
    ],
    ids=[
        "8.3.5433_tot_is_net_cons",
    ],
)
@pytest.mark.asyncio
async def test_cons_is_not_net_full_phase_cov(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
) -> None:
    """Finalize COV for metered 8.3.5433 force phase skipped paths."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    full_host = endpoint_path(version, "127.0.0.1")

    # force difference in one phase so it;s skipped
    production_json = await load_json_fixture(version, "production.json")
    production_json["consumption"][0]["lines"][1]["wNow"] = 27000

    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/production.json",
        status=200,
        payload=production_json,
        repeat=True,
    )
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/production.json?details=1",
        status=200,
        payload=production_json,
        repeat=True,
    )

    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None
    assert data.system_consumption is not None
    assert data.system_net_consumption is not None
    assert data.system_production is not None
    assert data.system_consumption_phases is not None
    assert data.system_net_consumption_phases is not None
    assert data.system_production_phases is not None
    assert (
        data.system_consumption.watts_now
        == data.system_net_consumption.watts_now + data.system_production.watts_now
    )
    assert (
        data.system_consumption_phases[PhaseNames.PHASE_1].watts_now  # type: ignore
        == data.system_net_consumption_phases[PhaseNames.PHASE_1].watts_now  # type: ignore
        + data.system_production_phases[PhaseNames.PHASE_1].watts_now  # type: ignore
    )
    assert data.system_consumption_phases[PhaseNames.PHASE_2].watts_now == 27000  # type: ignore

    # run test with single phase active, should skip phase part
    meter_json: Any = await load_json_fixture(version, "ivp_meters")
    meter_json[0]["phaseCount"] = 1
    meter_json[1]["phaseCount"] = 1
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}/ivp/meters",
        status=200,
        payload=meter_json,
        repeat=True,
    )
    envoy = await get_mock_envoy(test_client_session)
    data = envoy.data
    assert data is not None

    assert data.system_consumption
    assert data.system_net_consumption
    assert data.system_production
    # validate agg data is now different
    assert (
        data.system_consumption.watts_now
        == data.system_net_consumption.watts_now + data.system_production.watts_now
    )
    assert data.system_consumption_phases is None
    assert data.system_net_consumption_phases is None
    assert data.system_production_phases is None
