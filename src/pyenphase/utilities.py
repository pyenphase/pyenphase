"""Pyenphase helpers."""

import logging
from collections.abc import Generator
from contextlib import contextmanager

import aiohttp

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
