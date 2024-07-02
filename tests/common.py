"""common test functions for pyenphase."""

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


def load_fixture(version: str, name: str) -> str:
    """Return fixture file content as text."""
    with open(_fixtures_dir() / version / name) as read_in:
        return read_in.read()


def load_json_fixture(version: str, name: str) -> dict[str, Any]:
    """Return fixture file content as JSON."""
    return orjson.loads(load_fixture(version, name))


def load_json_list_fixture(version: str, name: str) -> list[dict[str, Any]]:
    """Return list[json] fixture file content as json"""
    return orjson.loads(load_fixture(version, name))


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


def prep_envoy(
    version: str,
    info: bool = False,  #: if true mock info
    meters: bool = True,  #: if true mock meters
    inverters: bool = True,  #: if true mock inverters
) -> None:
    """setup response mocks for envoy requests."""
    path = f"{_fixtures_dir()}/{version}"
    files = [f for f in listdir(path) if isfile(join(path, f))]

    if info:
        respx.get("/info").mock(
            return_value=Response(200, text=load_fixture(version, "info"))
        )

    if meters:
        respx.get("/ivp/meters").mock(return_value=Response(200, text="[]"))

    respx.get("/production").mock(
        return_value=Response(200, text=load_fixture(version, "production"))
    )
    respx.get("/production.json").mock(
        return_value=Response(200, text=load_fixture(version, "production.json"))
    )
    respx.get("/api/v1/production").mock(
        return_value=Response(200, json=load_json_fixture(version, "api_v1_production"))
    )
    if inverters:
        respx.get("/api/v1/production/inverters").mock(
            return_value=Response(
                200, json=load_json_fixture(version, "api_v1_production_inverters")
            )
        )
    respx.get("/ivp/ensemble/inventory").mock(return_value=Response(200, json=[]))

    if "admin_lib_tariff" in files:
        try:
            json_data = load_json_fixture(version, "admin_lib_tariff")
        except json.decoder.JSONDecodeError:
            json_data = None
        respx.get("/admin/lib/tariff").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/admin/lib/tariff").mock(return_value=Response(401))

    if "ivp_ss_gen_config" in files:
        try:
            json_data = load_json_fixture(version, "ivp_ss_gen_config")
        except json.decoder.JSONDecodeError:
            json_data = {}
        respx.get("/ivp/ss/gen_config").mock(return_value=Response(200, json=json_data))
    else:
        respx.get("/ivp/ss/gen_config").mock(return_value=Response(200, json={}))


def updater_features(updaters: list[EnvoyUpdater]) -> dict[str, SupportedFeatures]:
    """Return the updater supported features flags"""
    return {type(updater).__name__: updater._supported_features for updater in updaters}
