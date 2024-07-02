"""JSON utilities for pyenphase."""

import logging
from typing import Any

import orjson

_LOGGER = logging.getLogger(__name__)


def json_loads(end_point: str, json_source: bytes | str) -> Any:
    try:
        return orjson.loads(json_source)
    except orjson.JSONDecodeError as e:
        _LOGGER.debug(
            "Unable to decode response from Envoy endpoint %s: %s", end_point, e
        )
        raise
