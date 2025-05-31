"""common test functions for pyenphase."""

import asyncio
import json
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
    """
    Asynchronously retrieves the list of fixture filenames for a given version.

    Args:
        version: The version subdirectory to search for fixture files.

    Returns:
        A list of fixture filenames found in the specified version directory.
    """
    path: str = f"{_fixtures_dir()}/{version}"
    files: list[str] = await asyncio.get_running_loop().run_in_executor(
        None, _fixture_files, path
    )
    return files


def start_7_firmware_mock(mock_aioresponse: aioresponses) -> None:
    """
    Sets up repeated mock HTTP responses for Enlighten login, token, and Envoy JWT check endpoints.

    This function configures the provided `aioresponses` mock object to simulate successful authentication and token retrieval for firmware version 7 test scenarios. It mocks POST requests to Enlighten login endpoints (with and without a trailing '?'), the token endpoint, and a GET request to the Envoy JWT check endpoint, all with repeated responses.
    """
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
    client_session: aiohttp.ClientSession, update: bool = True
) -> Envoy:
    """
    Creates and returns a mock Envoy instance using the provided aiohttp client session.

    The Envoy is initialized, set up, authenticated with test credentials, and optionally updated twice to simulate repeated data refreshes.

    Args:
        client_session: The aiohttp client session to use for HTTP requests.
        update: If True, performs two consecutive update calls on the Envoy.

    Returns:
        A mock Envoy instance ready for testing.
    """
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
    """
    Returns the number of matched requests and the data payload of the last request for a given HTTP method and URL from the aioresponses mock.

    Args:
        method: The HTTP method to match (e.g., "GET", "POST").
        url: The URL substring to match against recorded requests.

    Returns:
        A tuple containing the count of matched requests and the data payload of the last matched request as bytes. If no requests match, returns (0, b"").
    """
    requests = [
        req
        for req in mock_aioresponse.requests.keys()
        if req[0] == method and url in str(req[1])
    ]
    if not requests:
        return 0, b""
    return len(requests), mock_aioresponse.requests[requests[-1]][-1].kwargs.get("data")


def mock_response(
    mock_aioresponse: aioresponses,
    method: str,
    url: str,
    reset: bool = False,
    **kwargs: Any,
) -> None:
    """
    Adds a mock HTTP response for the specified method and URL using aioresponses.

    If reset is True, existing mocks for the given method and URL are removed before adding the new mock.
    """
    if reset:
        return override_mock(
            mock_aioresponse,
            method,
            url,
            **kwargs,
        )
    getattr(mock_aioresponse, method.lower())(url, **kwargs)


def override_mock(
    mock_aioresponse: aioresponses, method: str, url: str, **kwargs: Any
) -> None:
    """
    Removes existing mocks for the specified HTTP method and URL from the aioresponses mock, then adds a new mock with the provided parameters.

    This ensures that only the latest mock for the given method and URL is active, replacing any previous mocks.
    """
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
    """
    Constructs the base URL for a given firmware version and host, using HTTPS if the version meets or exceeds the minimum required for token authentication.

    Args:
        version: The firmware version string, possibly with suffixes.
        host: The hostname or IP address of the Envoy device.

    Returns:
        The base URL as a string, prefixed with "http://" or "https://".
    """
    return f"http{'s' if AwesomeVersion(version.split('_')[0]) >= AUTH_TOKEN_MIN_VERSION else ''}://{host}"


async def prep_envoy(
    mock_aioresponse: aioresponses,
    host: str,
    version: str,  #: name of version folder to read fixtures from
) -> list[str]:
    """
    Sets up mocked HTTP responses for Envoy device endpoints using available fixture files.

    This function configures the provided `aioresponses` mock object to simulate Envoy API responses for a specific host and firmware version. It loads fixture files for the given version and mocks GET, POST, and PUT requests to various endpoints, returning appropriate payloads, bodies, or status codes based on the presence and content of each fixture. Endpoints include `/info`, `/ivp/meters`, `/production`, `/api/v1/production`, `/ivp/ensemble/inventory`, `/admin/lib/tariff`, and others. If a fixture is missing or contains invalid JSON, fallback responses such as 404 or empty payloads are used.

    Args:
        mock_aioresponse: The `aioresponses` mock object to configure.
        host: The hostname of the Envoy device.
        version: The firmware version directory to load fixtures from.

    Returns:
        A list of fixture filenames found for the specified version.
    """
    files: list[str] = await fixture_files(version)

    # Helper to create full URLs
    full_host = endpoint_path(version, host)

    def url(path: str) -> str:
        """
        Constructs a full URL by appending the given path to the base host URL.

        Args:
            path: The URL path to append.

        Returns:
            The complete URL as a string.
        """
        return f"{full_host}{path}"

    def url_https(path: str) -> str:
        Constructs a full HTTPS URL by concatenating the host and the given path.

        Args:
            path: The URL path to append to the host.

        Returns:
            The complete HTTPS URL as a string.
        return f"https://{host}{path}"

    def url_http(path: str) -> str:
        """
        Constructs an HTTP URL by concatenating the host and the given path.

        Args:
            path: The URL path to append to the host.

        Returns:
            The full HTTP URL as a string.
        """
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
    return files


def updater_features(updaters: list[EnvoyUpdater]) -> dict[str, SupportedFeatures]:
    """Return the updater supported features flags"""
    return {type(updater).__name__: updater._supported_features for updater in updaters}
