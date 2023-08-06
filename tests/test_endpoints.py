from pathlib import Path
from typing import Any

import orjson
import pytest
import respx
from httpx import Response

from pyenphase import Envoy, EnvoyInverter
from pyenphase.envoy import SupportedFeatures


def _fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


def _load_fixture(version: str, name: str) -> str:
    with open(_fixtures_dir() / version / name) as read_in:
        return read_in.read()


def _load_json_fixture(version: str, name: str) -> dict[str, Any]:
    return orjson.loads(_load_fixture(version, name))


async def _get_mock_envoy():
    """Return a mock Envoy."""
    envoy = Envoy("127.0.0.1")
    await envoy.setup()
    await envoy.authenticate("username", "password")
    await envoy.update()
    return envoy


@pytest.mark.asyncio
@respx.mock
async def test_with_4_2_27_firmware():
    """Verify with 4.2.27 firmware."""
    version = "4.2.27"
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(return_value=Response(404))
    respx.get("/production.json").mock(
        return_value=Response(200, json=_load_json_fixture(version, "production.json"))
    )
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production")
        )
    )
    respx.get("/api/v1/production/inverters").mock(return_value=Response(404))
    envoy = await _get_mock_envoy()
    data = envoy.data
    assert data is not None

    assert not (envoy._supported_features & SupportedFeatures.METERING)
    assert not (envoy._supported_features & SupportedFeatures.INVERTERS)
    assert envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION
    assert envoy._supported_features & SupportedFeatures.NET_CONSUMPTION
    assert envoy._production_endpoint == "/api/v1/production"
    assert envoy._consumption_endpoint == "/production.json"

    assert data.system_consumption.watts_now == 5811
    assert (
        data.system_production.watts_now == 5894
    )  # This used to use the production.json endpoint, but its always a bit behind
    assert data.system_consumption.watt_hours_today == 0
    assert data.system_production.watt_hours_today == 17920
    assert data.system_consumption.watt_hours_last_7_days == 0
    assert data.system_production.watt_hours_last_7_days == 276614
    assert data.system_consumption.watt_hours_lifetime == 0
    assert data.system_production.watt_hours_lifetime == 10279087
    assert not data.inverters


@pytest.mark.asyncio
@respx.mock
async def test_with_5_0_49_firmware():
    """Verify with 5.0.49 firmware."""
    version = "5.0.49"
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(return_value=Response(404))
    respx.get("/production.json").mock(
        return_value=Response(200, json=_load_json_fixture(version, "production.json"))
    )
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production")
        )
    )
    respx.get("/api/v1/production/inverters").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production_inverters")
        )
    )
    respx.get("/ivp/ensemble/inventory").mock(return_value=Response(200, json=[]))

    envoy = await _get_mock_envoy()
    data = envoy.data
    assert data is not None

    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert envoy._production_endpoint == "/api/v1/production"
    assert envoy._consumption_endpoint is None

    assert not data.system_consumption
    assert data.system_production.watts_now == 4859
    assert data.system_production.watt_hours_today == 5046
    assert data.system_production.watt_hours_last_7_days == 445686
    assert data.system_production.watt_hours_lifetime == 88742152
    assert data.inverters == {
        "121547055830": EnvoyInverter(
            serial_number="121547055830",
            last_report_date=1618083280,
            last_report_watts=131,
            max_report_watts=257,
        ),
        "121547059008": EnvoyInverter(
            serial_number="121547059008",
            last_report_date=1618083240,
            last_report_watts=133,
            max_report_watts=257,
        ),
        "121547059079": EnvoyInverter(
            serial_number="121547059079",
            last_report_date=1618083244,
            last_report_watts=130,
            max_report_watts=257,
        ),
        "121547059102": EnvoyInverter(
            serial_number="121547059102",
            last_report_date=1618083273,
            last_report_watts=134,
            max_report_watts=257,
        ),
        "121547059107": EnvoyInverter(
            serial_number="121547059107",
            last_report_date=1618083265,
            last_report_watts=132,
            max_report_watts=257,
        ),
        "121547059108": EnvoyInverter(
            serial_number="121547059108",
            last_report_date=1618083266,
            last_report_watts=131,
            max_report_watts=257,
        ),
        "121547059112": EnvoyInverter(
            serial_number="121547059112",
            last_report_date=1618083286,
            last_report_watts=132,
            max_report_watts=257,
        ),
        "121547059128": EnvoyInverter(
            serial_number="121547059128",
            last_report_date=1618083262,
            last_report_watts=135,
            max_report_watts=257,
        ),
        "121547059193": EnvoyInverter(
            serial_number="121547059193",
            last_report_date=1618083250,
            last_report_watts=131,
            max_report_watts=257,
        ),
        "121547059202": EnvoyInverter(
            serial_number="121547059202",
            last_report_date=1618083251,
            last_report_watts=133,
            max_report_watts=257,
        ),
        "121547059217": EnvoyInverter(
            serial_number="121547059217",
            last_report_date=1618083281,
            last_report_watts=137,
            max_report_watts=257,
        ),
        "121547059253": EnvoyInverter(
            serial_number="121547059253",
            last_report_date=1618083289,
            last_report_watts=131,
            max_report_watts=257,
        ),
        "121547059333": EnvoyInverter(
            serial_number="121547059333",
            last_report_date=1618083277,
            last_report_watts=134,
            max_report_watts=257,
        ),
        "121547059354": EnvoyInverter(
            serial_number="121547059354",
            last_report_date=1618083287,
            last_report_watts=132,
            max_report_watts=257,
        ),
        "121547059355": EnvoyInverter(
            serial_number="121547059355",
            last_report_date=1618083263,
            last_report_watts=131,
            max_report_watts=258,
        ),
        "121547059357": EnvoyInverter(
            serial_number="121547059357",
            last_report_date=1618083254,
            last_report_watts=133,
            max_report_watts=257,
        ),
        "121547059359": EnvoyInverter(
            serial_number="121547059359",
            last_report_date=1618083247,
            last_report_watts=134,
            max_report_watts=257,
        ),
        "121547059360": EnvoyInverter(
            serial_number="121547059360",
            last_report_date=1618083245,
            last_report_watts=131,
            max_report_watts=257,
        ),
        "121547059363": EnvoyInverter(
            serial_number="121547059363",
            last_report_date=1618083255,
            last_report_watts=131,
            max_report_watts=257,
        ),
        "121547059381": EnvoyInverter(
            serial_number="121547059381",
            last_report_date=1618083259,
            last_report_watts=132,
            max_report_watts=257,
        ),
        "121547059889": EnvoyInverter(
            serial_number="121547059889",
            last_report_date=1618083264,
            last_report_watts=133,
            max_report_watts=257,
        ),
        "121547060383": EnvoyInverter(
            serial_number="121547060383",
            last_report_date=1618083257,
            last_report_watts=135,
            max_report_watts=258,
        ),
        "121547060384": EnvoyInverter(
            serial_number="121547060384",
            last_report_date=1618083250,
            last_report_watts=134,
            max_report_watts=257,
        ),
        "121547060392": EnvoyInverter(
            serial_number="121547060392",
            last_report_date=1618083288,
            last_report_watts=133,
            max_report_watts=257,
        ),
        "121547060396": EnvoyInverter(
            serial_number="121547060396",
            last_report_date=1618083269,
            last_report_watts=133,
            max_report_watts=257,
        ),
        "121547060412": EnvoyInverter(
            serial_number="121547060412",
            last_report_date=1618083258,
            last_report_watts=131,
            max_report_watts=257,
        ),
        "121547060415": EnvoyInverter(
            serial_number="121547060415",
            last_report_date=1618083267,
            last_report_watts=133,
            max_report_watts=257,
        ),
        "121547060590": EnvoyInverter(
            serial_number="121547060590",
            last_report_date=1618083277,
            last_report_watts=133,
            max_report_watts=257,
        ),
        "121547060592": EnvoyInverter(
            serial_number="121547060592",
            last_report_date=1618083279,
            last_report_watts=133,
            max_report_watts=257,
        ),
        "121547060593": EnvoyInverter(
            serial_number="121547060593",
            last_report_date=1618083271,
            last_report_watts=133,
            max_report_watts=257,
        ),
        "121547060643": EnvoyInverter(
            serial_number="121547060643",
            last_report_date=1618083284,
            last_report_watts=131,
            max_report_watts=257,
        ),
        "121547060647": EnvoyInverter(
            serial_number="121547060647",
            last_report_date=1618083285,
            last_report_watts=134,
            max_report_watts=258,
        ),
        "121547060650": EnvoyInverter(
            serial_number="121547060650",
            last_report_date=1618083253,
            last_report_watts=131,
            max_report_watts=257,
        ),
        "121547060670": EnvoyInverter(
            serial_number="121547060670",
            last_report_date=1618083270,
            last_report_watts=134,
            max_report_watts=257,
        ),
        "121547060671": EnvoyInverter(
            serial_number="121547060671",
            last_report_date=1618083283,
            last_report_watts=135,
            max_report_watts=257,
        ),
        "121547060727": EnvoyInverter(
            serial_number="121547060727",
            last_report_date=1618083275,
            last_report_watts=134,
            max_report_watts=257,
        ),
        "121547060758": EnvoyInverter(
            serial_number="121547060758",
            last_report_date=1618083274,
            last_report_watts=130,
            max_report_watts=255,
        ),
        "121547060761": EnvoyInverter(
            serial_number="121547060761",
            last_report_date=1618083260,
            last_report_watts=133,
            max_report_watts=257,
        ),
        "121547060766": EnvoyInverter(
            serial_number="121547060766",
            last_report_date=1618083242,
            last_report_watts=132,
            max_report_watts=257,
        ),
        "121547060773": EnvoyInverter(
            serial_number="121547060773",
            last_report_date=1618083247,
            last_report_watts=132,
            max_report_watts=257,
        ),
    }


@pytest.mark.asyncio
@respx.mock
async def test_with_3_9_36_firmware():
    """Verify with 3.9.36 firmware."""
    version = "3.9.36"
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(return_value=Response(404))
    respx.get("/production.json").mock(return_value=Response(404))
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production")
        )
    )
    respx.get("/api/v1/production/inverters").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production_inverters")
        )
    )
    respx.get("/ivp/ensemble/inventory").mock(return_value=Response(200, json=[]))

    envoy = await _get_mock_envoy()
    data = envoy.data
    assert data is not None

    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert envoy._production_endpoint == "/api/v1/production"
    assert envoy._consumption_endpoint is None

    assert not data.system_consumption
    assert data.system_production.watts_now == 1271
    assert data.system_production.watt_hours_today == 1460
    assert data.system_production.watt_hours_last_7_days == 130349
    assert data.system_production.watt_hours_lifetime == 6012540
    assert data.inverters == {
        "121547058983": EnvoyInverter(
            serial_number="121547058983",
            last_report_date=1618083969,
            last_report_watts=137,
            max_report_watts=238,
        ),
        "121547058993": EnvoyInverter(
            serial_number="121547058993",
            last_report_date=1618083961,
            last_report_watts=138,
            max_report_watts=231,
        ),
        "121547060394": EnvoyInverter(
            serial_number="121547060394",
            last_report_date=1618083966,
            last_report_watts=138,
            max_report_watts=238,
        ),
        "121547060402": EnvoyInverter(
            serial_number="121547060402",
            last_report_date=1618083962,
            last_report_watts=138,
            max_report_watts=240,
        ),
        "121547060495": EnvoyInverter(
            serial_number="121547060495",
            last_report_date=1618083959,
            last_report_watts=135,
            max_report_watts=228,
        ),
        "121547060638": EnvoyInverter(
            serial_number="121547060638",
            last_report_date=1618083966,
            last_report_watts=139,
            max_report_watts=241,
        ),
        "121547060646": EnvoyInverter(
            serial_number="121547060646",
            last_report_date=1618083957,
            last_report_watts=139,
            max_report_watts=240,
        ),
        "121547060652": EnvoyInverter(
            serial_number="121547060652",
            last_report_date=1618083959,
            last_report_watts=140,
            max_report_watts=245,
        ),
        "121603025842": EnvoyInverter(
            serial_number="121603025842",
            last_report_date=1618083963,
            last_report_watts=139,
            max_report_watts=260,
        ),
        "121603034267": EnvoyInverter(
            serial_number="121603034267",
            last_report_date=1618083956,
            last_report_watts=138,
            max_report_watts=244,
        ),
        "121603038867": EnvoyInverter(
            serial_number="121603038867",
            last_report_date=1618083964,
            last_report_watts=138,
            max_report_watts=242,
        ),
        "121603039216": EnvoyInverter(
            serial_number="121603039216",
            last_report_date=1618083968,
            last_report_watts=139,
            max_report_watts=273,
        ),
    }


@pytest.mark.asyncio
@respx.mock
async def test_with_3_17_3_firmware():
    """Verify with 3.17.3 firmware."""
    version = "3.17.3"
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(return_value=Response(404))
    respx.get("/production.json").mock(return_value=Response(404))
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production")
        )
    )
    respx.get("/api/v1/production/inverters").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production_inverters")
        )
    )
    respx.get("/ivp/ensemble/inventory").mock(return_value=Response(200, json=[]))

    envoy = await _get_mock_envoy()
    data = envoy.data
    assert data is not None

    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert envoy._production_endpoint == "/api/v1/production"
    assert envoy._consumption_endpoint is None

    assert not data.system_consumption
    assert data.system_production.watts_now == 5463
    assert data.system_production.watt_hours_today == 5481
    assert data.system_production.watt_hours_last_7_days == 389581
    assert data.system_production.watt_hours_lifetime == 93706280
    assert data.inverters == {
        "121512006273": EnvoyInverter(
            serial_number="121512006273",
            last_report_date=1618082959,
            last_report_watts=206,
            max_report_watts=254,
        ),
        "121512009183": EnvoyInverter(
            serial_number="121512009183",
            last_report_date=1618082961,
            last_report_watts=204,
            max_report_watts=253,
        ),
        "121512033008": EnvoyInverter(
            serial_number="121512033008",
            last_report_date=1618082947,
            last_report_watts=101,
            max_report_watts=243,
        ),
        "121512036220": EnvoyInverter(
            serial_number="121512036220",
            last_report_date=1618082927,
            last_report_watts=198,
            max_report_watts=245,
        ),
        "121512036221": EnvoyInverter(
            serial_number="121512036221",
            last_report_date=1618082963,
            last_report_watts=8,
            max_report_watts=116,
        ),
        "121512036250": EnvoyInverter(
            serial_number="121512036250",
            last_report_date=1618082940,
            last_report_watts=20,
            max_report_watts=190,
        ),
        "121512036336": EnvoyInverter(
            serial_number="121512036336",
            last_report_date=1618082932,
            last_report_watts=199,
            max_report_watts=247,
        ),
        "121512037453": EnvoyInverter(
            serial_number="121512037453",
            last_report_date=1618082949,
            last_report_watts=205,
            max_report_watts=255,
        ),
        "121512038416": EnvoyInverter(
            serial_number="121512038416",
            last_report_date=1618082953,
            last_report_watts=151,
            max_report_watts=251,
        ),
        "121512038421": EnvoyInverter(
            serial_number="121512038421",
            last_report_date=1618082949,
            last_report_watts=14,
            max_report_watts=233,
        ),
        "121512038619": EnvoyInverter(
            serial_number="121512038619",
            last_report_date=1618082962,
            last_report_watts=203,
            max_report_watts=252,
        ),
        "121512038691": EnvoyInverter(
            serial_number="121512038691",
            last_report_date=1618082942,
            last_report_watts=26,
            max_report_watts=247,
        ),
        "121512038762": EnvoyInverter(
            serial_number="121512038762",
            last_report_date=1618082930,
            last_report_watts=203,
            max_report_watts=253,
        ),
        "121512038845": EnvoyInverter(
            serial_number="121512038845",
            last_report_date=1618082945,
            last_report_watts=203,
            max_report_watts=253,
        ),
        "121512038901": EnvoyInverter(
            serial_number="121512038901",
            last_report_date=1618082944,
            last_report_watts=102,
            max_report_watts=245,
        ),
        "121512038919": EnvoyInverter(
            serial_number="121512038919",
            last_report_date=1618082959,
            last_report_watts=102,
            max_report_watts=238,
        ),
        "121512038982": EnvoyInverter(
            serial_number="121512038982",
            last_report_date=1618082950,
            last_report_watts=203,
            max_report_watts=253,
        ),
        "121512039005": EnvoyInverter(
            serial_number="121512039005",
            last_report_date=1618082933,
            last_report_watts=55,
            max_report_watts=254,
        ),
        "121512039018": EnvoyInverter(
            serial_number="121512039018",
            last_report_date=1618082964,
            last_report_watts=27,
            max_report_watts=252,
        ),
        "121512039075": EnvoyInverter(
            serial_number="121512039075",
            last_report_date=1618082930,
            last_report_watts=102,
            max_report_watts=237,
        ),
        "121512039090": EnvoyInverter(
            serial_number="121512039090",
            last_report_date=1618082946,
            last_report_watts=32,
            max_report_watts=194,
        ),
        "121512039091": EnvoyInverter(
            serial_number="121512039091",
            last_report_date=1618082939,
            last_report_watts=27,
            max_report_watts=252,
        ),
        "121512039093": EnvoyInverter(
            serial_number="121512039093",
            last_report_date=1618082966,
            last_report_watts=209,
            max_report_watts=256,
        ),
        "121512039124": EnvoyInverter(
            serial_number="121512039124",
            last_report_date=1618082938,
            last_report_watts=205,
            max_report_watts=254,
        ),
        "121512039143": EnvoyInverter(
            serial_number="121512039143",
            last_report_date=1618082956,
            last_report_watts=104,
            max_report_watts=245,
        ),
        "121512039181": EnvoyInverter(
            serial_number="121512039181",
            last_report_date=1618082943,
            last_report_watts=101,
            max_report_watts=238,
        ),
        "121512041456": EnvoyInverter(
            serial_number="121512041456",
            last_report_date=1618082937,
            last_report_watts=13,
            max_report_watts=79,
        ),
        "121512041640": EnvoyInverter(
            serial_number="121512041640",
            last_report_date=1618082927,
            last_report_watts=200,
            max_report_watts=249,
        ),
        "121512041747": EnvoyInverter(
            serial_number="121512041747",
            last_report_date=1618082925,
            last_report_watts=64,
            max_report_watts=248,
        ),
        "121512042132": EnvoyInverter(
            serial_number="121512042132",
            last_report_date=1618082924,
            last_report_watts=200,
            max_report_watts=250,
        ),
        "121512042344": EnvoyInverter(
            serial_number="121512042344",
            last_report_date=1618082952,
            last_report_watts=205,
            max_report_watts=253,
        ),
        "121512043086": EnvoyInverter(
            serial_number="121512043086",
            last_report_date=1618082942,
            last_report_watts=202,
            max_report_watts=250,
        ),
        "121512043093": EnvoyInverter(
            serial_number="121512043093",
            last_report_date=1618082928,
            last_report_watts=208,
            max_report_watts=255,
        ),
        "121512043135": EnvoyInverter(
            serial_number="121512043135",
            last_report_date=1618082923,
            last_report_watts=205,
            max_report_watts=254,
        ),
        "121512043153": EnvoyInverter(
            serial_number="121512043153",
            last_report_date=1618082935,
            last_report_watts=18,
            max_report_watts=146,
        ),
        "121512043173": EnvoyInverter(
            serial_number="121512043173",
            last_report_date=1618082966,
            last_report_watts=200,
            max_report_watts=247,
        ),
        "121512043200": EnvoyInverter(
            serial_number="121512043200",
            last_report_date=1618082955,
            last_report_watts=203,
            max_report_watts=253,
        ),
        "121512043222": EnvoyInverter(
            serial_number="121512043222",
            last_report_date=1618082957,
            last_report_watts=207,
            max_report_watts=254,
        ),
        "121512043574": EnvoyInverter(
            serial_number="121512043574",
            last_report_date=1618082936,
            last_report_watts=203,
            max_report_watts=253,
        ),
        "121512043587": EnvoyInverter(
            serial_number="121512043587",
            last_report_date=1618082934,
            last_report_watts=202,
            max_report_watts=253,
        ),
        "121512044424": EnvoyInverter(
            serial_number="121512044424",
            last_report_date=1618082954,
            last_report_watts=106,
            max_report_watts=239,
        ),
    }


@pytest.mark.asyncio
@respx.mock
async def test_with_7_3_130_firmware():
    """Verify with 7.3.130 firmware."""
    version = "7.3.130"
    respx.post("https://enlighten.enphaseenergy.com/login/login.json?").mock(
        return_value=Response(
            200,
            json={
                "session_id": "1234567890",
                "user_id": "1234567890",
                "user_name": "test",
                "first_name": "Test",
                "is_consumer": True,
                "manager_token": "1234567890",
            },
        )
    )
    respx.post("https://entrez.enphaseenergy.com/tokens").mock(
        return_value=Response(200, text="token")
    )
    respx.get("/auth/check_jwt").mock(return_value=Response(200, json={}))
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(
        return_value=Response(200, json=_load_json_fixture(version, "production"))
    )
    respx.get("/production.json").mock(
        return_value=Response(200, json=_load_json_fixture(version, "production.json"))
    )
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production")
        )
    )
    respx.get("/api/v1/production/inverters").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production_inverters")
        )
    )
    respx.get("/ivp/ensemble/inventory").mock(return_value=Response(200, json=[]))

    envoy = await _get_mock_envoy()
    data = envoy.data
    assert data is not None

    assert envoy._production_endpoint == "/production"
    assert envoy._consumption_endpoint == "/production"
    assert envoy._supported_features & SupportedFeatures.METERING
    assert envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION
    assert envoy._supported_features & SupportedFeatures.NET_CONSUMPTION
    assert envoy._supported_features & SupportedFeatures.INVERTERS

    assert data.system_consumption.watts_now == 1488
    assert data.system_consumption.watt_hours_today == 15181
    assert data.system_consumption.watt_hours_last_7_days == 365477
    assert data.system_consumption.watt_hours_lifetime == 10154384
    assert data.system_production.watts_now == 180
    assert data.system_production.watt_hours_today == 87
    assert data.system_production.watt_hours_last_7_days == 149973
    assert data.system_production.watt_hours_lifetime == 3659507
    assert data.inverters == {
        "202218023114": EnvoyInverter(
            serial_number="202218023114",
            last_report_date=1691342554,
            last_report_watts=14,
            max_report_watts=346,
        ),
        "202218024705": EnvoyInverter(
            serial_number="202218024705",
            last_report_date=1691342553,
            last_report_watts=8,
            max_report_watts=345,
        ),
        "202218025399": EnvoyInverter(
            serial_number="202218025399",
            last_report_date=1691342465,
            last_report_watts=10,
            max_report_watts=350,
        ),
        "202218026521": EnvoyInverter(
            serial_number="202218026521",
            last_report_date=1691342464,
            last_report_watts=9,
            max_report_watts=347,
        ),
        "202218028926": EnvoyInverter(
            serial_number="202218028926",
            last_report_date=1691342462,
            last_report_watts=17,
            max_report_watts=346,
        ),
        "202218029586": EnvoyInverter(
            serial_number="202218029586",
            last_report_date=1691342643,
            last_report_watts=12,
            max_report_watts=347,
        ),
        "202218031593": EnvoyInverter(
            serial_number="202218031593",
            last_report_date=1691342674,
            last_report_watts=20,
            max_report_watts=348,
        ),
        "202218034002": EnvoyInverter(
            serial_number="202218034002",
            last_report_date=1691342555,
            last_report_watts=14,
            max_report_watts=345,
        ),
        "202218035988": EnvoyInverter(
            serial_number="202218035988",
            last_report_date=1691342613,
            last_report_watts=17,
            max_report_watts=348,
        ),
        "202218036214": EnvoyInverter(
            serial_number="202218036214",
            last_report_date=1691342432,
            last_report_watts=13,
            max_report_watts=347,
        ),
        "202218036386": EnvoyInverter(
            serial_number="202218036386",
            last_report_date=1691342584,
            last_report_watts=9,
            max_report_watts=346,
        ),
        "202218037990": EnvoyInverter(
            serial_number="202218037990",
            last_report_date=1691342525,
            last_report_watts=16,
            max_report_watts=348,
        ),
    }


@pytest.mark.asyncio
@respx.mock
async def test_with_7_6_175_firmware():
    """Verify with 7.6.175 firmware."""
    version = "7.6.175"
    respx.post("https://enlighten.enphaseenergy.com/login/login.json?").mock(
        return_value=Response(
            200,
            json={
                "session_id": "1234567890",
                "user_id": "1234567890",
                "user_name": "test",
                "first_name": "Test",
                "is_consumer": True,
                "manager_token": "1234567890",
            },
        )
    )
    respx.post("https://entrez.enphaseenergy.com/tokens").mock(
        return_value=Response(200, text="token")
    )
    respx.get("/auth/check_jwt").mock(return_value=Response(200, json={}))
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(
        return_value=Response(200, json=_load_json_fixture(version, "production"))
    )
    respx.get("/production.json").mock(
        return_value=Response(200, json=_load_json_fixture(version, "production.json"))
    )
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production")
        )
    )
    respx.get("/api/v1/production/inverters").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production_inverters")
        )
    )
    respx.get("/ivp/ensemble/inventory").mock(return_value=Response(200, json=[]))

    envoy = await _get_mock_envoy()
    data = envoy.data
    assert data is not None

    assert envoy._production_endpoint == "/api/v1/production"
    assert envoy._consumption_endpoint is None
    assert not (envoy._supported_features & SupportedFeatures.METERING)
    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert envoy._supported_features & SupportedFeatures.INVERTERS

    assert data.system_consumption is None
    assert data.system_production.watts_now == 3391
    assert data.system_production.watt_hours_today == 7883
    assert data.system_production.watt_hours_last_7_days == 107011
    assert data.system_production.watt_hours_lifetime == 8717473
    assert data.inverters == {
        "122146075749": EnvoyInverter(
            serial_number="122146075749",
            last_report_date=1691318584,
            last_report_watts=270,
            max_report_watts=296,
        ),
        "122146076029": EnvoyInverter(
            serial_number="122146076029",
            last_report_date=1691318494,
            last_report_watts=281,
            max_report_watts=297,
        ),
        "122146076125": EnvoyInverter(
            serial_number="122146076125",
            last_report_date=1691318704,
            last_report_watts=229,
            max_report_watts=297,
        ),
        "122146076128": EnvoyInverter(
            serial_number="122146076128",
            last_report_date=1691318674,
            last_report_watts=245,
            max_report_watts=297,
        ),
        "122146076272": EnvoyInverter(
            serial_number="122146076272",
            last_report_date=1691318672,
            last_report_watts=243,
            max_report_watts=297,
        ),
        "122146076336": EnvoyInverter(
            serial_number="122146076336",
            last_report_date=1691318523,
            last_report_watts=275,
            max_report_watts=296,
        ),
        "122146076488": EnvoyInverter(
            serial_number="122146076488",
            last_report_date=1691318612,
            last_report_watts=260,
            max_report_watts=297,
        ),
        "122146076492": EnvoyInverter(
            serial_number="122146076492",
            last_report_date=1691318556,
            last_report_watts=273,
            max_report_watts=297,
        ),
        "122146076500": EnvoyInverter(
            serial_number="122146076500",
            last_report_date=1691318613,
            last_report_watts=259,
            max_report_watts=297,
        ),
        "122146076518": EnvoyInverter(
            serial_number="122146076518",
            last_report_date=1691318462,
            last_report_watts=290,
            max_report_watts=297,
        ),
        "122146076618": EnvoyInverter(
            serial_number="122146076618",
            last_report_date=1691318643,
            last_report_watts=250,
            max_report_watts=297,
        ),
        "122146078718": EnvoyInverter(
            serial_number="122146078718",
            last_report_date=1691318583,
            last_report_watts=273,
            max_report_watts=297,
        ),
        "122146078769": EnvoyInverter(
            serial_number="122146078769",
            last_report_date=1691318673,
            last_report_watts=243,
            max_report_watts=297,
        ),
    }


@pytest.mark.asyncio
@respx.mock
async def test_with_7_3_517_firmware():
    """Verify with 7.3.517 firmware."""
    version = "7.3.517"
    respx.post("https://enlighten.enphaseenergy.com/login/login.json?").mock(
        return_value=Response(
            200,
            json={
                "session_id": "1234567890",
                "user_id": "1234567890",
                "user_name": "test",
                "first_name": "Test",
                "is_consumer": True,
                "manager_token": "1234567890",
            },
        )
    )
    respx.post("https://entrez.enphaseenergy.com/tokens").mock(
        return_value=Response(200, text="token")
    )
    respx.get("/auth/check_jwt").mock(return_value=Response(200, json={}))
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(
        return_value=Response(200, json=_load_json_fixture(version, "production"))
    )
    respx.get("/production.json").mock(
        return_value=Response(200, json=_load_json_fixture(version, "production.json"))
    )
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production")
        )
    )
    respx.get("/api/v1/production/inverters").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production_inverters")
        )
    )
    respx.get("/ivp/ensemble/dry_contacts").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "ivp_ensemble_dry_contacts")
        )
    )
    respx.get("/ivp/ss/dry_contacts_settings").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "ivp_ss_dry_contact_settings")
        )
    )
    respx.get("/ivp/ensemble/inventory").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "ivp_ensemble_inventory")
        )
    )
    respx.get("/ivp/ensemble/power").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "ivp_ensemble_power")
        )
    )
    envoy = await _get_mock_envoy()
    data = envoy.data
    assert data is not None

    assert envoy._production_endpoint == "/production"
    assert envoy._consumption_endpoint == "/production"
    assert envoy._supported_features & SupportedFeatures.METERING
    assert envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION
    assert envoy._supported_features & SupportedFeatures.NET_CONSUMPTION
    assert envoy._supported_features & SupportedFeatures.INVERTERS

    assert data.system_consumption.watts_now == 2636
    assert data.system_consumption.watt_hours_today == 28106
    assert data.system_consumption.watt_hours_last_7_days == 433
    assert data.system_consumption.watt_hours_lifetime == 26869751
    assert data.system_production.watts_now == 1927
    assert data.system_production.watt_hours_today == 5460
    assert data.system_production.watt_hours_last_7_days == 217064
    assert data.system_production.watt_hours_lifetime == 18774214
    assert data.inverters == {
        "555555001326": EnvoyInverter(
            serial_number="555555001326",
            last_report_date=1691347968,
            last_report_watts=66,
            max_report_watts=245,
        ),
        "555555001781": EnvoyInverter(
            serial_number="555555001781",
            last_report_date=1691348028,
            last_report_watts=80,
            max_report_watts=245,
        ),
        "555555002877": EnvoyInverter(
            serial_number="555555002877",
            last_report_date=1691347908,
            last_report_watts=92,
            max_report_watts=246,
        ),
        "555555003467": EnvoyInverter(
            serial_number="555555003467",
            last_report_date=1691347938,
            last_report_watts=95,
            max_report_watts=246,
        ),
        "555555003473": EnvoyInverter(
            serial_number="555555003473",
            last_report_date=1691347757,
            last_report_watts=80,
            max_report_watts=246,
        ),
        "555555003484": EnvoyInverter(
            serial_number="555555003484",
            last_report_date=1691347848,
            last_report_watts=75,
            max_report_watts=245,
        ),
        "555555003803": EnvoyInverter(
            serial_number="555555003803",
            last_report_date=1691347997,
            last_report_watts=98,
            max_report_watts=247,
        ),
    }
