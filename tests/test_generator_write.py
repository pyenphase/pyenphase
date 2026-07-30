"""Test generator write actions for envoy with an Enpower and standby generator"""

import logging
from copy import deepcopy

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

VERSION = "8.3.5169_with_generator"


@pytest.mark.asyncio
async def test_set_generator_exercise_schedule(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify setting the exercise schedule sends the round-tripped payload."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", VERSION)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    assert envoy.supported_features & SupportedFeatures.GENERATOR

    full_host = endpoint_path(VERSION, envoy.host)
    mock_aioresponse.post(
        f"{full_host}{URL_GEN_SCHEDULE}", status=200, payload={}, repeat=True
    )

    await envoy.set_generator_exercise_schedule(
        freq_in_weeks=2,
        day="mon",
        start=840,
        duration=20,
    )

    # payload is the full GET shape with only exercise_config replaced,
    # day normalized to the capitalized short name
    schedule_json = await load_json_fixture(VERSION, "ivp_ss_gen_schedule")
    expected = deepcopy(schedule_json)
    expected["exercise_config"] = {
        "freq_in_weeks": 2,
        "day": "Mon",
        "start": 840,
        "duration": 20,
    }
    _cnt, request_data = latest_request(mock_aioresponse, "POST", URL_GEN_SCHEDULE)
    assert orjson.loads(request_data) == expected

    # internal data is preemptively updated
    assert envoy.data is not None
    assert envoy.data.generator_schedule is not None
    assert envoy.data.generator_schedule.exercise_freq_in_weeks == 2
    assert envoy.data.generator_schedule.exercise_day == "Mon"
    assert envoy.data.generator_schedule.exercise_start == 840
    assert envoy.data.generator_schedule.exercise_duration == 20

    # out of range values are rejected without sending a request
    with pytest.raises(ValueError):
        await envoy.set_generator_exercise_schedule(
            freq_in_weeks=0, day="Mon", start=840, duration=20
        )
    # the official app's frequency domain is every 1-4 weeks
    with pytest.raises(ValueError):
        await envoy.set_generator_exercise_schedule(
            freq_in_weeks=5, day="Mon", start=840, duration=20
        )
    with pytest.raises(ValueError):
        await envoy.set_generator_exercise_schedule(
            freq_in_weeks=1, day="Monday", start=840, duration=20
        )
    with pytest.raises(ValueError):
        await envoy.set_generator_exercise_schedule(
            freq_in_weeks=1, day="Mon", start=-1, duration=20
        )
    with pytest.raises(ValueError):
        await envoy.set_generator_exercise_schedule(
            freq_in_weeks=1, day="Mon", start=1440, duration=20
        )
    with pytest.raises(ValueError):
        await envoy.set_generator_exercise_schedule(
            freq_in_weeks=1, day="Mon", start=840, duration=5
        )
    with pytest.raises(ValueError):
        await envoy.set_generator_exercise_schedule(
            freq_in_weeks=1, day="Mon", start=840, duration=65
        )
    # firmware accepts and persists intermediate values like 25 (verified
    # live on D8.3.5169) but the Enlighten UI renders them as a blank
    # duration field, so the library enforces the vendor step-10 domain
    with pytest.raises(ValueError):
        await envoy.set_generator_exercise_schedule(
            freq_in_weeks=1, day="Mon", start=840, duration=25
        )

    # setting the schedule before the first data update is rejected
    bad_envoy = await get_mock_envoy(test_client_session, update=False)
    await bad_envoy.probe()
    with pytest.raises(ValueError):
        await bad_envoy.set_generator_exercise_schedule(
            freq_in_weeks=1, day="Mon", start=840, duration=20
        )


@pytest.mark.asyncio
async def test_set_generator_charge_from_generator(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify setting charge from generator sends the round-tripped payload."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", VERSION)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    assert envoy.supported_features & SupportedFeatures.GENERATOR

    full_host = endpoint_path(VERSION, envoy.host)
    mock_aioresponse.post(
        f"{full_host}{URL_GEN_CONFIG}", status=200, payload={}, repeat=True
    )

    config_json = await load_json_fixture(VERSION, "ivp_ss_gen_config")
    assert config_json["charge_from_generator"] is True

    for new_value in (False, True):
        await envoy.set_generator_charge_from_generator(new_value)

        # payload is the full GET shape with only charge_from_generator replaced
        expected = deepcopy(config_json)
        expected["charge_from_generator"] = new_value
        _cnt, request_data = latest_request(mock_aioresponse, "POST", URL_GEN_CONFIG)
        assert orjson.loads(request_data) == expected

        # internal data is preemptively updated
        assert envoy.data is not None
        assert envoy.data.generator_config is not None
        assert envoy.data.generator_config.charge_from_generator == new_value

    # non-bool values are rejected without sending a request
    with pytest.raises(TypeError):
        await envoy.set_generator_charge_from_generator("true")  # type: ignore[arg-type]

    # setting before the first data update is rejected
    bad_envoy = await get_mock_envoy(test_client_session, update=False)
    await bad_envoy.probe()
    with pytest.raises(ValueError):
        await bad_envoy.set_generator_charge_from_generator(False)


@pytest.mark.asyncio
async def test_generator_write_actions_without_generator(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify generator write actions are feature gated without a generator."""
    version = "8.2.127_with_3cts_and_battery_split"
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    assert not envoy.supported_features & SupportedFeatures.GENERATOR

    with pytest.raises(EnvoyFeatureNotAvailable):
        await envoy.set_generator_exercise_schedule(
            freq_in_weeks=1, day="Mon", start=840, duration=20
        )
    with pytest.raises(EnvoyFeatureNotAvailable):
        await envoy.set_generator_charge_from_generator(True)


@pytest.mark.asyncio
async def test_set_generator_exercise_schedule_without_gen_schedule(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify the schedule setter rejects firmware without the gen_schedule endpoint."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", VERSION)
    caplog.set_level(logging.DEBUG)

    # Simulate a firmware variant with gen_config but no gen_schedule endpoint
    full_host = endpoint_path(VERSION, "127.0.0.1")
    for path in (URL_GENERATOR, URL_GEN_SCHEDULE, URL_GEN_MODE):
        override_mock(
            mock_aioresponse, "get", f"{full_host}{path}", status=404, repeat=True
        )

    envoy = await get_mock_envoy(test_client_session)
    assert envoy.supported_features & SupportedFeatures.GENERATOR
    assert envoy.data is not None
    assert envoy.data.generator_schedule is None

    with pytest.raises(EnvoyFeatureNotAvailable):
        await envoy.set_generator_exercise_schedule(
            freq_in_weeks=1, day="Mon", start=840, duration=20
        )
