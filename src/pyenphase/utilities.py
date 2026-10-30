"""Pyenphase helpers."""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import aiohttp

from .const import DEVICE_TYPES, FIXTURE_STATE
from .exceptions import EnvoyClientClosedError

_LOGGER = logging.getLogger(__name__)


def raise_on_client_closed(client: aiohttp.ClientSession, endpoint: str) -> None:
    """Raise EnvoyClientClosedError if client is closed"""
    if client.closed:
        _LOGGER.error(
            "Request to %s aborted because client is closed.",
            endpoint,
        )
        raise EnvoyClientClosedError("Session is closed before request is issued")


@contextmanager
def translate_client_closed(
    client: aiohttp.ClientSession,
) -> Generator[None, None, None]:
    """Context manager for requests handling session closed"""
    try:
        yield
    except RuntimeError as err:
        if client.closed:
            raise EnvoyClientClosedError("Session is closed") from err
        raise


def usable_fixture(
    endpoint: str, fixtures: dict[str, Any], kind: type
) -> FIXTURE_STATE:
    """
    Verify fixture data is usable for intent.

    Verify if fixtures[endpoint] exists and is of expected data type.

    Verify if endpoint has companion fixtures[endpoint_log] with [code]
    field and if so, its value is 200. If either is missing let it default
    to 200.

    - If endpoint is not present return :any:`FIXTURE_STATE.MISSING`.
    - If endpoint is present, of specified type and code is 200,
      return :any:`FIXTURE_STATE.USABLE`.
    - If endpoint is present but not of specified
      data type, return :any:`FIXTURE_STATE.TYPE_ERROR`.
    - Otherwise return :any:`FIXTURE_STATE.UNUSABLE`.

    The UNUSABLE state signals a non-200 HTTP code is found,
    while the data is of expected type. Valid information may
    or may not be present, the state just signals the HTTP code.

    :param endpoint: endpoint in fixtures to verify
    :param fixtures: dict keyed by endpoint names and
        endpoint data as value
    :param kind: expected data type of fixtures[endpoint]
    :return: evaluated state of endpoint entry in fixtures
    """
    if endpoint not in fixtures:
        return FIXTURE_STATE.MISSING
    code_ok = fixtures.get(f"{endpoint}_log", {}).get("code", 200) == 200
    if not isinstance(fixtures.get(endpoint), kind):
        return FIXTURE_STATE.TYPE_ERROR if code_ok else FIXTURE_STATE.UNUSABLE
    return FIXTURE_STATE.USABLE if code_ok else FIXTURE_STATE.UNUSABLE


def device_type_name(data: dict[Any, Any], key: str) -> str:
    """Get int key value from dict, map to name, default to UNKNOWN if missing."""
    return DEVICE_TYPES.get(
        (v if isinstance(v := data.get(key), int) else 0), "UNKNOWN"
    )


def safe_error_description(err: BaseException) -> str:
    """Build safe error text from error"""
    return f"{type(err).__name__}({err.args[0] if err.args else ''})"
