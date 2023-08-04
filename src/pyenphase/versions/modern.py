"""Model for an envoy."""

from dataclasses import dataclass

from .base import EnvoyBaseData


@dataclass(slots=True)
class EnvoyModernData(EnvoyBaseData):
    """Model for a envoy with firmware version >= 7.0.0."""
