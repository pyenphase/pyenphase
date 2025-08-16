"""common test functions for pyenphase."""

import asyncio
import json
import logging
from collections.abc import Generator
from contextlib import contextmanager
from os import listdir
from os.path import isfile, join
from pathlib import Path
from typing import Any

import aiohttp
import orjson
from aioresponses import aioresponses
from awesomeversion import AwesomeVersion

from pyenphase import AUTH_TOKEN_MIN_VERSION, Envoy
from pyenphase.envoy import SupportedFeatures
from pyenphase.updaters.base import EnvoyUpdater


@contextmanager
def temporary_log_level(logger_name: str, level: int) -> Generator[None, None, None]:
    """Temporarily change the log level of a logger."""
    logger = logging.getLogger(logger_name)
    original_level = logger.level
    logger.setLevel(level)
    try:
        yield
    finally:
        logger.setLevel(original_level)


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


async def get_mock_envoy(
    client_session: aiohttp.ClientSession | None, update: bool = True
) -> Envoy:
    """Return a mock Envoy."""
    host = "127.0.0.1"
    envoy = Envoy(host, client=client_session)
    await envoy.setup()
    await envoy.authenticate("username", "password")
    if update:
        await envoy.update()
        await envoy.update()  # make sure we can update twice
    return envoy


def latest_request(
    mock_aioresponse: aioresponses, method: str, url: str
) -> tuple[int, bytes]:
    """Return count of matched request and last request data."""
    requests = [
        req
        for req in mock_aioresponse.requests.keys()
        if req[0] == method and url in str(req[1])
    ]
    if not requests:
        return 0, b""
    return len(requests), mock_aioresponse.requests[requests[-1]][-1].kwargs.get("data")


def override_mock(
    mock_aioresponse: aioresponses, method: str, url: str, **kwargs: Any
) -> None:
    """Override an existing mock by removing it first and adding a new one."""
    from yarl import URL

    url_obj = URL(url)

    # Remove existing mocks for this URL and method from _matches
    keys_to_remove = []
    for key, matcher in mock_aioresponse._matches.items():
        # Check if this matches our URL and method
        url_matches = False
        if hasattr(matcher.url_or_pattern, "match"):
            # It's a regex pattern
            url_matches = bool(matcher.url_or_pattern.match(str(url_obj)))
        else:
            # It's a URL
            url_matches = str(matcher.url_or_pattern).rstrip("/") == str(
                url_obj
            ).rstrip("/")

        if url_matches and matcher.method.lower() == method.lower():
            keys_to_remove.append(key)

    # Remove the matching mocks
    for key in keys_to_remove:
        del mock_aioresponse._matches[key]

    # Add the new mock
    getattr(mock_aioresponse, method.lower())(url, **kwargs)


def endpoint_path(version: str, host: str) -> str:
    return f"http{'s' if AwesomeVersion(version.split('_')[0]) >= AUTH_TOKEN_MIN_VERSION else ''}://{host}"


async def prep_envoy(
    mock_aioresponse: aioresponses,
    host: str,
    version: str,  #: name of version folder to read fixtures from
) -> list[str]:
    """Setup response mocks for envoy requests and return list of found mock files."""
    files: list[str] = await fixture_files(version)

    # Helper to create full URLs
    full_host = endpoint_path(version, host)

    def url(path: str) -> str:
        return f"{full_host}{path}"

    def url_https(path: str) -> str:
        return f"https://{host}{path}"

    def url_http(path: str) -> str:
        return f"http://{host}{path}"

    mock_aioresponse.get(
        url_http("/info"),
        status=200,
        body=await load_fixture(version, "info"),
        repeat=True,
    )
    mock_aioresponse.get(
        url_https("/info"),
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
        except json.decoder.JSONDecodeError:
            # v3 fw with html return 401
            mock_aioresponse.get(url("/ivp/meters"), status=401, repeat=True)
            # mock_aioresponse.get(url_http("/ivp/meters"), status=401, repeat=True)
    else:
        mock_aioresponse.get(url("/ivp/meters"), status=404, repeat=True)
        # mock_aioresponse.get(url_http("/ivp/meters"), status=404, repeat=True)

    if "ivp_meters_readings" in files:
        mock_aioresponse.get(
            url("/ivp/meters/readings"),
            status=200,
            payload=await load_json_fixture(version, "ivp_meters_readings"),
            repeat=True,
        )
    else:
        mock_aioresponse.get(url("/ivp/meters/readings"), status=404, repeat=True)
        # mock_aioresponse.get(url_http("/ivp/meters/readings"), status=404, repeat=True)

    if "production" in files:
        try:
            json_data = await load_json_fixture(version, "production")
            mock_aioresponse.get(
                url("/production"), status=200, payload=json_data, repeat=True
            )
        except json.decoder.JSONDecodeError:
            # v3 fw reports production in html format
            mock_aioresponse.get(
                url("/production"),
                status=200,
                body=await load_fixture(version, "production"),
                repeat=True,
            )
    else:
        mock_aioresponse.get(url("/production"), status=404, repeat=True)
        # mock_aioresponse.get(url_http("/production"), status=404, repeat=True)

    if "production.json" in files:
        try:
            json_data = await load_json_fixture(version, "production.json")
            mock_aioresponse.get(
                url("/production.json"), status=200, payload=json_data, repeat=True
            )
            mock_aioresponse.get(
                url("/production.json?details=1"),
                status=200,
                payload=json_data,
                repeat=True,
            )
        except json.decoder.JSONDecodeError:
            mock_aioresponse.get(url("/production.json"), status=404, repeat=True)
            # mock_aioresponse.get(url_http("/production.json"), status=404, repeat=True)
            mock_aioresponse.get(
                url("/production.json?details=1"), status=404, repeat=True
            )
    else:
        mock_aioresponse.get(url("/production.json"), status=404, repeat=True)

    if "api_v1_production" in files:
        # Check if this is a bad_auth version by looking at the fixture content
        api_v1_prod_data = await load_json_fixture(version, "api_v1_production")
        status = (
            401
            if "status" in api_v1_prod_data and api_v1_prod_data["status"] == 401
            else 200
        )

        mock_aioresponse.get(
            url("/api/v1/production"),
            status=status,
            payload=api_v1_prod_data,
            repeat=True,
        )
    else:
        mock_aioresponse.get(url("/api/v1/production"), status=404, repeat=True)

    if "api_v1_production_inverters" in files:
        # Check if this is a bad_auth version by looking at the fixture content
        api_v1_inv_data = await load_json_fixture(
            version, "api_v1_production_inverters"
        )
        status = (
            401
            if isinstance(api_v1_inv_data, dict)
            and "status" in api_v1_inv_data
            and api_v1_inv_data["status"] == 401
            else 200
        )

        mock_aioresponse.get(
            url("/api/v1/production/inverters"),
            status=status,
            payload=api_v1_inv_data,
            repeat=True,
        )
    else:
        mock_aioresponse.get(
            url("/api/v1/production/inverters"), status=404, repeat=True
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

    if "ivp_pdm_device_data" in files:
        mock_aioresponse.get(
            url("/ivp/pdm/device_data"),
            status=200,
            payload=await load_json_fixture(version, "ivp_pdm_device_data"),
            repeat=True,
        )
    else:
        mock_aioresponse.get(url("/ivp/pdm/device_data"), status=404, repeat=True)

    return files


def updater_features(updaters: list[EnvoyUpdater]) -> dict[str, SupportedFeatures]:
    """Return the updater supported features flags"""
    return {type(updater).__name__: updater._supported_features for updater in updaters}
