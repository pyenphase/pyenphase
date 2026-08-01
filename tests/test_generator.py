"""Test generator data for envoy with an Enpower and standby generator"""

import logging

import aiohttp
import orjson
import pytest
from aioresponses import aioresponses

from pyenphase.const import (
    URL_GEN_CONFIG,
    URL_GEN_MODE,
    URL_GEN_SCHEDULE,
    URL_GENERATOR,
)
from pyenphase.envoy import SupportedFeatures
from pyenphase.exceptions import EnvoyFeatureNotAvailable

from .common import (
    endpoint_path,
    get_mock_envoy,
    latest_request,
    load_json_fixture,
    override_mock,
    prep_envoy,
    start_7_firmware_mock,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "version",
    [
        "8.2.127_with_generator_running",
        "8.3.5169_with_generator",
    ],
    ids=[
        "8.2.127_with_generator_running",
        "8.3.5169_with_generator",
    ],
)
@pytest.mark.asyncio
async def test_generator_data(
    version: str,
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify generator status, config and schedule models."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)

    assert envoy.supported_features & SupportedFeatures.GENERATOR

    data = envoy.data
    assert data is not None

    generator_json = await load_json_fixture(version, "ivp_ensemble_generator")
    assert data.generator is not None
    assert data.generator.admin_state == generator_json["admin_state"]
    assert data.generator.oper_state == generator_json["oper_state"]
    assert data.generator.admin_mode == generator_json["admin_mode"]
    assert data.generator.schedule == generator_json["schedule"]
    assert data.generator.start_soc == generator_json["start_soc"]
    assert data.generator.stop_soc == generator_json["stop_soc"]
    assert data.generator.exc_on == generator_json["exc_on"]
    assert data.generator.present == bool(generator_json["present"])
    assert data.generator.type == generator_json["type"]

    config_json = await load_json_fixture(version, "ivp_ss_gen_config")
    assert data.generator_config is not None
    assert data.generator_config.max_cont_gen_amps == config_json["max_cont_gen_amps"]
    assert (
        data.generator_config.min_gen_loading_perc
        == config_json["min_gen_loading_perc"]
    )
    assert (
        data.generator_config.max_gen_efficiency_perc
        == config_json["max_gen_efficiency_perc"]
    )
    assert (
        data.generator_config.name_plate_rating_wat
        == config_json["name_plate_rating_wat"]
    )
    assert data.generator_config.start_method == config_json["start_method"]
    assert data.generator_config.warm_up_mins == config_json["warm_up_mins"]
    assert data.generator_config.cool_down_mins == config_json["cool_down_mins"]
    assert data.generator_config.gen_type == config_json["gen_type"]
    assert data.generator_config.model == config_json["model"]
    assert data.generator_config.manufacturer == config_json["manufacturer"]
    assert data.generator_config.last_updated_by == config_json["last_updated_by"]
    assert data.generator_config.generator_id == config_json["generator_id"]
    assert (
        data.generator_config.charge_from_generator
        == config_json["charge_from_generator"]
    )

    schedule_json = await load_json_fixture(version, "ivp_ss_gen_schedule")
    assert data.generator_schedule is not None
    assert (
        data.generator_schedule.exercise_freq_in_weeks
        == schedule_json["exercise_config"]["freq_in_weeks"]
    )
    assert (
        data.generator_schedule.exercise_start
        == schedule_json["exercise_config"]["start"]
    )
    assert (
        data.generator_schedule.exercise_duration
        == schedule_json["exercise_config"]["duration"]
    )
    assert (
        data.generator_schedule.exercise_day == schedule_json["exercise_config"]["day"]
    )
    assert (
        data.generator_schedule.default_start_soc
        == schedule_json["default_soc"]["start_soc"]
    )
    assert (
        data.generator_schedule.default_stop_soc
        == schedule_json["default_soc"]["stop_soc"]
    )
    assert data.generator_schedule.last_updated_by == schedule_json["last_updated_by"]

    # raw data for all three endpoints should be available
    assert data.raw[URL_GENERATOR] == generator_json
    assert data.raw[URL_GEN_CONFIG] == config_json
    assert data.raw[URL_GEN_SCHEDULE] == schedule_json


@pytest.mark.asyncio
async def test_generator_mode_data(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify the generator mode model for firmware with the gen_mode endpoint."""
    version = "8.3.5169_with_generator"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)

    assert envoy.supported_features & SupportedFeatures.GENERATOR

    data = envoy.data
    assert data is not None

    mode_json = await load_json_fixture(version, "ivp_ss_gen_mode")
    assert data.generator_mode is not None
    assert data.generator_mode.gen_cmd == mode_json["gen_cmd"]
    assert data.generator_mode.last_updated_by == mode_json["last_updated_by"]
    assert data.raw[URL_GEN_MODE] == mode_json


@pytest.mark.asyncio
async def test_generator_mode_not_supported(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify no generator mode is reported for firmware without the endpoint."""
    version = "8.2.127_with_generator_running"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)

    assert envoy.supported_features & SupportedFeatures.GENERATOR

    data = envoy.data
    assert data is not None
    assert data.generator_mode is None
    assert URL_GEN_MODE not in data.raw


@pytest.mark.asyncio
async def test_no_generator_data(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify no generator data is reported for an Enpower system without generator."""
    version = "8.2.127_with_3cts_and_battery_split"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)

    assert not envoy.supported_features & SupportedFeatures.GENERATOR

    data = envoy.data
    assert data is not None
    assert data.generator is None
    assert data.generator_config is None
    assert data.generator_schedule is None
    assert data.generator_mode is None
    assert URL_GENERATOR not in data.raw
    assert URL_GEN_CONFIG not in data.raw
    assert URL_GEN_SCHEDULE not in data.raw
    assert URL_GEN_MODE not in data.raw

    # generator mode control is feature gated
    with pytest.raises(EnvoyFeatureNotAvailable):
        await envoy.set_generator_mode("auto")


@pytest.mark.asyncio
async def test_generator_partial_endpoint_support(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify generator data degrades per-endpoint when only gen_config exists."""
    version = "8.3.5169_with_generator"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)

    # Simulate a firmware variant that reports gen_config but exposes none
    # of the other generator endpoints
    full_host = endpoint_path(version, "127.0.0.1")
    for path in (URL_GENERATOR, URL_GEN_SCHEDULE, URL_GEN_MODE):
        override_mock(
            mock_aioresponse, "get", f"{full_host}{path}", status=404, repeat=True
        )

    envoy = await get_mock_envoy(test_client_session)

    # gen_config alone still flags generator support
    assert envoy.supported_features & SupportedFeatures.GENERATOR

    data = envoy.data
    assert data is not None
    # config is populated, all other generator fields degrade to None
    assert data.generator_config is not None
    assert URL_GEN_CONFIG in data.raw
    assert data.generator is None
    assert data.generator_schedule is None
    assert data.generator_mode is None
    assert URL_GENERATOR not in data.raw
    assert URL_GEN_SCHEDULE not in data.raw
    assert URL_GEN_MODE not in data.raw

    # mode control still works without gen_mode data; the preemptive
    # local update is skipped as there is no generator_mode to update
    mock_aioresponse.post(
        f"{full_host}{URL_GEN_MODE}", status=200, payload={}, repeat=True
    )
    await envoy.set_generator_mode("auto")
    _cnt, request_data = latest_request(mock_aioresponse, "POST", URL_GEN_MODE)
    assert orjson.loads(request_data) == {"gen_cmd": "auto"}
    assert data.generator_mode is None


@pytest.mark.asyncio
async def test_set_generator_mode(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify setting the generator mode sends the expected request."""
    version = "8.3.5169_with_generator"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)

    assert envoy.supported_features & SupportedFeatures.GENERATOR

    full_host = endpoint_path(version, envoy.host)
    mock_aioresponse.post(
        f"{full_host}{URL_GEN_MODE}", status=200, payload={}, repeat=True
    )

    for mode in ("off", "on", "auto"):
        await envoy.set_generator_mode(mode)
        _cnt, request_data = latest_request(mock_aioresponse, "POST", URL_GEN_MODE)
        assert orjson.loads(request_data) == {"gen_cmd": mode}

    # input is normalized to lowercase before sending
    await envoy.set_generator_mode("AUTO")
    _cnt, request_data = latest_request(mock_aioresponse, "POST", URL_GEN_MODE)
    assert orjson.loads(request_data) == {"gen_cmd": "auto"}

    # internal data is preemptively updated with the new mode
    assert envoy.data is not None
    assert envoy.data.generator_mode is not None
    assert envoy.data.generator_mode.gen_cmd == "auto"

    # invalid modes are rejected without sending a request
    with pytest.raises(ValueError):
        await envoy.set_generator_mode("standby")
