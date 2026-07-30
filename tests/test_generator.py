"""Test generator data for envoy with an Enpower and standby generator"""

import logging

import aiohttp
import pytest
from aioresponses import aioresponses

from pyenphase.const import URL_GEN_CONFIG, URL_GEN_SCHEDULE, URL_GENERATOR
from pyenphase.envoy import SupportedFeatures

from .common import (
    get_mock_envoy,
    load_json_fixture,
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
    assert URL_GENERATOR not in data.raw
    assert URL_GEN_SCHEDULE not in data.raw
