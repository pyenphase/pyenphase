"""Test Envoy options."""

import logging
from typing import Any

import aiohttp
import pytest
from aioresponses import aioresponses

from pyenphase.const import URL_PRODUCTION, URL_PRODUCTION_JSON, URL_PRODUCTION_V1
from pyenphase.envoy import EnvoyData, EnvoyOptions, EnvoyProbeFailed, SupportedFeatures

from .common import (
    endpoint_fixture_file,
    endpoint_path,
    get_mock_envoy,
    load_json_fixture,
    override_mock,
    prep_envoy,
    start_7_firmware_mock,
)

LOGGER = logging.getLogger(__name__)


def assert_api_v1(
    envoy_data: EnvoyData, json_data: dict[str, Any], present: bool
) -> None:
    """Assert /api/v1/production data."""
    assert envoy_data
    assert "/production.json?details=1" not in envoy_data.raw
    assert "/production.json" not in envoy_data.raw
    assert "/production" not in envoy_data.raw
    if present:
        assert URL_PRODUCTION_V1 in envoy_data.raw
        assert envoy_data.system_production
        assert envoy_data.system_production.watts_now == round(json_data["wattsNow"], 0)
        assert envoy_data.system_production.watt_hours_today == round(
            json_data["wattHoursToday"], 0
        )
        assert envoy_data.system_production.watt_hours_last_7_days == round(
            json_data["wattHoursSevenDays"], 0
        )
        assert envoy_data.system_production.watt_hours_lifetime == round(
            json_data["wattHoursLifetime"], 0
        )
    else:
        assert URL_PRODUCTION_V1 not in envoy_data.raw
        assert envoy_data.system_production is None
        assert envoy_data.system_consumption is None
        assert envoy_data.system_net_consumption is None


@pytest.mark.parametrize(
    ("version"),
    [
        "8.3.5169_ACB_inventory",
    ],
    ids=[
        "no_solar",
    ],
)
@pytest.mark.asyncio
async def test_envoy_no_solar_option(
    version: str,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Test NO_SOLAR envoy_options."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    full_host = endpoint_path(version, "127.0.0.1")

    # test standard mode with production data
    envoy = await get_mock_envoy(test_client_session, v2_acb_mode=False)

    data = envoy.data
    assert data
    assert URL_PRODUCTION_JSON in data.raw
    assert URL_PRODUCTION_V1 not in data.raw
    assert SupportedFeatures.PRODUCTION in envoy.supported_features

    prod_json = await load_json_fixture(
        version, endpoint_fixture_file(URL_PRODUCTION_JSON)
    )
    assert data.system_production
    assert data.system_production.watts_now == round(
        prod_json["production"][1]["wNow"], 0
    )
    assert data.system_production.watt_hours_today == round(
        prod_json["production"][1]["whToday"], 0
    )
    assert data.system_production.watt_hours_last_7_days == round(
        prod_json["production"][1]["whLastSevenDays"], 0
    )
    assert data.system_production.watt_hours_lifetime == round(
        prod_json["production"][1]["whLifetime"], 0
    )

    # If no /production then verify fallback to /api/v1/production
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}{URL_PRODUCTION_JSON}",
        status=404,
        payload=None,
        repeat=True,
    )
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}{URL_PRODUCTION}",
        status=404,
        payload=None,
        repeat=True,
    )

    await envoy.probe()
    data = await envoy.update()
    assert data
    v1_prod_json = await load_json_fixture(
        version, endpoint_fixture_file(URL_PRODUCTION_V1)
    )
    assert_api_v1(data, v1_prod_json, present=True)

    # Without any production endpoint probe will raise
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}{URL_PRODUCTION_V1}",
        status=404,
        payload=None,
        repeat=True,
    )
    with pytest.raises(EnvoyProbeFailed):
        await envoy.probe()

    # In NO_SOLAR mode it can run without /production and /api/v1/production
    envoy = await get_mock_envoy(
        test_client_session,
        v2_acb_mode=False,
        envoy_options=EnvoyOptions.NO_SOLAR,
    )

    data = envoy.data
    assert data
    assert SupportedFeatures.PRODUCTION not in envoy.supported_features
    assert_api_v1(data, v1_prod_json, present=False)

    # typically /api/v1/production will reply for no_solar envoy
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}{URL_PRODUCTION_V1}",
        status=200,
        payload=v1_prod_json,
        repeat=True,
    )

    await envoy.probe()
    data = await envoy.update()
    assert data
    assert SupportedFeatures.PRODUCTION in envoy.supported_features
    assert_api_v1(data, v1_prod_json, present=True)

    # Even if /production endpoint would reply, it will be ignored in NO_SOLAR mode
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}{URL_PRODUCTION_JSON}",
        status=200,
        payload=prod_json,
        repeat=True,
    )
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}{URL_PRODUCTION}",
        status=200,
        payload=prod_json,
        repeat=True,
    )
    override_mock(
        mock_aioresponse,
        "get",
        f"{full_host}{URL_PRODUCTION_V1}",
        status=404,
        payload=None,
        repeat=True,
    )
    await envoy.probe()
    data = await envoy.update()
    assert data
    assert SupportedFeatures.PRODUCTION not in envoy.supported_features
    assert_api_v1(data, v1_prod_json, present=False)

    # verify /production was actually mocked in previous test
    request_result = await envoy._json_request(URL_PRODUCTION_JSON, None)
    assert request_result == prod_json
