"""Test envoy firmware prior to v7."""

import logging
import re

import aiohttp
import pytest
from aioresponses import aioresponses

from pyenphase import EnvoyInverter, register_updater
from pyenphase.const import URL_PRODUCTION
from pyenphase.envoy import SupportedFeatures, get_updaters
from pyenphase.exceptions import (
    ENDPOINT_PROBE_EXCEPTIONS,
    EnvoyAuthenticationRequired,
    EnvoyFeatureNotAvailable,
    EnvoyPoorDataQuality,
    EnvoyProbeFailed,
)
from pyenphase.models.envoy import EnvoyData
from pyenphase.models.meters import EnvoyPhaseMode
from pyenphase.models.system_production import EnvoySystemProduction
from pyenphase.updaters.base import EnvoyUpdater

from .common import (
    get_mock_envoy,
    load_json_fixture,
    override_mock,
    prep_envoy,
    updater_features,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_with_4_2_27_firmware(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify with 4.2.27 firmware."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "4.2.27"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(version, test_client_session)
    data: EnvoyData | None = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

    assert not (envoy._supported_features & SupportedFeatures.METERING)
    assert not (envoy._supported_features & SupportedFeatures.INVERTERS)
    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert updater_features(envoy._updaters) == {
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
async def test_with_4_2_33_firmware_no_cons_ct(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify with 4.2.33 firmware."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "4.2.33"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(version, test_client_session)
    data: EnvoyData | None = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

    assert envoy._supported_features & SupportedFeatures.METERING
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert updater_features(envoy._updaters) == {
        "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
        | SupportedFeatures.PRODUCTION,
        "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
        "EnvoyMetersUpdater": SupportedFeatures.DUALPHASE | SupportedFeatures.CTMETERS,
    }
    assert envoy.part_number == "800-00547-r05"

    assert data.system_production is not None
    assert (
        data.system_production.watts_now == -9
    )  # This used to use the production.json endpoint, but its always a bit behind
    assert data.system_production.watt_hours_today == 10215
    assert data.system_production.watt_hours_last_7_days == 10833
    assert data.system_production.watt_hours_lifetime == 8598257
    assert not data.system_consumption
    assert data.inverters["1234567890"] == EnvoyInverter(
        serial_number="1234567890",
        last_report_date=1743551631,
        last_report_watts=3,
        max_report_watts=131,
    )
    assert data.inverters["121622033019"] == EnvoyInverter(
        serial_number="121622033019",
        last_report_date=1536668634,
        last_report_watts=17,
        max_report_watts=17,
    )
    assert envoy.ct_meter_count == 1
    assert envoy.phase_count == 2
    assert envoy.phase_mode == EnvoyPhaseMode.SPLIT
    assert envoy.consumption_meter_type is None
    assert not data.system_consumption_phases
    assert not data.system_production_phases
    assert envoy.envoy_model == "Envoy, phases: 2, phase mode: split, production CT"

    # Test that Ensemble commands raise FeatureNotAvailable
    with pytest.raises(EnvoyFeatureNotAvailable):
        await envoy.go_off_grid()
    with pytest.raises(EnvoyFeatureNotAvailable):
        await envoy.go_on_grid()

    await envoy.update()


@pytest.mark.asyncio
async def test_with_5_0_49_firmware(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify with 5.0.49 firmware."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "5.0.49"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(version, test_client_session)
    data = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert updater_features(envoy._updaters) == {
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
    assert data.system_production is not None
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
async def test_with_3_7_0_firmware(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify with 3.7.0 firmware."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "3.7.0"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # Verify the library does not support scraping to comply with ADR004
    with pytest.raises(EnvoyProbeFailed):
        await get_mock_envoy(version, test_client_session)

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
                data = await response.text()
            except ENDPOINT_PROBE_EXCEPTIONS:
                return None
            if "Since Installation" not in data:
                return None
            self._supported_features |= SupportedFeatures.PRODUCTION
            return self._supported_features

        async def update(self, envoy_data: EnvoyData) -> None:
            """Update the Envoy for this updater."""
            response = await self._request(URL_PRODUCTION)
            production_data = await response.text()
            envoy_data.raw[URL_PRODUCTION] = production_data
            envoy_data.system_production = (
                LegacyEnvoySystemProduction.from_production_legacy(production_data)
            )

    remove = register_updater(LegacyProductionScraper)
    assert LegacyProductionScraper in get_updaters()
    try:
        envoy = await get_mock_envoy(version, test_client_session)
        data = envoy.data
        assert data is not None
        assert envoy._supported_features is not None

        assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
        assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
        assert not (envoy._supported_features & SupportedFeatures.INVERTERS)
        assert updater_features(envoy._updaters) == {
            "LegacyProductionScraper": SupportedFeatures.PRODUCTION,
        }
        assert envoy.part_number == "800-00069-r05"

        assert not data.system_consumption
        assert data.system_production is not None
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
async def test_with_3_9_36_firmware_bad_auth(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify with 3.9.36 firmware with incorrect auth."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "3.9.36_bad_auth"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # Override production endpoints to return 401
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production",
        status=401,
        payload={
            "status": 401,
            "error": "",
            "info": "Authentication required",
            "moreInfo": "",
        },
        repeat=True,
    )
    override_mock(
        mock_aioresponse,
        "get",
        "http://127.0.0.1/api/v1/production",
        status=401,
        payload={
            "status": 401,
            "error": "",
            "info": "Authentication required",
            "moreInfo": "",
        },
        repeat=True,
    )

    with pytest.raises(EnvoyAuthenticationRequired):
        await get_mock_envoy(version, test_client_session)


@pytest.mark.asyncio
async def test_with_3_9_36_firmware_no_inverters(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify with 3.9.36 firmware with auth that does not allow inverters."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "3.9.36_bad_auth"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    # force auth failure on inverters
    mock_aioresponse.get(
        "https://127.0.0.1/api/v1/production/inverters",
        status=401,
        payload=await load_json_fixture(version, "api_v1_production_inverters"),
        repeat=True,
    )
    mock_aioresponse.get(
        "http://127.0.0.1/api/v1/production/inverters",
        status=401,
        payload=await load_json_fixture(version, "api_v1_production_inverters"),
        repeat=True,
    )

    envoy = await get_mock_envoy(version, test_client_session)
    data = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.INVERTERS)
    assert updater_features(envoy._updaters) == {
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
async def test_with_3_9_36_firmware(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify with 3.9.36 firmware."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "3.9.36"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    # no access to tariff
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/admin/lib/tariff",
        status=401,
        repeat=True,
    )
    override_mock(
        mock_aioresponse,
        "get",
        "http://127.0.0.1/admin/lib/tariff",
        status=401,
        repeat=True,
    )

    envoy = await get_mock_envoy(version, test_client_session)
    data = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert updater_features(envoy._updaters) == {
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
    assert data.system_production is not None
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
async def test_with_3_9_36_firmware_with_production_401(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify with 3.9.36 firmware when /production throws a 401."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "3.9.36"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    # force 401 on production
    mock_aioresponse.get("https://127.0.0.1/production", status=401, repeat=True)
    mock_aioresponse.get("http://127.0.0.1/production", status=401, repeat=True)

    envoy = await get_mock_envoy(version, test_client_session)
    data = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert updater_features(envoy._updaters) == {
        "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
        "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
    }
    assert envoy.part_number == "800-00069-r05"

    assert not data.system_consumption
    assert data.system_production is not None
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
async def test_with_3_9_36_firmware_with_production_and_production_json_401(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify with 3.9.36 firmware when /production and /production.json throws a 401."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "3.9.36"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    # force 401 on production
    override_mock(
        mock_aioresponse, "get", "https://127.0.0.1/production", status=401, repeat=True
    )
    override_mock(
        mock_aioresponse, "get", "http://127.0.0.1/production", status=401, repeat=True
    )
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/production.json",
        status=401,
        repeat=True,
    )
    override_mock(
        mock_aioresponse,
        "get",
        "http://127.0.0.1/production.json",
        status=401,
        repeat=True,
    )
    # Also need to override the API v1 endpoint
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production",
        status=401,
        repeat=True,
    )
    override_mock(
        mock_aioresponse,
        "get",
        "http://127.0.0.1/api/v1/production",
        status=401,
        repeat=True,
    )

    with pytest.raises(EnvoyAuthenticationRequired):
        await get_mock_envoy(version, test_client_session)


@pytest.mark.asyncio
async def test_with_3_8_10_firmware_with_meters_401(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify with 3.8.10 firmware when /ivp/meters throws a 401."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "3.8.10"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    override_mock(
        mock_aioresponse, "get", "https://127.0.0.1/ivp/meters", status=401, repeat=True
    )
    override_mock(
        mock_aioresponse, "get", "http://127.0.0.1/ivp/meters", status=401, repeat=True
    )
    caplog.set_level(logging.DEBUG)
    await get_mock_envoy(version, test_client_session)
    assert "Skipping meters endpoint as user does not have access to" in caplog.text


@pytest.mark.asyncio
async def test_with_3_17_3_firmware(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify with 3.17.3 firmware."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "3.17.3"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    envoy = await get_mock_envoy(version, test_client_session)
    data = envoy.data
    assert data is not None
    assert envoy._supported_features is not None

    assert not (envoy._supported_features & SupportedFeatures.TOTAL_CONSUMPTION)
    assert not (envoy._supported_features & SupportedFeatures.NET_CONSUMPTION)
    assert envoy._supported_features & SupportedFeatures.INVERTERS
    assert updater_features(envoy._updaters) == {
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
    assert data.system_production is not None
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
async def test_with_3_17_3_firmware_zero_production(
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify with 3.17.3 firmware."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)
    version = "3.17.3"
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)

    # Get envoy and let it probe with good data
    envoy = await get_mock_envoy(version, test_client_session, update=True)

    # Now override the production endpoint to return zeros for the next update
    override_mock(
        mock_aioresponse,
        "get",
        "https://127.0.0.1/api/v1/production",
        status=200,
        payload={
            "wattHoursToday": 0,
            "wattHoursSevenDays": 0,
            "wattHoursLifetime": 0,
            "wattsNow": 0,
        },
        repeat=True,
    )
    override_mock(
        mock_aioresponse,
        "get",
        "http://127.0.0.1/api/v1/production",
        status=200,
        payload={
            "wattHoursToday": 0,
            "wattHoursSevenDays": 0,
            "wattHoursLifetime": 0,
            "wattsNow": 0,
        },
        repeat=True,
    )

    # Now update should fail with poor data quality
    with pytest.raises(EnvoyPoorDataQuality):
        await envoy.update()
