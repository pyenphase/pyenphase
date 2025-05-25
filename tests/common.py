"""common test functions for pyenphase."""

import asyncio
import json
from os import listdir
from os.path import isfile, join
from pathlib import Path
from typing import Any

import orjson
from aioresponses import aioresponses

from pyenphase import Envoy
from pyenphase.envoy import SupportedFeatures
from pyenphase.updaters.base import EnvoyUpdater


def _fixtures_dir() -> Path:
    """Return location of fixture folder."""
    return Path(__file__).parent / "fixtures"


def _load_fixture(path: str) -> str:
    """Return fixture file content as text."""
    with open(path) as read_in:
        return read_in.read()


async def load_fixture(version: str, name: str) -> str:
    """Return fixture file content as text in executor."""
    path: str = f"{_fixtures_dir()}/{version}/{name}"
    content: str = await asyncio.get_running_loop().run_in_executor(
        None, _load_fixture, path
    )
    return content


async def load_json_fixture(version: str, name: str) -> dict[str, Any]:
    """Return fixture file content as JSON."""
    json: str = await load_fixture(version, name)
    return orjson.loads(json)


async def load_json_list_fixture(version: str, name: str) -> list[dict[str, Any]]:
    """Return list[json] fixture file content as json"""
    json: str = await load_fixture(version, name)
    return orjson.loads(json)


def _fixture_files(path: str) -> list[str]:
    """Get fixture files list"""
    return [f for f in listdir(path) if isfile(join(path, f))]


async def fixture_files(version: str) -> list[str]:
    """Get fixture files list in executor"""
    path: str = f"{_fixtures_dir()}/{version}"
    files: list[str] = await asyncio.get_running_loop().run_in_executor(
        None, _fixture_files, path
    )
    return files


def start_7_firmware_mock(mock_aioresponse: aioresponses) -> None:
    """Setup response mocks for Enlighten and Envoy token requests."""
    # Use repeat=True since auth might create its own session
    # Mock both with and without the trailing ?
    mock_aioresponse.post(
        "https://enlighten.enphaseenergy.com/login/login.json?",
        status=200,
        payload={
            "session_id": "1234567890",
            "user_id": "1234567890",
            "user_name": "test",
            "first_name": "Test",
            "is_consumer": True,
            "manager_token": "1234567890",
        },
        repeat=True,
    )
    mock_aioresponse.post(
        "https://enlighten.enphaseenergy.com/login/login.json",
        status=200,
        payload={
            "session_id": "1234567890",
            "user_id": "1234567890",
            "user_name": "test",
            "first_name": "Test",
            "is_consumer": True,
            "manager_token": "1234567890",
        },
        repeat=True,
    )
    mock_aioresponse.post(
        "https://entrez.enphaseenergy.com/tokens",
        status=200,
        body="token",
        repeat=True,
    )
    # Mock the JWT check endpoint on the Envoy
    mock_aioresponse.get("https://127.0.0.1/auth/check_jwt", status=200, repeat=True)


async def get_mock_envoy(version: str, client_session, update: bool = True):  # type: ignore[no-untyped-def]
    """Return a mock Envoy."""
    host = "127.0.0.1"
    envoy = Envoy(host, client=client_session)
    await envoy.setup()
    await envoy.authenticate("username", "password")
    if update:
        await envoy.update()
        await envoy.update()  # make sure we can update twice
    return envoy


async def prep_envoy(
    mock_aioresponse: aioresponses,
    host: str,
    version: str,  #: name of version folder to read fixtures from
) -> list[str]:
    """Setup response mocks for envoy requests and return list of found mock files."""
    files: list[str] = await fixture_files(version)

    # Helper to create full URLs
    def url(path: str) -> str:
        return f"https://{host}{path}"

    def url_http(path: str) -> str:
        return f"http://{host}{path}"

    mock_aioresponse.get(
        url("/info"), status=200, body=await load_fixture(version, "info"), repeat=True
    )
    mock_aioresponse.get(
        url_http("/info"),
        status=200,
        body=await load_fixture(version, "info"),
        repeat=True,
    )
    mock_aioresponse.get(url("/info.xml"), status=200, body="", repeat=True)

    if "ivp_meters" in files:
        try:
            mock_aioresponse.get(
                url("/ivp/meters"),
                status=200,
                payload=(await load_json_fixture(version, "ivp_meters")),
                repeat=True,
            )
            mock_aioresponse.get(
                url_http("/ivp/meters"),
                status=200,
                payload=(await load_json_fixture(version, "ivp_meters")),
                repeat=True,
            )
        except json.decoder.JSONDecodeError:
            # v3 fw with html return 401
            mock_aioresponse.get(url("/ivp/meters"), status=401, repeat=True)
            mock_aioresponse.get(url_http("/ivp/meters"), status=401, repeat=True)
    else:
        mock_aioresponse.get(url("/ivp/meters"), status=404, repeat=True)
        mock_aioresponse.get(url_http("/ivp/meters"), status=404, repeat=True)

    if "ivp_meters_readings" in files:
        mock_aioresponse.get(
            url("/ivp/meters/readings"),
            status=200,
            payload=await load_json_fixture(version, "ivp_meters_readings"),
            repeat=True,
        )
    else:
        mock_aioresponse.get(url("/ivp/meters/readings"), status=404, repeat=True)

    if "production" in files:
        try:
            json_data = await load_json_fixture(version, "production")
            mock_aioresponse.get(
                url("/production"), status=200, payload=json_data, repeat=True
            )
            mock_aioresponse.get(
                url_http("/production"), status=200, payload=json_data, repeat=True
            )
        except json.decoder.JSONDecodeError:
            # v3 fw reports production in html format
            mock_aioresponse.get(
                url("/production"),
                status=200,
                body=await load_fixture(version, "production"),
                repeat=True,
            )
            mock_aioresponse.get(
                url_http("/production"),
                status=200,
                body=await load_fixture(version, "production"),
                repeat=True,
            )
    else:
        mock_aioresponse.get(url("/production"), status=404, repeat=True)
        mock_aioresponse.get(url_http("/production"), status=404, repeat=True)

    if "production.json" in files:
        try:
            json_data = await load_json_fixture(version, "production.json")
            mock_aioresponse.get(
                url("/production.json"), status=200, payload=json_data, repeat=True
            )
            mock_aioresponse.get(
                url_http("/production.json"), status=200, payload=json_data, repeat=True
            )
            mock_aioresponse.get(
                url("/production.json?details=1"),
                status=200,
                payload=json_data,
                repeat=True,
            )
            mock_aioresponse.get(
                url_http("/production.json?details=1"),
                status=200,
                payload=json_data,
                repeat=True,
            )
        except json.decoder.JSONDecodeError:
            mock_aioresponse.get(url("/production.json"), status=404, repeat=True)
            mock_aioresponse.get(url_http("/production.json"), status=404, repeat=True)
            mock_aioresponse.get(
                url("/production.json?details=1"), status=404, repeat=True
            )
            mock_aioresponse.get(
                url_http("/production.json?details=1"), status=404, repeat=True
            )
    else:
        mock_aioresponse.get(url("/production.json"), status=404, repeat=True)
        mock_aioresponse.get(url("/production.json?details=1"), status=404, repeat=True)

    if "api_v1_production" in files:
        mock_aioresponse.get(
            url("/api/v1/production"),
            status=200,
            payload=await load_json_fixture(version, "api_v1_production"),
            repeat=True,
        )
        mock_aioresponse.get(
            url_http("/api/v1/production"),
            status=200,
            payload=await load_json_fixture(version, "api_v1_production"),
            repeat=True,
        )
    else:
        mock_aioresponse.get(url("/api/v1/production"), status=404, repeat=True)
        mock_aioresponse.get(url_http("/api/v1/production"), status=404, repeat=True)

    if "api_v1_production_inverters" in files:
        mock_aioresponse.get(
            url("/api/v1/production/inverters"),
            status=200,
            payload=await load_json_fixture(version, "api_v1_production_inverters"),
            repeat=True,
        )
        mock_aioresponse.get(
            url_http("/api/v1/production/inverters"),
            status=200,
            payload=await load_json_fixture(version, "api_v1_production_inverters"),
            repeat=True,
        )
    else:
        mock_aioresponse.get(
            url("/api/v1/production/inverters"), status=404, repeat=True
        )
        mock_aioresponse.get(
            url_http("/api/v1/production/inverters"), status=404, repeat=True
        )

    if "ivp_ensemble_inventory" in files:
        mock_aioresponse.get(
            url("/ivp/ensemble/inventory"),
            status=200,
            payload=await load_json_fixture(version, "ivp_ensemble_inventory"),
            repeat=True,
        )
        mock_aioresponse.get(
            url_http("/ivp/ensemble/inventory"),
            status=200,
            payload=await load_json_fixture(version, "ivp_ensemble_inventory"),
            repeat=True,
        )
    else:
        mock_aioresponse.get(url("/ivp/ensemble/inventory"), status=404, repeat=True)
        mock_aioresponse.get(
            url_http("/ivp/ensemble/inventory"), status=404, repeat=True
        )

    if "ivp_ensemble_dry_contacts" in files:
        try:
            json_data = await load_json_fixture(version, "ivp_ensemble_dry_contacts")
        except json.decoder.JSONDecodeError:
            json_data = {}
        mock_aioresponse.get(
            url("/ivp/ensemble/dry_contacts"),
            status=200,
            payload=json_data,
            repeat=True,
        )
        mock_aioresponse.post(
            url("/ivp/ensemble/dry_contacts"),
            status=200,
            payload=json_data,
            repeat=True,
        )

    if "ivp_ss_dry_contact_settings" in files:
        try:
            json_data = await load_json_fixture(version, "ivp_ss_dry_contact_settings")
        except json.decoder.JSONDecodeError:
            json_data = {}
        mock_aioresponse.get(
            url("/ivp/ss/dry_contact_settings"),
            status=200,
            payload=json_data,
            repeat=True,
        )
        mock_aioresponse.post(
            url("/ivp/ss/dry_contact_settings"),
            status=200,
            payload=json_data,
            repeat=True,
        )

    if "ivp_ensemble_power" in files:
        try:
            json_data = await load_json_fixture(version, "ivp_ensemble_power")
        except json.decoder.JSONDecodeError:
            json_data = {}
        mock_aioresponse.get(
            url("/ivp/ensemble/power"), status=200, payload=json_data, repeat=True
        )

    if "ivp_ensemble_secctrl" in files:
        try:
            json_data = await load_json_fixture(version, "ivp_ensemble_secctrl")
        except json.decoder.JSONDecodeError:
            json_data = {}
        mock_aioresponse.get(
            url("/ivp/ensemble/secctrl"), status=200, payload=json_data, repeat=True
        )

    if "admin_lib_tariff" in files:
        try:
            json_data = await load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = {}
        mock_aioresponse.get(
            url("/admin/lib/tariff"), status=200, payload=json_data, repeat=True
        )
        mock_aioresponse.get(
            url_http("/admin/lib/tariff"), status=200, payload=json_data, repeat=True
        )
        mock_aioresponse.put(
            url("/admin/lib/tariff"), status=200, payload=json_data, repeat=True
        )
    else:
        mock_aioresponse.get(url("/admin/lib/tariff"), status=404, repeat=True)

    if "ivp_ss_gen_config" in files:
        try:
            json_data = await load_json_fixture(version, "ivp_ss_gen_config")
        except json.decoder.JSONDecodeError:
            json_data = {}
        mock_aioresponse.get(
            url("/ivp/ss/gen_config"), status=200, payload=json_data, repeat=True
        )
    else:
        mock_aioresponse.get(
            url("/ivp/ss/gen_config"), status=200, payload={}, repeat=True
        )

    if "home" in files:
        mock_aioresponse.get(
            url("/home"),
            status=200,
            payload=await load_json_fixture(version, "home"),
            repeat=True,
        )
    else:
        mock_aioresponse.get(url("/home"), status=404, repeat=True)
    return files


def updater_features(updaters: list[EnvoyUpdater]) -> dict[str, SupportedFeatures]:
    """Return the updater supported features flags"""
    return {type(updater).__name__: updater._supported_features for updater in updaters}
