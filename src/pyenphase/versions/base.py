"""Model for an envoy."""

from dataclasses import dataclass, field
from typing import Any

from ..models.dry_contacts import EnvoyDryContact
from ..models.encharge import EnvoyEncharge
from ..models.enpower import EnvoyEnpower
from ..models.inverter import EnvoyInverter
from ..models.system_production import EnvoySystemProduction


@dataclass(slots=True)
class EnvoyBaseData:
    firmware: str
    serial: str
    encharge: EnvoyEncharge | None
    enpower: EnvoyEnpower | None
    system_production: EnvoySystemProduction | None
    dry_contacts: dict[str, EnvoyDryContact] = field(default_factory=dict)
    inverters: dict[str, EnvoyInverter] = field(default_factory=dict)
    raw: dict[str, dict[str, Any]] = field(default_factory=dict)
