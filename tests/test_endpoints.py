import logging
import re
from dataclasses import replace
from os import listdir
from os.path import isfile, join
from pathlib import Path
from typing import Any

import orjson
import pytest
import respx
from httpx import Response
from syrupy import SnapshotAssertion

from pyenphase import Envoy, EnvoyInverter, register_updater
from pyenphase.const import URL_GRID_RELAY, URL_PRODUCTION
from pyenphase.envoy import SupportedFeatures, get_updaters
from pyenphase.exceptions import (
    ENDPOINT_PROBE_EXCEPTIONS,
    EnvoyAuthenticationRequired,
    EnvoyFeatureNotAvailable,
    EnvoyProbeFailed,
)
from pyenphase.models.dry_contacts import DryContactStatus
from pyenphase.models.envoy import EnvoyData
from pyenphase.models.system_production import EnvoySystemProduction
from pyenphase.updaters.base import EnvoyUpdater

LOGGER = logging.getLogger(__name__)


def _fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


def _load_fixture(version: str, name: str) -> str:
    with open(_fixtures_dir() / version / name) as read_in:
        return read_in.read()


def _load_json_fixture(version: str, name: str) -> dict[str, Any]:
    return orjson.loads(_load_fixture(version, name))


def _updater_features(updaters: list[EnvoyUpdater]) -> dict[str, SupportedFeatures]:
    return {type(updater).__name__: updater._supported_features for updater in updaters}


async def _get_mock_envoy(update: bool = True):  # type: ignore[no-untyped-def]
    """Return a mock Envoy."""
    envoy = Envoy("127.0.0.1")
    await envoy.setup()
    await envoy.authenticate("username", "password")
    if update:
        await envoy.update()
        await envoy.update()  # make sure we can update twice
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
    assert _updater_features(envoy._updaters) == {
        "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
        "EnvoyProductionJsonUpdater": SupportedFeatures.TOTAL_CONSUMPTION
        | SupportedFeatures.NET_CONSUMPTION,
    }
    assert envoy.part_number == "800-00551-r02"

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

    # Test that Ensemble commands raise FeatureNotAvailable
    with pytest.raises(EnvoyFeatureNotAvailable):
        await envoy.go_off_grid()
    with pytest.raises(EnvoyFeatureNotAvailable):
        await envoy.go_on_grid()


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
    assert _updater_features(envoy._updaters) == {
        "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
        "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
    }
    assert envoy.part_number == "800-00551-r02"

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
async def test_with_3_7_0_firmware():
    """Verify with 3.7.0 firmware."""
    version = "3.7.0"
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(
        return_value=Response(200, text=_load_fixture(version, "production"))
    )
    respx.get("/production.json").mock(return_value=Response(404))
    respx.get("/api/v1/production").mock(
        return_value=Response(
            404,
        )
    )
    respx.get("/api/v1/production/inverters").mock(
        return_value=Response(
            404,
        )
    )
    respx.get("/ivp/ensemble/inventory").mock(return_value=Response(200, json=[]))

    # Verify the library does not support scraping to comply with ADR004
    with pytest.raises(EnvoyProbeFailed):
        await _get_mock_envoy()

    # Test the register interface by registering a legacy production scraper
    #
    # ADR004 compliance:
    # We won't do this in our production code as we don't support scraping, but
    # we want to leave the door open for custom components to use the interface.
    #

    _KEY_TO_REGEX = {
        "watts_now": r"<td>Current.*</td>\s*<td>\s*(\d+|\d+\.\d+)\s*(W|kW|MW)</td>",
        "watt_hours_last_7_days": r"<td>Past Week</td>\s*<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>",
        "watt_hours_today": r"<td>Today</td>\s*<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>",
        "watt_hours_lifetime": r"<td>Since Installation</td>\s*<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>",
    }

    class LegacyEnvoySystemProduction(EnvoySystemProduction):
        @classmethod
        def from_production_legacy(cls, text: str) -> EnvoySystemProduction:
            """Legacy parser."""
            data: dict[str, int] = {
                "watts_now": 0,
                "watt_hours_today": 0,
                "watt_hours_last_7_days": 0,
                "watt_hours_lifetime": 0,
            }
            for key, regex in _KEY_TO_REGEX.items():
                if match := re.search(regex, text, re.MULTILINE):
                    unit = match.group(2).lower()
                    value = float(match.group(1))
                    if unit.startswith("k"):
                        value *= 1000
                    elif unit.startswith("m"):
                        value *= 1000000
                    data[key] = int(value)
            return cls(**data)

    class LegacyProductionScraper(EnvoyUpdater):
        async def probe(
            self, discovered_features: SupportedFeatures
        ) -> SupportedFeatures | None:
            """Probe the Envoy for this updater and return SupportedFeatures."""
            if SupportedFeatures.PRODUCTION in discovered_features:
                # Already discovered from another updater
                return None

            try:
                response = await self._probe_request(URL_PRODUCTION)
                data = response.text
            except ENDPOINT_PROBE_EXCEPTIONS:
                return None
            if "Since Installation" not in data:
                return None
            self._supported_features |= SupportedFeatures.PRODUCTION
            return self._supported_features

        async def update(self, envoy_data: EnvoyData) -> None:
            """Update the Envoy for this updater."""
            response = await self._request(URL_PRODUCTION)
            production_data = response.text
            envoy_data.raw[URL_PRODUCTION] = production_data
            envoy_data.system_production = (
                LegacyEnvoySystemProduction.from_production_legacy(production_data)
            )

    remove = register_updater(LegacyProductionScraper)
    assert LegacyProductionScraper in get_updaters()
    try:
        envoy = await _get_mock_envoy()
        data = envoy.data
        assert data is not None

        assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
        assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
        assert not (envoy._supported_features & SupportedFeatures.INVERTERS)
        assert _updater_features(envoy._updaters) == {
            "LegacyProductionScraper": SupportedFeatures.PRODUCTION,
        }
        assert envoy.part_number == "800-00069-r05"

        assert not data.system_consumption
        assert data.system_production.watts_now == 6630
        assert data.system_production.watt_hours_today == 53600
        assert data.system_production.watt_hours_last_7_days == 405000
        assert data.system_production.watt_hours_lifetime == 133000000
        assert not data.inverters
    finally:
        remove()
        assert LegacyProductionScraper not in get_updaters()


@pytest.mark.asyncio
@respx.mock
async def test_with_3_9_36_firmware_bad_auth():
    """Verify with 3.9.36 firmware with incorrect auth."""
    version = "3.9.36_bad_auth"
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(return_value=Response(404))
    respx.get("/production.json").mock(return_value=Response(404))
    respx.get("/api/v1/production").mock(
        return_value=Response(
            401, json=_load_json_fixture(version, "api_v1_production")
        )
    )
    respx.get("/api/v1/production/inverters").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production_inverters")
        )
    )
    respx.get("/ivp/ensemble/inventory").mock(return_value=Response(200, json=[]))

    with pytest.raises(EnvoyAuthenticationRequired):
        await _get_mock_envoy()


@pytest.mark.asyncio
@respx.mock
async def test_with_3_9_36_firmware_no_inverters():
    """Verify with 3.9.36 firmware with auth that does not allow inverters."""
    version = "3.9.36_bad_auth"
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
            401, json=_load_json_fixture(version, "api_v1_production_inverters")
        )
    )
    respx.get("/ivp/ensemble/inventory").mock(return_value=Response(200, json=[]))

    envoy = await _get_mock_envoy()
    data = envoy.data
    assert data is not None

    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.INVERTERS)
    assert _updater_features(envoy._updaters) == {
        "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
    }
    assert envoy.part_number == "800-00069-r05"


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
    assert _updater_features(envoy._updaters) == {
        "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
        "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
    }
    assert envoy.part_number == "800-00069-r05"

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
async def test_with_3_9_36_firmware_with_production_401():
    """Verify with 3.9.36 firmware when /production throws a 401."""
    version = "3.9.36"
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(return_value=Response(401))
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
    assert _updater_features(envoy._updaters) == {
        "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
        "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
    }
    assert envoy.part_number == "800-00069-r05"

    assert not data.system_consumption
    assert data.system_production.watts_now == 1271
    assert data.system_production.watt_hours_today == 1460
    assert data.system_production.watt_hours_last_7_days == 130349
    assert data.system_production.watt_hours_lifetime == 6012540
    assert data.inverters


@pytest.mark.asyncio
@respx.mock
async def test_with_3_9_36_firmware_with_production_and_production_json_401():
    """Verify with 3.9.36 firmware when /production and /production.json throws a 401."""
    version = "3.9.36"
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(return_value=Response(401))
    respx.get("/production.json").mock(return_value=Response(401))
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

    with pytest.raises(EnvoyAuthenticationRequired):
        await _get_mock_envoy()


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
    assert _updater_features(envoy._updaters) == {
        "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
        "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
    }
    assert envoy.part_number == "800-00069-r05"

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


@pytest.mark.parametrize(
    (
        "version",
        "part_number",
        "supported_features",
        "updaters",
    ),
    [
        (
            "5.0.62",
            "800-00551-r02",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
            },
        ),
        (
            "7.3.130",
            "800-00555-r03",
            SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
            },
        ),
        (
            "7.3.517",
            "800-00555-r03",
            SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyEnembleUpdater": SupportedFeatures.ENPOWER
                | SupportedFeatures.ENCHARGE,
            },
        ),
        (
            "7.6.114_without_cts",
            "800-00656-r06",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
            },
        ),
        (
            "7.6.175",
            "800-00555-r03",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
            },
        ),
        (
            "7.6.175_standard",
            "800-00656-r06",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
            },
        ),
        (
            "7.6.175_with_cts",
            "800-00654-r08",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
            },
        ),
        (
            "8.1.41",
            "800-00664-r05",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyEnembleUpdater": SupportedFeatures.ENPOWER
                | SupportedFeatures.ENCHARGE,
                "EnvoyProductionUpdater": SupportedFeatures.PRODUCTION
                | SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION,
            },
        ),
    ],
    ids=[
        "5.0.62",
        "7.3.130",
        "7.3.517",
        "7.6.114_without_cts",
        "7.6.175",
        "7.6.175_standard",
        "7.6.175_with_cts",
        "8.1.41",
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_with_7_x_firmware(
    version: str,
    part_number: str,
    snapshot: SnapshotAssertion,
    supported_features: SupportedFeatures,
    updaters: dict[str, SupportedFeatures],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify with 7.x firmware."""
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
    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    respx.post("https://entrez.enphaseenergy.com/tokens").mock(
        return_value=Response(200, text="token")
    )
    respx.get("/auth/check_jwt").mock(return_value=Response(200, json={}))
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    if "production" in files:
        respx.get("/production").mock(
            return_value=Response(200, json=_load_json_fixture(version, "production"))
        )
    else:
        respx.get("/production").mock(return_value=Response(404))
    if "production.json" in files:
        respx.get("/production.json").mock(
            return_value=Response(
                200, json=_load_json_fixture(version, "production.json")
            )
        )
    else:
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
    respx.get("/ivp/ensemble/inventory").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "ivp_ensemble_inventory")
        )
    )
    if "ivp_ensemble_dry_contacts" in files:
        respx.get("/ivp/ensemble/dry_contacts").mock(
            return_value=Response(
                200, json=_load_json_fixture(version, "ivp_ensemble_dry_contacts")
            )
        )
        respx.post("/ivp/ensemble/dry_contacts").mock(
            return_value=Response(
                200, json=_load_json_fixture(version, "ivp_ensemble_dry_contacts")
            )
        )
    if "ivp_ss_dry_contact_settings" in files:
        respx.get("/ivp/ss/dry_contact_settings").mock(
            return_value=Response(
                200, json=_load_json_fixture(version, "ivp_ss_dry_contact_settings")
            )
        )
        respx.post("/ivp/ss/dry_contact_settings").mock(
            return_value=Response(
                200, json=_load_json_fixture(version, "ivp_ss_dry_contact_settings")
            )
        )
    if "ivp_ensemble_power" in files:
        respx.get("/ivp/ensemble/power").mock(
            return_value=Response(
                200, json=_load_json_fixture(version, "ivp_ensemble_power")
            )
        )

    if "ivp_ensemble_secctrl" in files:
        respx.get("/ivp/ensemble/secctrl").mock(
            return_value=Response(
                200, json=_load_json_fixture(version, "ivp_ensemble_secctrl")
            )
        )

    caplog.set_level(logging.DEBUG)

    envoy = await _get_mock_envoy()
    data = envoy.data
    assert data == snapshot

    assert envoy.part_number == part_number
    assert _updater_features(envoy._updaters) == updaters
    assert envoy._supported_features == supported_features

    if supported_features & supported_features.ENPOWER:
        respx.post(URL_GRID_RELAY).mock(return_value=Response(200, json={}))
        await envoy.go_on_grid()
        assert respx.calls.last.request.content == orjson.dumps(
            {"mains_admin_state": "closed"}
        )
        await envoy.go_off_grid()
        assert respx.calls.last.request.content == orjson.dumps(
            {"mains_admin_state": "open"}
        )

        # Test updating dry contacts
        with pytest.raises(ValueError):
            await envoy.update_dry_contact({"missing": "id"})

        with pytest.raises(ValueError):
            bad_envoy = await _get_mock_envoy(False)
            await bad_envoy.probe()
            await bad_envoy.update_dry_contact({"id": "NC1"})

        dry_contact = envoy.data.dry_contact_settings["NC1"]
        new_data = {"id": "NC1", "load_name": "NC1 Test"}
        new_model = replace(dry_contact, **new_data)

        await envoy.update_dry_contact(new_data)
        assert respx.calls.last.request.content == orjson.dumps(
            {"dry_contacts": new_model.to_api()}
        )

        await envoy.open_dry_contact("NC1")
        assert envoy.data.dry_contact_status["NC1"].status == DryContactStatus.OPEN
        assert respx.calls.last.request.content == orjson.dumps(
            {"dry_contacts": {"id": "NC1", "status": "open"}}
        )

        await envoy.close_dry_contact("NC1")
        assert envoy.data.dry_contact_status["NC1"].status == DryContactStatus.CLOSED
        assert respx.calls.last.request.content == orjson.dumps(
            {"dry_contacts": {"id": "NC1", "status": "closed"}}
        )

        assert "Sending POST" in caplog.text

    else:
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.go_off_grid()
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.go_on_grid()
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.update_dry_contact({"id": "NC1"})
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.update_dry_contact({"id": "NC1"})
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.open_dry_contact("NC1")
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.close_dry_contact("NC1")
