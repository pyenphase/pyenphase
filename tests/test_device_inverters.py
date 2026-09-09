"""Test inverter data from device_data endpoint."""

import logging
from typing import Any

import aiohttp
import pytest
from aioresponses import aioresponses

from pyenphase.const import URL_DEVICE_DATA
from pyenphase.envoy import UPDATERS, Envoy, SupportedFeatures, register_updater
from pyenphase.updaters.api_v1_production_inverters import (
    EnvoyApiV1ProductionInvertersUpdater,
)
from pyenphase.updaters.device_data_inverters import (
    RESIGNAL_INTERVAL,
    EnvoyDeviceDataInvertersUpdater,
)

from .common import (
    get_mock_envoy,
    load_json_fixture,
    override_mock,
    prep_envoy,
    start_7_firmware_mock,
    updater_features,
)

LOGGER = logging.getLogger(__name__)


async def init_device_test(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    inverter_count: int,
    device_to_test: str,
) -> tuple[Envoy, str, dict[str, Any]]:
    """Initialize inverter device test."""
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
    payload: dict[str, Any] = await load_json_fixture(version, "ivp_pdm_device_data")
    sn = payload[device_to_test]["sn"]
    assert sn in data.inverters

    return envoy, sn, payload


async def envoy_update(
    envoy: Envoy, sn: str, inverter_included: bool = True, inverter_count: int = 0
) -> None:
    """Update envoy data and test results."""
    await envoy.update()
    data = envoy.data
    assert data
    assert len(data.inverters) == inverter_count
    assert (sn in data.inverters) if inverter_included else (sn not in data.inverters)


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
    envoy, _sn, _payload = await init_device_test(
        mock_aioresponse, test_client_session, version, inverter_count, device_to_test
    )
    assert envoy.data


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
    envoy, sn, payload = await init_device_test(
        mock_aioresponse, test_client_session, version, inverter_count, device_to_test
    )

    # verify inverters with missing required keys at update
    # are excluded from data and no crash occurs
    # probe() detected these successful before

    # note that in each step we delete higher level data or
    # keys tested earlier in the code so we don't need to
    # reload the fixture file. If that changes reload may be needed

    caplog.clear()

    # without watts now we should not have device_to_test sn in inverters result
    # a warning for lost inverter data should be present
    del payload[device_to_test]["channels"][0]["watts"]["now"]
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    # update envoy, sn should not be in data and warn on log
    await envoy_update(envoy, sn, False, inverter_count - 1)
    assert f"no data reported for: {sn}" in caplog.text
    assert "previously reported inverters" not in caplog.text
    assert "nvalid device data detected" not in caplog.text
    assert " complete inverter data" not in caplog.text
    assert "all inverters or inverter data" not in caplog.text
    caplog.clear()

    # without lastReadings endDate we should not have device_to_test sn in inverters result
    # no warning, that is suppressed after previous test issued a warning for sn
    del payload[device_to_test]["channels"][0]["lastReading"]["endDate"]
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    await envoy_update(envoy, sn, False, inverter_count - 1)
    assert "no data reported for:" not in caplog.text
    assert "previously reported inverters" not in caplog.text
    assert "nvalid device data detected" not in caplog.text
    assert " complete inverter data" not in caplog.text
    assert "all inverters or inverter data" not in caplog.text
    caplog.clear()

    # without lastReadings we should not have device_to_test sn in inverters result
    # no warning, that is suppressed after previous test issued a warning for sn
    del payload[device_to_test]["channels"][0]["lastReading"]
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )
    await envoy_update(envoy, sn, False, inverter_count - 1)
    assert "no data reported for:" not in caplog.text
    assert "previously reported inverters" not in caplog.text
    assert "nvalid device data detected" not in caplog.text
    assert " complete inverter data" not in caplog.text
    assert "all inverters or inverter data" not in caplog.text
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
    await envoy_update(envoy, sn, False, inverter_count - 1)
    assert "no data reported for:" not in caplog.text
    assert "previously reported inverters" not in caplog.text
    assert "nvalid device data detected" not in caplog.text
    assert " complete inverter data" not in caplog.text
    assert "all inverters or inverter data" not in caplog.text
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
    await envoy_update(envoy, sn, False, 0)
    assert "no data reported for:" not in caplog.text
    assert "previously reported inverters" not in caplog.text
    assert "nvalid device data detected: 'sn'" in caplog.text
    assert " complete inverter data" not in caplog.text
    assert "all inverters or inverter data" not in caplog.text
    caplog.clear()

    # without any data we should get repeated warning after previous test now for devName
    empty_payload: dict[str, Any] = {device_to_test: {}}
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=empty_payload,
    )
    await envoy_update(envoy, sn, False, 0)
    assert "no data reported for:" not in caplog.text
    assert "previously reported inverters" not in caplog.text
    assert "nvalid device data detected: 'devName'" in caplog.text
    assert " complete inverter data" not in caplog.text
    assert "all inverters or inverter data" not in caplog.text
    caplog.clear()

    # the repeated message shows as debug next time
    await envoy_update(envoy, sn, False, 0)
    assert "no data reported for:" not in caplog.text
    assert "previously reported inverters" not in caplog.text
    assert "Invalid device data detected: 'devName'" not in caplog.text
    assert "Repeated invalid device data detected: 'devName'" in caplog.text
    assert " complete inverter data" not in caplog.text
    assert "all inverters or inverter data" not in caplog.text
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
    await envoy_update(envoy, sn, True, inverter_count)
    assert "no data reported for:" not in caplog.text
    assert "previously reported inverters" not in caplog.text
    assert "Invalid device data detected: 'devName'" not in caplog.text
    assert "Repeated invalid device data detected: 'devName'" not in caplog.text
    assert f" complete inverter data for: {sn}" in caplog.text
    assert "all inverters or inverter data" not in caplog.text
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
    await envoy_update(envoy, sn, False, inverter_count - 1)
    assert f"no data reported for: {sn}" in caplog.text
    assert "previously reported inverters" not in caplog.text
    assert "Invalid device data detected:" not in caplog.text
    assert "Repeated invalid device data detected: 'devName'" not in caplog.text
    assert " complete inverter data for:" not in caplog.text
    assert "all inverters or inverter data" not in caplog.text
    caplog.clear()

    # resignal been reset by previous restore and warning should show again
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=empty_payload,
    )
    await envoy_update(envoy, sn, False, 0)
    assert "no data reported for:" not in caplog.text
    assert "previously reported inverters" not in caplog.text
    assert "Invalid device data detected: 'devName'" in caplog.text
    assert "Repeated invalid device data detected: 'devName'" not in caplog.text
    assert " complete inverter data for:" not in caplog.text
    assert "all inverters or inverter data" not in caplog.text
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
    """Test handling of no active inverter at all in update"""
    envoy, sn, payload = await init_device_test(
        mock_aioresponse, test_client_session, version, inverter_count, device_to_test
    )

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
    await envoy_update(envoy, sn, False, 0)
    assert "No active inverter devices detected, skipping" in caplog.text
    assert "no data reported for:" not in caplog.text
    assert "previously reported inverters" not in caplog.text
    assert "nvalid device data detected:" not in caplog.text
    assert "Repeated invalid device data detected: 'devName'" not in caplog.text
    assert " complete inverter data for:" not in caplog.text
    assert "all inverters or inverter data" not in caplog.text
    caplog.clear()

    # on repeated problems it should be debug, no warning
    for _ in range(RESIGNAL_INTERVAL):
        await envoy_update(envoy, sn, False, 0)
        assert "No active inverter devices detected repeat" in caplog.text
        assert "nvalid device data detected:" not in caplog.text
        assert "previously reported inverters" not in caplog.text
        assert "nvalid device data detected:" not in caplog.text
        assert "Repeated invalid device data detected: 'devName'" not in caplog.text
        assert " complete inverter data for:" not in caplog.text
        assert "all inverters or inverter data" not in caplog.text
        caplog.clear()

    # now no active warning should rering
    await envoy_update(envoy, sn, False, 0)
    assert "No active inverter devices detected repeat (0)" in caplog.text
    assert "nvalid device data detected:" not in caplog.text
    assert "previously reported inverters" not in caplog.text
    assert "nvalid device data detected:" not in caplog.text
    assert "Repeated invalid device data detected: 'devName'" not in caplog.text
    assert " complete inverter data for:" not in caplog.text
    assert "all inverters or inverter data" not in caplog.text
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
    await envoy_update(envoy, sn, True, inverter_count)
    assert "No active inverter devices detected repeat" not in caplog.text
    assert "nvalid device data detected:" not in caplog.text
    assert "previously reported inverters" not in caplog.text
    assert "nvalid device data detected:" not in caplog.text
    assert "Repeated invalid device data detected: 'devName'" not in caplog.text
    assert " complete inverter data for: " in caplog.text
    assert "all inverters or inverter data" not in caplog.text
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
async def test_single_not_active_inverter_devices_data(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    version: str,
    caplog: pytest.LogCaptureFixture,
    inverter_count: int,
    device_to_test: str,
) -> None:
    """Test handling of single not active inverter in update"""
    envoy, sn, payload = await init_device_test(
        mock_aioresponse, test_client_session, version, inverter_count, device_to_test
    )

    # test single inactive and rering of warn
    sn = payload[device_to_test]["sn"]
    payload[device_to_test]["active"] = False

    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )

    # test warn on previous found inverter now missing
    await envoy_update(envoy, sn, False, inverter_count - 1)
    assert "No active inverter devices detected, skipping" not in caplog.text
    assert f"no data reported for: {sn}" in caplog.text
    assert "previously reported inverters" in caplog.text
    assert "nvalid device data detected:" not in caplog.text
    assert "Repeated invalid device data detected: 'devName'" not in caplog.text
    assert " complete inverter data for:" not in caplog.text
    assert "all inverters or inverter data" not in caplog.text
    caplog.clear()

    # between warning resignal no warnings
    caplog.set_level(logging.WARN)
    for _ in range(RESIGNAL_INTERVAL - 1):
        await envoy_update(envoy, sn, False, inverter_count - 1)
        assert "No active inverter devices detected, skipping" not in caplog.text
        assert "no data reported for: " not in caplog.text
        assert "previously reported inverters" not in caplog.text
        assert "nvalid device data detected:" not in caplog.text
        assert "Repeated invalid device data detected: 'devName'" not in caplog.text
        assert " complete inverter data for:" not in caplog.text
        assert "all inverters or inverter data" not in caplog.text
        caplog.clear()

    caplog.set_level(logging.DEBUG)

    # verify resignal, it's now on skipped list so test for that message
    await envoy_update(envoy, sn, False, inverter_count - 1)
    assert "No active inverter devices detected, skipping" not in caplog.text
    assert f"no data reported for: {sn}" in caplog.text
    assert "previously reported inverters" not in caplog.text
    assert "nvalid device data detected:" not in caplog.text
    assert "Repeated invalid device data detected: 'devName'" not in caplog.text
    assert " complete inverter data for:" not in caplog.text
    assert "all inverters or inverter data" in caplog.text
    caplog.clear()

    # restore active to True
    payload[device_to_test]["active"] = True
    override_mock(
        mock_aioresponse,
        "get",
        f"https://127.0.0.1{URL_DEVICE_DATA}",
        repeat=True,
        payload=payload,
    )

    # inverter should be reported in debug as back again
    await envoy_update(envoy, sn, True, inverter_count)
    assert "No active inverter devices detected" not in caplog.text
    assert "no data reported for:" not in caplog.text
    assert "previously reported inverters" not in caplog.text
    assert "nvalid device data detected:" not in caplog.text
    assert "Repeated invalid device data detected: 'devName'" not in caplog.text
    assert f" complete inverter data for: {sn}" in caplog.text
    assert "all inverters or inverter data" not in caplog.text
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
    envoy, sn, payload = await init_device_test(
        mock_aioresponse, test_client_session, version, inverter_count, device_to_test
    )

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
    await envoy_update(envoy, sn, False, inverter_count - 1)
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
    await envoy_update(envoy, sn, False, inverter_count - 1)
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
    await envoy_update(envoy, sn, True, inverter_count)
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
    envoy, sn, payload = await init_device_test(
        mock_aioresponse, test_client_session, version, inverter_count, device_to_test
    )

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
    await envoy_update(envoy, sn, False, 0)
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
        await envoy_update(envoy, sn, False, 0)
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
    await envoy_update(envoy, sn, False, 0)
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
    await envoy_update(envoy, sn, False, 0)
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
    envoy, sn, payload = await init_device_test(
        mock_aioresponse, test_client_session, version, inverter_count, device_to_test
    )

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
