"""Pyenphase helpers."""

import logging

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
        raise EnvoyClientClosedError("Client closed before request is issued")
