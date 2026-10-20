"""Pyenphase helpers."""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import aiohttp

from .const import DEVICE_TYPES
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


def usable_fixture(endpoint: str, fixtures: dict[str, Any], kind: type) -> bool:
    """
    Verify fixture data is usable for intent.

    Verify if fixtures[endpoint] exists and is of expected data type.

    Verify if endpoint has code field in fixtures[endpoint_log] and verify its
    value is 200.

    If endpoint is present, of specified type and code not or code has value 200
    return TRUE, otherwise return False

    :param endpoint: endpoint in fixtures to verify
        for presence of _log companion code key with
        value 200 and matching type
    :param fixtures: dict keyed by endpoint name and
        endpoint data as value
    :param kind: expected data type of fixtures[endpoint]
    :return: True if endpoint is usable otherwise False
    """
    return fixtures.get(f"{endpoint}_log", {}).get("code", 200) == 200 and isinstance(
        fixtures.get(endpoint), kind
    )


def device_type_name(data: dict[Any, Any], key: str) -> str:
    """Get int key value from dict, map to name, default to UNKNOWN if missing."""
    return DEVICE_TYPES.get(
        (v if isinstance(v := data.get(key), int) else 0), "UNKNOWN"
    )
