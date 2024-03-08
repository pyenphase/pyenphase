import json
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
from syrupy.assertion import SnapshotAssertion

from pyenphase import Envoy, EnvoyInverter, register_updater
from pyenphase.const import URL_GRID_RELAY, URL_PRODUCTION, URL_TARIFF, PhaseNames
from pyenphase.envoy import SupportedFeatures, get_updaters
from pyenphase.exceptions import (
    ENDPOINT_PROBE_EXCEPTIONS,
    EnvoyAuthenticationRequired,
    EnvoyFeatureNotAvailable,
    EnvoyProbeFailed,
)
from pyenphase.models.dry_contacts import DryContactStatus
from pyenphase.models.envoy import EnvoyData
from pyenphase.models.meters import (
    CtMeterData,
    CtMeterStatus,
    CtType,
    EnvoyMeterData,
    EnvoyPhaseMode,
)
from pyenphase.models.system_consumption import EnvoySystemConsumption
from pyenphase.models.system_production import EnvoySystemProduction
from pyenphase.models.tariff import EnvoyStorageMode
from pyenphase.updaters.base import EnvoyUpdater
from pyenphase.updaters.meters import EnvoyMetersUpdater

LOGGER = logging.getLogger(__name__)


def _fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


def _load_fixture(version: str, name: str) -> str:
    with open(_fixtures_dir() / version / name) as read_in:
        return read_in.read()


def _load_json_fixture(version: str, name: str) -> dict[str, Any]:
    return orjson.loads(_load_fixture(version, name))


def _load_json_list_fixture(version: str, name: str) -> list[dict[str, Any]]:
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
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
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

    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if "admin_lib_tariff" in files:
        try:
            json_data = _load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/admin/lib/tariff").mock(return_value=Response(404))

    respx.get("/ivp/meters").mock(return_value=Response(200, json=[]))

    envoy = await _get_mock_envoy()
    data: EnvoyData | None = envoy.data
    assert data is not None

    assert not (envoy._supported_features & SupportedFeatures.METERING)
    assert not (envoy._supported_features & SupportedFeatures.INVERTERS)
    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert _updater_features(envoy._updaters) == {
        "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
    }
    assert envoy.part_number == "800-00551-r02"

    assert data.system_production is not None
    assert (
        data.system_production.watts_now == 5894
    )  # This used to use the production.json endpoint, but its always a bit behind
    assert data.system_production.watt_hours_today == 17920
    assert data.system_production.watt_hours_last_7_days == 276614
    assert data.system_production.watt_hours_lifetime == 10279087
    assert not data.inverters
    assert envoy.ct_meter_count == 0
    assert envoy.phase_count == 1
    assert envoy.phase_mode is None
    assert envoy.consumption_meter_type is None
    assert not data.system_consumption_phases
    assert not data.system_production_phases
    assert envoy.envoy_model == "Envoy"

    # Test that Ensemble commands raise FeatureNotAvailable
    with pytest.raises(EnvoyFeatureNotAvailable):
        await envoy.go_off_grid()
    with pytest.raises(EnvoyFeatureNotAvailable):
        await envoy.go_on_grid()


@pytest.mark.asyncio
@respx.mock
async def test_with_5_0_49_firmware():
    """Verify with 5.0.49 firmware."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
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

    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if "admin_lib_tariff" in files:
        try:
            json_data = _load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/admin/lib/tariff").mock(return_value=Response(404))

    respx.get("/ivp/meters").mock(return_value=Response(404))

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
    assert envoy.phase_count == 1

    assert not data.system_consumption
    assert envoy.ct_meter_count == 0
    assert envoy.phase_count == 1
    assert envoy.phase_mode is None
    assert envoy.consumption_meter_type is None
    assert not data.system_consumption_phases
    assert not data.system_production_phases
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
    assert envoy.envoy_model == "Envoy"


@pytest.mark.asyncio
@respx.mock
async def test_with_3_7_0_firmware():
    """Verify with 3.7.0 firmware."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
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
    respx.get("/admin/lib/tariff").mock(return_value=Response(404))
    respx.get("/ivp/meters").mock(return_value=Response(404))

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
        assert envoy.ct_meter_count == 0
        assert envoy.phase_count == 1
        assert envoy.phase_mode is None
        assert envoy.consumption_meter_type is None
        assert not data.system_consumption_phases
        assert not data.system_production_phases
        assert envoy.envoy_model == "Envoy"
    finally:
        remove()
        assert LegacyProductionScraper not in get_updaters()


@pytest.mark.asyncio
@respx.mock
async def test_with_3_9_36_firmware_bad_auth():
    """Verify with 3.9.36 firmware with incorrect auth."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
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

    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if "admin_lib_tariff" in files:
        try:
            json_data = _load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/admin/lib/tariff").mock(return_value=Response(401))

    respx.get("/ivp/meters").mock(return_value=Response(200, json=[]))

    with pytest.raises(EnvoyAuthenticationRequired):
        await _get_mock_envoy()


@pytest.mark.asyncio
@respx.mock
async def test_with_3_9_36_firmware_no_inverters():
    """Verify with 3.9.36 firmware with auth that does not allow inverters."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
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

    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if "admin_lib_tariff" in files:
        try:
            json_data = _load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/admin/lib/tariff").mock(return_value=Response(401))

    respx.get("/ivp/meters").mock(return_value=Response(404))

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
    assert envoy.ct_meter_count == 0
    assert envoy.phase_count == 1
    assert envoy.phase_mode is None
    assert envoy.consumption_meter_type is None
    assert not data.system_consumption_phases
    assert not data.system_production_phases


@pytest.mark.asyncio
@respx.mock
async def test_with_3_9_36_firmware():
    """Verify with 3.9.36 firmware."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
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

    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if "admin_lib_tariff" in files:
        try:
            json_data = _load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/admin/lib/tariff").mock(return_value=Response(401))

    respx.get("/ivp/meters").mock(
        return_value=Response(404, json={"error": "404 - Not Found"})
    )

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
    assert envoy.ct_meter_count == 0
    assert envoy.phase_count == 1
    assert envoy.phase_mode is None
    assert envoy.consumption_meter_type is None
    assert not data.system_consumption_phases
    assert not data.system_production_phases
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
    assert envoy.envoy_model == "Envoy"


@pytest.mark.asyncio
@respx.mock
async def test_with_3_9_36_firmware_with_production_401():
    """Verify with 3.9.36 firmware when /production throws a 401."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
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

    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if "admin_lib_tariff" in files:
        try:
            json_data = _load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/admin/lib/tariff").mock(return_value=Response(404))

    respx.get("/ivp/meters").mock(return_value=Response(404))

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
    assert envoy.ct_meter_count == 0
    assert envoy.phase_count == 1
    assert envoy.phase_mode is None
    assert envoy.consumption_meter_type is None
    assert not data.system_consumption_phases
    assert not data.system_production_phases


@pytest.mark.asyncio
@respx.mock
async def test_with_3_9_36_firmware_with_production_and_production_json_401():
    """Verify with 3.9.36 firmware when /production and /production.json throws a 401."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
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
    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if "admin_lib_tariff" in files:
        try:
            json_data = _load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/admin/lib/tariff").mock(return_value=Response(404))
    respx.get("/ivp/meters").mock(return_value=Response(200, json=[]))

    with pytest.raises(EnvoyAuthenticationRequired):
        await _get_mock_envoy()


@pytest.mark.asyncio
@respx.mock
async def test_with_3_9_36_firmware_with_meters_401():
    """Verify with 3.9.36 firmware when /ivp/meters throws a 401."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "3.9.36"
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(return_value=Response(404))
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
    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if "admin_lib_tariff" in files:
        try:
            json_data = _load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/admin/lib/tariff").mock(return_value=Response(404))
    respx.get("/ivp/meters").mock(return_value=Response(401))

    with pytest.raises(EnvoyAuthenticationRequired):
        await _get_mock_envoy()


@pytest.mark.asyncio
@respx.mock
async def test_with_3_8_10_firmware_with_meters_401():
    """Verify with 3.8.10 firmware when /ivp/meters throws a 401."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "3.8.10"
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(return_value=Response(404))
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
    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if "admin_lib_tariff" in files:
        try:
            json_data = _load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/admin/lib/tariff").mock(return_value=Response(404))
    respx.get("/ivp/meters").mock(return_value=Response(401))

    with pytest.raises(EnvoyAuthenticationRequired):
        await _get_mock_envoy()


@pytest.mark.asyncio
@respx.mock
async def test_with_3_17_3_firmware():
    """Verify with 3.17.3 firmware."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
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

    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    if "admin_lib_tariff" in files:
        try:
            json_data = _load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/admin/lib/tariff").mock(return_value=Response(404))

    respx.get("/ivp/meters").mock(return_value=Response(200, json=[]))

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
    assert envoy.ct_meter_count == 0
    assert envoy.phase_count == 1
    assert envoy.phase_mode is None
    assert envoy.consumption_meter_type is None
    assert not data.system_consumption_phases
    assert not data.system_production_phases
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


def _start_7_firmware_mock():
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


@pytest.mark.asyncio
@respx.mock
async def test_pr111_with_7_3_466_metered_disabled_cts():
    """Test envoy metered with disabled ct to report from production inverters PR111."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.3.466_metered_disabled_cts"
    _start_7_firmware_mock()
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(
        return_value=Response(200, text=_load_fixture(version, "production"))
    )
    respx.get("/production.json").mock(
        return_value=Response(200, text=_load_fixture(version, "production.json"))
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
    respx.get("/admin/lib/tariff").mock(return_value=Response(404))
    respx.get("/ivp/meters").mock(
        return_value=Response(200, text=_load_fixture(version, "ivp_meters"))
    )

    envoy = await _get_mock_envoy()
    data = envoy.data
    assert data is not None

    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert envoy._supported_features & SupportedFeatures.PRODUCTION
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert envoy._supported_features & SupportedFeatures.PRODUCTION
    assert _updater_features(envoy._updaters) == {
        "EnvoyProductionJsonFallbackUpdater": SupportedFeatures.PRODUCTION,
        "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
    }
    assert envoy.part_number == "800-00654-r08"

    assert not data.system_consumption
    assert data.system_production.watts_now == 751
    assert data.system_production.watt_hours_today == 4425
    assert data.system_production.watt_hours_last_7_days == 111093
    assert data.system_production.watt_hours_lifetime == 702919


@pytest.mark.asyncio
@respx.mock
async def test_pr111_with_7_6_175_with_cts():
    """Test envoy metered with ct to report from production eim PR111."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_with_cts"
    _start_7_firmware_mock()
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(
        return_value=Response(200, text=_load_fixture(version, "production"))
    )
    respx.get("/production.json").mock(
        return_value=Response(200, text=_load_fixture(version, "production.json"))
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
    respx.get("/admin/lib/tariff").mock(return_value=Response(404))
    respx.get("/ivp/meters").mock(
        return_value=Response(200, text=_load_fixture(version, "ivp_meters"))
    )
    respx.get("/ivp/meters/readings").mock(
        return_value=Response(200, text=_load_fixture(version, "ivp_meters_readings"))
    )
    envoy = await _get_mock_envoy()
    data = envoy.data
    assert data is not None

    assert envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION
    assert envoy._supported_features & SupportedFeatures.NET_CONSUMPTION
    assert envoy._supported_features & SupportedFeatures.PRODUCTION
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert envoy._supported_features & SupportedFeatures.METERING
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert envoy._supported_features & SupportedFeatures.CTMETERS
    assert _updater_features(envoy._updaters) == {
        "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
        "EnvoyProductionUpdater": SupportedFeatures.METERING
        | SupportedFeatures.TOTAL_CONSUMPTION
        | SupportedFeatures.NET_CONSUMPTION
        | SupportedFeatures.PRODUCTION,
        "EnvoyMetersUpdater": SupportedFeatures.CTMETERS,
    }

    assert envoy.part_number == "800-00654-r08"

    assert data.system_consumption
    assert data.system_production.watts_now == 488
    assert data.system_production.watt_hours_today == 4425
    assert data.system_production.watt_hours_last_7_days == 111093
    assert data.system_production.watt_hours_lifetime == 3183793
    assert (
        envoy.envoy_model
        == "Envoy, phases: 1, phase mode: three, net-consumption CT, production CT"
    )


@pytest.mark.asyncio
@respx.mock
async def test_pr111_with_7_6_175_standard():
    """Test envoy metered with ct to report from production eim PR111."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "7.6.175_standard"
    _start_7_firmware_mock()
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(
        return_value=Response(200, text=_load_fixture(version, "production"))
    )
    respx.get("/production.json").mock(
        return_value=Response(200, text=_load_fixture(version, "production.json"))
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
    respx.get("/admin/lib/tariff").mock(return_value=Response(404))
    respx.get("/ivp/meters").mock(return_value=Response(200, text=""))

    envoy = await _get_mock_envoy()
    data = envoy.data
    assert data is not None

    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert envoy._supported_features & SupportedFeatures.PRODUCTION
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert _updater_features(envoy._updaters) == {
        "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
        "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
    }

    assert envoy.part_number == "800-00656-r06"

    assert not data.system_consumption
    assert data.system_production.watts_now == 5740
    assert data.system_production.watt_hours_today == 36462
    assert data.system_production.watt_hours_last_7_days == 189712
    assert data.system_production.watt_hours_lifetime == 6139406
    assert envoy.envoy_model == "Envoy"


@pytest.mark.asyncio
@respx.mock
async def test_ct_data_structures_with_7_6_175_with_cts_3phase():
    """Test meters model using envoy metered CT with multiple phases"""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)

    # start with regular data first
    version = "7.6.175_with_cts_3phase"
    _start_7_firmware_mock()
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production").mock(
        return_value=Response(200, text=_load_fixture(version, "production"))
    )
    respx.get("/production.json").mock(
        return_value=Response(200, text=_load_fixture(version, "production.json"))
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
    respx.get("/admin/lib/tariff").mock(return_value=Response(404))
    respx.get("/ivp/meters").mock(
        return_value=Response(200, text=_load_fixture(version, "ivp_meters"))
    )
    respx.get("/ivp/meters/readings").mock(
        return_value=Response(200, text=_load_fixture(version, "ivp_meters_readings"))
    )

    # details of this test is done elsewhere already, just check data is returned
    envoy = await _get_mock_envoy()
    data = envoy.data
    assert data is not None

    # Test prior similar updater active
    remove_2nd_metersupdater = register_updater(EnvoyMetersUpdater)
    await envoy.probe()
    remove_2nd_metersupdater

    # load mock data for meters and their readings
    meters_status = _load_json_list_fixture(version, "ivp_meters")
    meters_readings = _load_json_list_fixture(version, "ivp_meters_readings")

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
    assert ct_data.eid == 704643328
    assert ct_data.measurement_type == "production"

    # test meters.from_phase method
    ct_phase_data: EnvoyMeterData | None = EnvoyMeterData.from_phase(
        meters_readings[0], meter_status, 0
    )
    assert ct_phase_data is not None
    assert ct_phase_data.eid == 1778385169
    assert ct_phase_data.measurement_type == "production"
    assert ct_phase_data.energy_delivered == 3183794

    assert (
        envoy.envoy_model
        == "Envoy, phases: 3, phase mode: three, net-consumption CT, production CT"
    )

    # test exception handling by specifying non-existing phase
    ct_no_phase_data = EnvoyMeterData.from_phase(meters_readings[0], meter_status, 3)
    assert ct_no_phase_data is None

    # test exception handling for missing phase data, remove phase data from mock data
    del meters_readings[0]["channels"]
    ct_no_phase_data = EnvoyMeterData.from_phase(meters_readings[0], meter_status, 0)
    assert ct_no_phase_data is None

    # test exception handling for phase data in production using wrong phase
    production_data = data.raw["/production"]
    production_no_phase_data = EnvoySystemProduction.from_production_phase(
        production_data, 3
    )
    assert production_no_phase_data is None

    # test exception handling for phase data if key is missing
    del production_data["production"][1]["type"]
    try:
        production_no_phase_data = EnvoySystemProduction.from_production_phase(
            production_data, 0
        )
    except ValueError:
        production_no_phase_data = None
    assert production_no_phase_data is None

    # test exception handling for phase data in consumption using wrong phase
    consumption_data = data.raw["/production"]
    consumption_no_phase_data = EnvoySystemConsumption.from_production_phase(
        consumption_data, 3
    )
    assert consumption_no_phase_data is None

    # test handling missing phases when expected in ct readings
    meters_status = _load_json_list_fixture(version, "ivp_meters")
    meters_readings = _load_json_list_fixture(version, "ivp_meters_readings")

    # remove phase data from CT readings
    del meters_readings[0]["channels"]
    del meters_readings[1]["channels"]

    respx.get("/ivp/meters").mock(return_value=Response(200, json=meters_status))
    respx.get("/ivp/meters/readings").mock(
        return_value=Response(200, json=meters_readings)
    )

    await envoy.update()
    assert envoy.data.ctmeter_production_phases is None
    assert envoy.data.ctmeter_consumption_phases is None


@pytest.mark.parametrize(
    (
        "version",
        "part_number",
        "supported_features",
        "updaters",
        "phase_count",
        "common_properties",
        "production_phases",
        "consumption_phases",
        "ct_production",
        "ct_consumption",
        "ct_production_phases",
        "ct_consumption_phases",
    ),
    [
        (
            "5.0.62",
            "800-00551-r02",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "4.10.35",
            "800-00555-r03",
            SupportedFeatures.METERING
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.DUALPHASE
                | SupportedFeatures.CTMETERS,
            },
            2,
            {
                "ctMeters": 2,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "consumptionMeter": CtType.NET_CONSUMPTION,
            },
            {},
            {},
            {
                "eid": 704643328,
                "active_power": 166,
                "measurement_type": CtType.PRODUCTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                "eid": 704643584,
                "active_power": 567,
                "measurement_type": CtType.NET_CONSUMPTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385169,
                    "active_power": 83,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385170,
                    "active_power": 84,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385425,
                    "active_power": 394,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385426,
                    "active_power": 173,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
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
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.3.130_no_consumption",
            "800-00647-r10",
            SupportedFeatures.METERING
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionUpdater": SupportedFeatures.METERING
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.DUALPHASE
                | SupportedFeatures.CTMETERS,
            },
            2,
            {
                "ctMeters": 1,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "consumptionMeter": None,
            },
            {},
            {},
            {
                "eid": 704643328,
                "active_power": 3625,
                "measurement_type": CtType.PRODUCTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {},
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385169,
                    "active_power": 1811,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385170,
                    "active_power": 1814,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {},
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
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyEnembleUpdater": SupportedFeatures.ENPOWER
                | SupportedFeatures.ENCHARGE,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.3.517_legacy_savings_mode",
            "800-00555-r03",
            SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyEnembleUpdater": SupportedFeatures.ENPOWER
                | SupportedFeatures.ENCHARGE,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.3.517_system_2",
            "800-00555-r03",
            SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyEnembleUpdater": SupportedFeatures.ENPOWER
                | SupportedFeatures.ENCHARGE,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.DUALPHASE
                | SupportedFeatures.CTMETERS,
            },
            2,
            {
                "ctMeters": 2,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "consumptionMeter": CtType.NET_CONSUMPTION,
            },
            {},
            {},
            {
                "eid": 704643328,
                "active_power": 2660,
                "measurement_type": CtType.PRODUCTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                "eid": 704643584,
                "active_power": 23,
                "measurement_type": CtType.NET_CONSUMPTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385169,
                    "active_power": 1331,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385170,
                    "active_power": 1329,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385425,
                    "active_power": -17,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385426,
                    "active_power": 41,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
        ),
        (
            "7.3.466_metered_disabled_cts",
            "800-00654-r08",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonFallbackUpdater": SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.6.114_without_cts",
            "800-00656-r06",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.6.175",
            "800-00555-r03",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.6.175_total",
            "800-00654-r06",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonFallbackUpdater": SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.6.175_standard",
            "800-00656-r06",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.6.175_with_cts",
            "800-00654-r08",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.CTMETERS,
            },
            1,
            {
                "ctMeters": 2,
                "phaseCount": 1,
                "phaseMode": EnvoyPhaseMode.THREE,
                "consumptionMeter": CtType.NET_CONSUMPTION,
            },
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.6.175_with_cts_3phase",
            "800-00654-r08",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.THREEPHASE
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.THREEPHASE
                | SupportedFeatures.CTMETERS,
            },
            3,
            {
                "ctMeters": 2,
                "phaseCount": 3,
                "phaseMode": EnvoyPhaseMode.THREE,
                "consumptionMeter": CtType.NET_CONSUMPTION,
            },
            {
                PhaseNames.PHASE_1: {
                    "watt_hours_lifetime": 1869678,
                    "watt_hours_last_7_days": 29891,
                    "watt_hours_today": 2200,
                    "watts_now": -3,
                },
                PhaseNames.PHASE_2: {
                    "watt_hours_lifetime": 1241246,
                    "watt_hours_last_7_days": 19794,
                    "watt_hours_today": 1455,
                    "watts_now": 0,
                },
                PhaseNames.PHASE_3: {
                    "watt_hours_lifetime": 1240189,
                    "watt_hours_last_7_days": 19807,
                    "watt_hours_today": 1458,
                    "watts_now": -4,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "watt_hours_lifetime": 2293783,
                    "watt_hours_last_7_days": 39392,
                    "watt_hours_today": 8585,
                    "watts_now": 89,
                },
                PhaseNames.PHASE_2: {
                    "watt_hours_lifetime": 948058,
                    "watt_hours_last_7_days": 18949,
                    "watt_hours_today": 2155,
                    "watts_now": 123,
                },
                PhaseNames.PHASE_3: {
                    "watt_hours_lifetime": 832954,
                    "watt_hours_last_7_days": 10443,
                    "watt_hours_today": 1683,
                    "watts_now": -3,
                },
            },
            {
                "eid": 704643328,
                "active_power": 489,
                "measurement_type": CtType.PRODUCTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                "eid": 704643584,
                "active_power": -36,
                "measurement_type": CtType.NET_CONSUMPTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385169,
                    "active_power": 489,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385170,
                    "active_power": 0,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_3: {
                    "eid": 1778385171,
                    "active_power": -1,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385425,
                    "active_power": -36,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385426,
                    "active_power": -0,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_3: {
                    "eid": 1778385427,
                    "active_power": -0,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
        ),
        (
            "7.6.185_with_cts_and_battery_3t",
            "800-00654-r08",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.TARIFF
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyEnembleUpdater": SupportedFeatures.ENCHARGE,
                "EnvoyProductionUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.CTMETERS,
            },
            1,
            {
                "ctMeters": 2,
                "phaseCount": 1,
                "phaseMode": EnvoyPhaseMode.THREE,
                "consumptionMeter": CtType.NET_CONSUMPTION,
            },
            {},
            {},
            {},
            {},
            {},
            {},
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
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "8.2.127_with_3cts_and_battery_split",
            "800-00654-r08",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.TARIFF
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyEnembleUpdater": SupportedFeatures.ENCHARGE
                | SupportedFeatures.ENPOWER,
                "EnvoyProductionUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.DUALPHASE
                | SupportedFeatures.CTMETERS,
            },
            2,
            {
                "ctMeters": 3,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "consumptionMeter": CtType.NET_CONSUMPTION,
            },
            {},
            {},
            {
                "eid": 704643328,
                "active_power": 1714,
                "measurement_type": CtType.PRODUCTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                "eid": 704643584,
                "active_power": 129,
                "measurement_type": CtType.NET_CONSUMPTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385169,
                    "active_power": 856,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385170,
                    "active_power": 858,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385425,
                    "active_power": -201,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385426,
                    "active_power": 331,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
        ),
    ],
    ids=[
        "5.0.62",
        "4.10.35",
        "7.3.130",
        "7.3.130_no_consumption",
        "7.3.517",
        "7.3.517_legacy_savings_mode",
        "7.3.517_system_2",
        "7.3.466_metered_disabled_cts",
        "7.6.114_without_cts",
        "7.6.175",
        "7.6.175_total",
        "7.6.175_standard",
        "7.6.175_with_cts",
        "7.6.175_with_cts_3phase",
        "7.6.185_with_cts_and_battery_3t",
        "8.1.41",
        "8.2.127_with_3cts_and_battery_split",
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
    phase_count: int,
    common_properties: dict[str, Any],
    production_phases: dict[str, dict[str, Any]],
    consumption_phases: dict[str, dict[str, Any]],
    ct_production: dict[str, Any],
    ct_consumption: dict[str, Any],
    ct_production_phases: dict[str, dict[str, Any]],
    ct_consumption_phases: dict[str, dict[str, Any]],
) -> None:
    """Verify with 7.x firmware."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    _start_7_firmware_mock()
    path = f"tests/fixtures/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    respx.get("/info").mock(
        return_value=Response(200, text=_load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    if "production" in files:
        try:
            json_data = _load_json_fixture(version, "production")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/production").mock(return_value=Response(200, json=json_data))
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
        try:
            json_data = _load_json_fixture(version, "ivp_ensemble_dry_contacts")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/ivp/ensemble/dry_contacts").mock(
            return_value=Response(200, json=json_data)
        )
        respx.post("/ivp/ensemble/dry_contacts").mock(
            return_value=Response(200, json=json_data)
        )
    if "ivp_ss_dry_contact_settings" in files:
        try:
            json_data = _load_json_fixture(version, "ivp_ss_dry_contact_settings")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/ivp/ss/dry_contact_settings").mock(
            return_value=Response(200, json=json_data)
        )
        respx.post("/ivp/ss/dry_contact_settings").mock(
            return_value=Response(200, json=json_data)
        )
    if "ivp_ensemble_power" in files:
        try:
            json_data = _load_json_fixture(version, "ivp_ensemble_power")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/ivp/ensemble/power").mock(
            return_value=Response(200, json=json_data)
        )

    if "ivp_ensemble_secctrl" in files:
        try:
            json_data = _load_json_fixture(version, "ivp_ensemble_secctrl")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/ivp/ensemble/secctrl").mock(
            return_value=Response(200, json=json_data)
        )

    if "admin_lib_tariff" in files:
        try:
            json_data = _load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
        respx.put("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/admin/lib/tariff").mock(return_value=Response(404))

    if "ivp_meters" in files:
        respx.get("/ivp/meters").mock(
            return_value=Response(200, json=_load_json_fixture(version, "ivp_meters"))
        )
    else:
        respx.get("/ivp/meters").mock(return_value=Response(404))

    if "ivp_meters_readings" in files:
        respx.get("/ivp/meters/readings").mock(
            return_value=Response(
                200, json=_load_json_fixture(version, "ivp_meters_readings")
            )
        )
    else:
        respx.get("/ivp/meters/readings").mock(return_value=Response(404))

    caplog.set_level(logging.DEBUG)

    envoy = await _get_mock_envoy()
    data = envoy.data
    assert data == snapshot

    assert envoy.firmware == version.split("_")[0]
    assert envoy.serial_number

    assert envoy.part_number == part_number
    assert _updater_features(envoy._updaters) == updaters
    # We're testing, disable warning on private member
    # pylint: disable=protected-access
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
        new_data: dict[str, Any] = {"id": "NC1", "load_name": "NC1 Test"}
        new_model = replace(dry_contact, **new_data)

        await envoy.update_dry_contact(new_data)
        assert respx.calls.last.request.content == orjson.dumps(
            {"dry_contacts": new_model.to_api()}
        )

        if envoy.data.dry_contact_settings["NC1"].black_start is not None:
            assert (
                new_model.to_api()["black_s_start"]
                == envoy.data.dry_contact_settings["NC1"].black_start
            )
        else:
            assert "black_s_start" not in new_model.to_api()

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

    if (supported_features & SupportedFeatures.ENCHARGE) and (
        supported_features & SupportedFeatures.TARIFF
    ):
        # Test `savings-mode` is converted to `economy`
        if (
            envoy.data.raw[URL_TARIFF]["tariff"]["storage_settings"]["mode"]
            == "savings-mode"
        ):
            assert envoy.data.tariff.storage_settings.mode == EnvoyStorageMode.SAVINGS

        storage_settings = envoy.data.tariff.storage_settings
        new_data = {"charge_from_grid": True}
        new_model = replace(storage_settings, **new_data)

        if envoy.data.tariff.storage_settings.date is not None:
            assert new_model.to_api()["date"] == envoy.data.tariff.storage_settings.date
        else:
            assert "date" not in new_model.to_api()

        # Test setting battery features
        await envoy.enable_charge_from_grid()
        assert envoy.data.tariff.storage_settings.charge_from_grid is True
        assert respx.calls.last.request.content == orjson.dumps(
            {"tariff": envoy.data.tariff.to_api()}
        )

        await envoy.disable_charge_from_grid()
        assert envoy.data.tariff.storage_settings.charge_from_grid is False
        assert respx.calls.last.request.content == orjson.dumps(  # type: ignore[unreachable]
            {"tariff": envoy.data.tariff.to_api()}
        )

        await envoy.set_reserve_soc(50)
        assert envoy.data.tariff.storage_settings.reserved_soc == round(float(50), 1)
        assert respx.calls.last.request.content == orjson.dumps(
            {"tariff": envoy.data.tariff.to_api()}
        )

        await envoy.set_storage_mode(EnvoyStorageMode.SELF_CONSUMPTION)
        assert (
            envoy.data.tariff.storage_settings.mode == EnvoyStorageMode.SELF_CONSUMPTION
        )
        assert respx.calls.last.request.content == orjson.dumps(
            {"tariff": envoy.data.tariff.to_api()}
        )

        with pytest.raises(TypeError):
            await envoy.set_storage_mode("invalid")

        bad_envoy = await _get_mock_envoy()
        await bad_envoy.probe()
        with pytest.raises(EnvoyFeatureNotAvailable):
            bad_envoy.data.tariff.storage_settings = None
            await bad_envoy.enable_charge_from_grid()
        with pytest.raises(ValueError):
            bad_envoy.data.tariff = None
            await bad_envoy.enable_charge_from_grid()
        with pytest.raises(ValueError):
            bad_envoy.data = None
            await bad_envoy.enable_charge_from_grid()
    else:
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.enable_charge_from_grid()
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.disable_charge_from_grid()

    assert envoy.phase_count == phase_count
    assert envoy.ct_meter_count == common_properties["ctMeters"]
    assert envoy.phase_count == common_properties["phaseCount"]
    assert envoy.phase_mode == common_properties["phaseMode"]
    assert envoy.consumption_meter_type == common_properties["consumptionMeter"]

    # are all production phases reported
    assert (
        envoy.active_phase_count == 0
        if data.system_production_phases is None
        else len(data.system_production_phases)
    )
    # Test each production phase
    for phase in production_phases:
        proddata = envoy.data.system_production_phases[phase]
        modeldata = production_phases[phase]

        # test each element of the phase data
        assert proddata.watt_hours_lifetime == modeldata["watt_hours_lifetime"]
        assert proddata.watt_hours_last_7_days == modeldata["watt_hours_last_7_days"]
        assert proddata.watt_hours_today == modeldata["watt_hours_today"]
        assert proddata.watts_now == modeldata["watts_now"]

    # are all consumption phases reported
    assert (
        envoy.active_phase_count == 0
        if data.system_consumption_phases is None
        else len(data.system_consumption_phases)
    )
    # Test each consumption phase
    for phase in consumption_phases:
        consdata = envoy.data.system_consumption_phases[phase]
        modeldata = consumption_phases[phase]

        # test each element of the phase data
        assert consdata.watt_hours_lifetime == modeldata["watt_hours_lifetime"]
        assert consdata.watt_hours_last_7_days == modeldata["watt_hours_last_7_days"]
        assert consdata.watt_hours_today == modeldata["watt_hours_today"]
        assert consdata.watts_now == modeldata["watts_now"]

    # test ct production meter values
    for key in ct_production:
        assert ct_production[key] == getattr(envoy.data.ctmeter_production, key)

    # are all CT production phases reported
    assert (
        envoy.active_phase_count == 0
        if data.ctmeter_production_phases is None
        else len(data.ctmeter_production_phases)
    )

    # Test each ct production phase
    for phase in ct_production_phases:
        proddata = envoy.data.ctmeter_production_phases[phase]
        modeldata = ct_production_phases[phase]
        # test each element of the phase data
        for key in modeldata:
            assert modeldata[key] == getattr(proddata, key)

    # test ct consumption meter values
    for key in ct_consumption:
        assert ct_consumption[key] == getattr(envoy.data.ctmeter_consumption, key)

    # are all production CT phases reported
    assert (
        envoy.active_phase_count == 0
        if data.ctmeter_consumption_phases is None
        else len(data.ctmeter_consumption_phases)
    )

    # Test each ct consumption phase
    for phase in ct_consumption_phases:
        consdata = envoy.data.ctmeter_consumption_phases[phase]
        modeldata = ct_consumption_phases[phase]
        # test each element of the phase data
        for key in modeldata:
            assert modeldata[key] == getattr(consdata, key)
