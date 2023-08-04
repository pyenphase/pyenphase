"""Model for an envoy."""

from dataclasses import dataclass

from .base import EnvoyBaseData


@dataclass(slots=True)
class EnvoyLegacyData(EnvoyBaseData):
    """Model for a legacy envoy."""
