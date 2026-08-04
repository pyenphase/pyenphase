"""Test generator write actions for envoy with an Enpower and standby generator"""

import logging
from copy import deepcopy
from typing import Any

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
from pyenphase.exceptions import EnvoyCommunicationError, EnvoyFeatureNotAvailable

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
async def test_update_generator_schedule(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify updating single and multiple generator schedule settings."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", VERSION)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    assert envoy.supported_features & SupportedFeatures.GENERATOR

    schedule_json = await load_json_fixture(VERSION, "ivp_ss_gen_schedule")
    full_host = endpoint_path(VERSION, envoy.host)

    # The Envoy replies with the resulting schedule
    expected = deepcopy(schedule_json)
    expected["exercise_config"]["day"] = "Mon"
    mock_aioresponse.post(
        f"{full_host}{URL_GEN_SCHEDULE}", status=200, payload=expected, repeat=True
    )

    # a single setting can be changed without passing the others
    result = await envoy.update_generator_schedule({"exercise_day": "mon"})

    _cnt, request_data = latest_request(mock_aioresponse, "POST", URL_GEN_SCHEDULE)
    assert orjson.loads(request_data) == expected

    # the reply is returned and used to update both raw and typed data
    assert result == expected
    assert envoy.data is not None
    assert envoy.data.raw[URL_GEN_SCHEDULE] == expected
    assert envoy.data.generator_schedule is not None
    assert envoy.data.generator_schedule.exercise_day == "Mon"
    # untouched settings keep their value
    assert (
        envoy.data.generator_schedule.exercise_start
        == schedule_json["exercise_config"]["start"]
    )
    assert (
        envoy.data.generator_schedule.default_start_soc
        == schedule_json["default_soc"]["start_soc"]
    )

    # all settings can still be changed in one go
    all_settings = deepcopy(expected)
    all_settings["exercise_config"] = {
        "freq_in_weeks": 2,
        "start": 840,
        "duration": 30,
        "day": "Sun",
    }
    all_settings["default_soc"] = {"start_soc": 35, "stop_soc": 75}
    override_mock(
        mock_aioresponse,
        "post",
        f"{full_host}{URL_GEN_SCHEDULE}",
        status=200,
        payload=all_settings,
        repeat=True,
    )
    await envoy.update_generator_schedule(
        {
            "exercise_freq_in_weeks": 2,
            "exercise_start": 840,
            "exercise_duration": 30,
            "exercise_day": "Sun",
            "default_start_soc": 35,
            "default_stop_soc": 75,
        }
    )
    _cnt, request_data = latest_request(mock_aioresponse, "POST", URL_GEN_SCHEDULE)
    assert orjson.loads(request_data) == all_settings
    assert envoy.data.generator_schedule.exercise_duration == 30
    assert envoy.data.generator_schedule.default_stop_soc == 75


@pytest.mark.asyncio
async def test_update_generator_schedule_twice_before_update(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify a second update builds on the first one, not on stale data."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", VERSION)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    schedule_json = await load_json_fixture(VERSION, "ivp_ss_gen_schedule")
    full_host = endpoint_path(VERSION, envoy.host)

    first = deepcopy(schedule_json)
    first["exercise_config"]["day"] = "Mon"
    mock_aioresponse.post(
        f"{full_host}{URL_GEN_SCHEDULE}", status=200, payload=first, repeat=True
    )
    await envoy.update_generator_schedule({"exercise_day": "Mon"})

    second = deepcopy(first)
    second["exercise_config"]["duration"] = 40
    override_mock(
        mock_aioresponse,
        "post",
        f"{full_host}{URL_GEN_SCHEDULE}",
        status=200,
        payload=second,
        repeat=True,
    )
    await envoy.update_generator_schedule({"exercise_duration": 40})

    # without an intermediate Envoy.update the second request must still
    # carry the day set by the first one
    _cnt, request_data = latest_request(mock_aioresponse, "POST", URL_GEN_SCHEDULE)
    sent = orjson.loads(request_data)
    assert sent["exercise_config"]["day"] == "Mon"
    assert sent["exercise_config"]["duration"] == 40
    assert sent == second


@pytest.mark.asyncio
async def test_update_generator_schedule_validation(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify generator schedule settings are validated before sending."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", VERSION)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)

    for invalid in (
        {"exercise_freq_in_weeks": 0},
        {"exercise_freq_in_weeks": 5},
        {"exercise_day": "Monday"},
        {"exercise_start": -1},
        {"exercise_start": 1440},
        {"exercise_duration": 5},
        {"exercise_duration": 65},
        # firmware accepts intermediate durations but Enlighten can not
        # display them, so the vendor step-10 domain is enforced
        {"exercise_duration": 25},
        {"default_start_soc": 101},
        {"default_stop_soc": -1},
        {"exercise_days": "Mon"},
        # the generator starts at the low SOC and stops at the high one
        {"default_start_soc": 80},
        {"default_stop_soc": 20},
        {"default_start_soc": 60, "default_stop_soc": 40},
        {"default_start_soc": 50, "default_stop_soc": 50},
    ):
        with pytest.raises(ValueError):
            await envoy.update_generator_schedule(invalid)

    # a valid pair is accepted, verified against the stored value for the
    # setting that is not changed
    assert envoy.data is not None
    assert envoy.data.generator_schedule is not None
    assert envoy.data.generator_schedule.default_stop_soc == 70
    validated = envoy._validated_generator_schedule(
        {"default_start_soc": 40}, envoy.data.generator_schedule
    )
    assert validated == {"default_start_soc": 40}

    # nothing was sent to the Envoy
    cnt, _data = latest_request(mock_aioresponse, "POST", URL_GEN_SCHEDULE)
    assert cnt == 0

    # updating before the first data update is rejected
    bad_envoy = await get_mock_envoy(test_client_session, update=False)
    await bad_envoy.probe()
    with pytest.raises(ValueError):
        await bad_envoy.update_generator_schedule({"exercise_duration": 20})


@pytest.mark.asyncio
async def test_set_generator_charge_from_generator(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify setting charge from generator sends the full configuration."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", VERSION)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    assert envoy.supported_features & SupportedFeatures.GENERATOR

    config_json = await load_json_fixture(VERSION, "ivp_ss_gen_config")
    assert config_json["charge_from_generator"] is True
    full_host = endpoint_path(VERSION, envoy.host)

    disabled = deepcopy(config_json)
    disabled["charge_from_generator"] = False
    mock_aioresponse.post(
        f"{full_host}{URL_GEN_CONFIG}", status=200, payload=disabled, repeat=True
    )

    result = await envoy.set_generator_charge_from_generator(False)

    # the whole configuration is sent with only the one field changed
    _cnt, request_data = latest_request(mock_aioresponse, "POST", URL_GEN_CONFIG)
    assert orjson.loads(request_data) == disabled

    assert result == disabled
    assert envoy.data is not None
    assert envoy.data.raw[URL_GEN_CONFIG] == disabled
    assert envoy.data.generator_config is not None
    assert envoy.data.generator_config.charge_from_generator is False

    # a system that normalizes the value back reports the effective value
    override_mock(
        mock_aioresponse,
        "post",
        f"{full_host}{URL_GEN_CONFIG}",
        status=200,
        payload=config_json,
        repeat=True,
    )
    result = await envoy.set_generator_charge_from_generator(False)
    assert result["charge_from_generator"] is True
    # re-read the stored config after the write rather than asserting on
    # envoy.data.generator_config again: the narrowing from the earlier
    # is False assertion sticks to that expression, which would make the
    # rest of this test statically unreachable
    effective_config = envoy.data.generator_config
    assert effective_config.charge_from_generator is True

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
        await envoy.update_generator_schedule({"exercise_duration": 20})
    with pytest.raises(EnvoyFeatureNotAvailable):
        await envoy.set_generator_charge_from_generator(True)


@pytest.mark.asyncio
async def test_update_generator_schedule_without_gen_schedule(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify the schedule update rejects firmware without the gen_schedule endpoint."""
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
        await envoy.update_generator_schedule({"exercise_duration": 20})


@pytest.mark.parametrize(
    ("reply", "reason"),
    [
        ([], "not a document"),
        ({}, "sentinel key missing"),
        ({"exercise_config": {"freq_in_weeks": 1}}, "document incomplete"),
    ],
    ids=["not_a_document", "sentinel_missing", "incomplete"],
)
@pytest.mark.asyncio
async def test_update_generator_schedule_incomplete_reply(
    reply: Any,
    reason: str,
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify stored data is kept if the Envoy returns no complete schedule."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", VERSION)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    schedule_json = await load_json_fixture(VERSION, "ivp_ss_gen_schedule")
    full_host = endpoint_path(VERSION, envoy.host)
    mock_aioresponse.post(
        f"{full_host}{URL_GEN_SCHEDULE}", status=200, payload=reply, repeat=True
    )

    with pytest.raises(EnvoyCommunicationError):
        await envoy.update_generator_schedule({"exercise_duration": 50})

    # data is left at the last known state, not at an optimistic one
    assert envoy.data is not None
    assert envoy.data.generator_schedule is not None
    assert (
        envoy.data.generator_schedule.exercise_duration
        == schedule_json["exercise_config"]["duration"]
    )
    assert envoy.data.raw[URL_GEN_SCHEDULE] == schedule_json


@pytest.mark.parametrize(
    ("reply", "reason"),
    [
        ([], "not a document"),
        ({}, "sentinel key missing"),
        ({"charge_from_generator": False}, "document incomplete"),
    ],
    ids=["not_a_document", "sentinel_missing", "incomplete"],
)
@pytest.mark.asyncio
async def test_set_generator_charge_from_generator_incomplete_reply(
    reply: Any,
    reason: str,
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify stored data is kept if the Envoy returns no complete configuration."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", VERSION)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    config_json = await load_json_fixture(VERSION, "ivp_ss_gen_config")
    full_host = endpoint_path(VERSION, envoy.host)
    mock_aioresponse.post(
        f"{full_host}{URL_GEN_CONFIG}", status=200, payload=reply, repeat=True
    )

    with pytest.raises(EnvoyCommunicationError):
        await envoy.set_generator_charge_from_generator(False)

    assert envoy.data is not None
    assert envoy.data.generator_config is not None
    assert envoy.data.generator_config.charge_from_generator is True
    assert envoy.data.raw[URL_GEN_CONFIG] == config_json


@pytest.mark.asyncio
async def test_generator_write_refresh(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify refresh re-reads the document before merging the changes."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", VERSION)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    schedule_json = await load_json_fixture(VERSION, "ivp_ss_gen_schedule")
    config_json = await load_json_fixture(VERSION, "ivp_ss_gen_config")
    full_host = endpoint_path(VERSION, envoy.host)

    # something else changed the SOC settings since the last data update
    changed = deepcopy(schedule_json)
    changed["default_soc"] = {"start_soc": 45, "stop_soc": 85}
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}{URL_GEN_SCHEDULE}",
        status=200,
        payload=changed,
        repeat=True,
    )
    sent_back = deepcopy(changed)
    sent_back["exercise_config"]["duration"] = 50
    mock_aioresponse.post(
        f"{full_host}{URL_GEN_SCHEDULE}", status=200, payload=sent_back, repeat=True
    )

    await envoy.update_generator_schedule({"exercise_duration": 50}, refresh=True)

    # the re-read values are sent, not the stale ones
    _cnt, request_data = latest_request(mock_aioresponse, "POST", URL_GEN_SCHEDULE)
    assert orjson.loads(request_data)["default_soc"] == {
        "start_soc": 45,
        "stop_soc": 85,
    }

    # same for the generator configuration
    changed_config = deepcopy(config_json)
    changed_config["warm_up_mins"] = 7
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}{URL_GEN_CONFIG}",
        status=200,
        payload=changed_config,
        repeat=True,
    )
    config_reply = deepcopy(changed_config)
    config_reply["charge_from_generator"] = False
    mock_aioresponse.post(
        f"{full_host}{URL_GEN_CONFIG}", status=200, payload=config_reply, repeat=True
    )

    await envoy.set_generator_charge_from_generator(False, refresh=True)

    _cnt, request_data = latest_request(mock_aioresponse, "POST", URL_GEN_CONFIG)
    assert orjson.loads(request_data)["warm_up_mins"] == 7


@pytest.mark.asyncio
async def test_generator_write_refresh_incomplete(
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify no update is sent if the refresh returns an incomplete document."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", VERSION)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    full_host = endpoint_path(VERSION, envoy.host)

    for path in (URL_GEN_SCHEDULE, URL_GEN_CONFIG):
        override_mock(
            mock_aioresponse,
            "get",
            f"{full_host}{path}",
            status=200,
            payload={"incomplete": True},
            repeat=True,
        )

    with pytest.raises(EnvoyCommunicationError):
        await envoy.update_generator_schedule({"exercise_duration": 50}, refresh=True)
    with pytest.raises(EnvoyCommunicationError):
        await envoy.set_generator_charge_from_generator(False, refresh=True)

    # nothing was sent
    cnt, _data = latest_request(mock_aioresponse, "POST", URL_GEN_SCHEDULE)
    assert cnt == 0
    cnt, _data = latest_request(mock_aioresponse, "POST", URL_GEN_CONFIG)
    assert cnt == 0
