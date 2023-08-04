"""Model for an envoy."""

from dataclasses import dataclass, field
from typing import Any

from .dry_contacts import EnvoyDryContact
from .encharge import EnvoyEncharge
from .enpower import EnvoyEnpower
from .inverter import EnvoyInverter
from .system_production import EnvoySystemProduction


@dataclass(slots=True)
class EnvoyData:
    """Model for an envoy."""

    encharge: EnvoyEncharge | None
    enpower: EnvoyEnpower | None
    system_production: EnvoySystemProduction | None
    dry_contacts: dict[str, EnvoyDryContact] = field(default_factory=dict)
    inverters: dict[str, EnvoyInverter] = field(default_factory=dict)
    raw: dict[str, dict[str, Any]] = field(default_factory=dict)
