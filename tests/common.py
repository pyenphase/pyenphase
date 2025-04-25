"""common test functions for pyenphase."""

import asyncio
import json
from os import listdir
from os.path import isfile, join
from pathlib import Path
from typing import Any

import orjson
import respx
from httpx import Response

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


def start_7_firmware_mock() -> None:
    """Setup response mocks for Enlighten and Envoy token requests."""
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


async def get_mock_envoy(update: bool = True):  # type: ignore[no-untyped-def]
    """Return a mock Envoy."""
    envoy = Envoy("127.0.0.1")
    await envoy.setup()
    await envoy.authenticate("username", "password")
    if update:
        await envoy.update()
        await envoy.update()  # make sure we can update twice
    return envoy


async def prep_envoy(
    version: str,  #: name of version folder to read fixtures from
) -> list[str]:
    """Setup response mocks for envoy requests and return list of found mock files."""
    files: list[str] = await fixture_files(version)

    respx.get("/info").mock(
        return_value=Response(200, text=await load_fixture(version, "info"))
    )
    respx.get("/info.xml").mock(return_value=Response(200, text=""))

    if "ivp_meters" in files:
        try:
            respx.get("/ivp/meters").mock(
                return_value=Response(
                    200, json=(await load_json_fixture(version, "ivp_meters"))
                )
            )
        except json.decoder.JSONDecodeError:
            # v3 fw with html return 401
            respx.get("ivp_meters").mock(return_value=Response(401))
    else:
        respx.get("/ivp/meters").mock(return_value=Response(404))

    if "ivp_meters_readings" in files:
        respx.get("/ivp/meters/readings").mock(
            return_value=Response(
                200, json=await load_json_fixture(version, "ivp_meters_readings")
            )
        )
    else:
        respx.get("/ivp/meters/readings").mock(return_value=Response(404))

    if "production" in files:
        try:
            json_data = await load_json_fixture(version, "production")
            respx.get("/production").mock(return_value=Response(200, json=json_data))
        except json.decoder.JSONDecodeError:
            # v3 fw reports production in html format
            respx.get("/production").mock(
                return_value=Response(
                    200, text=await load_fixture(version, "production")
                )
            )
    else:
        respx.get("/production").mock(return_value=Response(404))

    if "production.json" in files:
        try:
            respx.get("/production.json").mock(
                return_value=Response(
                    200, json=await load_json_fixture(version, "production.json")
                )
            )
            respx.get("/production.json?details=1").mock(
                return_value=Response(
                    200, json=await load_json_fixture(version, "production.json")
                )
            )
        except json.decoder.JSONDecodeError:
            respx.get("/production.json").mock(return_value=Response(404))
            respx.get("/production.json?details=1").mock(return_value=Response(404))
    else:
        respx.get("/production.json").mock(return_value=Response(404))
        respx.get("/production.json?details=1").mock(return_value=Response(404))

    if "api_v1_production" in files:
        respx.get("/api/v1/production").mock(
            return_value=Response(
                200, json=await load_json_fixture(version, "api_v1_production")
            )
        )
    else:
        respx.get("/api/v1/production").mock(return_value=Response(404))

    if "api_v1_production_inverters" in files:
        respx.get("/api/v1/production/inverters").mock(
            return_value=Response(
                200,
                json=await load_json_fixture(version, "api_v1_production_inverters"),
            )
        )
    else:
        respx.get("/api/v1/production/inverters").mock(return_value=Response(404))

    if "ivp_ensemble_inventory" in files:
        respx.get("/ivp/ensemble/inventory").mock(
            return_value=Response(
                200, json=await load_json_fixture(version, "ivp_ensemble_inventory")
            )
        )
    else:
        respx.get("/ivp/ensemble/inventory").mock(return_value=Response(404))

    if "ivp_ensemble_dry_contacts" in files:
        try:
            json_data = await load_json_fixture(version, "ivp_ensemble_dry_contacts")
        except json.decoder.JSONDecodeError:
            json_data = {}
        respx.get("/ivp/ensemble/dry_contacts").mock(
            return_value=Response(200, json=json_data)
        )
        respx.post("/ivp/ensemble/dry_contacts").mock(
            return_value=Response(200, json=json_data)
        )

    if "ivp_ss_dry_contact_settings" in files:
        try:
            json_data = await load_json_fixture(version, "ivp_ss_dry_contact_settings")
        except json.decoder.JSONDecodeError:
            json_data = {}
        respx.get("/ivp/ss/dry_contact_settings").mock(
            return_value=Response(200, json=json_data)
        )
        respx.post("/ivp/ss/dry_contact_settings").mock(
            return_value=Response(200, json=json_data)
        )

    if "ivp_ensemble_power" in files:
        try:
            json_data = await load_json_fixture(version, "ivp_ensemble_power")
        except json.decoder.JSONDecodeError:
            json_data = {}
        respx.get("/ivp/ensemble/power").mock(
            return_value=Response(200, json=json_data)
        )

    if "ivp_ensemble_secctrl" in files:
        try:
            json_data = await load_json_fixture(version, "ivp_ensemble_secctrl")
        except json.decoder.JSONDecodeError:
            json_data = {}
        respx.get("/ivp/ensemble/secctrl").mock(
            return_value=Response(200, json=json_data)
        )

    if "admin_lib_tariff" in files:
        try:
            json_data = await load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = {}
        respx.get("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
        respx.put("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/admin/lib/tariff").mock(return_value=Response(404))

    if "ivp_ss_gen_config" in files:
        try:
            json_data = await load_json_fixture(version, "ivp_ss_gen_config")
        except json.decoder.JSONDecodeError:
            json_data = {}
        respx.get("/ivp/ss/gen_config").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/ivp/ss/gen_config").mock(return_value=Response(200, json={}))

    if "home" in files:
        respx.get("/home").mock(
            return_value=Response(200, json=await load_json_fixture(version, "home"))
        )
    else:
        respx.get("home").mock(return_value=Response(404))

    return files


def updater_features(updaters: list[EnvoyUpdater]) -> dict[str, SupportedFeatures]:
    """Return the updater supported features flags"""
    return {type(updater).__name__: updater._supported_features for updater in updaters}
