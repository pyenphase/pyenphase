"""Model for an envoy."""

from dataclasses import dataclass, field
from typing import Any

from .dry_contacts import EnvoyDryContactSettings, EnvoyDryContactStatus
from .encharge import EnvoyEncharge, EnvoyEnchargeAggregate, EnvoyEnchargePower
from .enpower import EnvoyEnpower
from .inverter import EnvoyInverter
from .meters import EnvoyMeterData
from .system_consumption import EnvoySystemConsumption
from .system_production import EnvoySystemProduction
from .tariff import EnvoyTariff


@dataclass(slots=True)
class EnvoyData:
    """Model for an envoy."""

    encharge_inventory: dict[str, EnvoyEncharge] | None = None
    encharge_power: dict[str, EnvoyEnchargePower] | None = None
    encharge_aggregate: EnvoyEnchargeAggregate | None = None
    enpower: EnvoyEnpower | None = None
    system_consumption: EnvoySystemConsumption | None = None
    system_production: EnvoySystemProduction | None = None
    system_consumption_phases: dict[str, EnvoySystemConsumption | None] | None = (
        None  #: Individual phase consumption data, only for Envoy metered with CT installed
    )
    system_production_phases: dict[str, EnvoySystemProduction | None] | None = (
        None  #: Individual phase production data, only for Envoy metered with CT installed
    )
    ctmeter_production: EnvoyMeterData | None = None  #: Production CT Meter data
    ctmeter_consumption: EnvoyMeterData | None = None  #: Consumption CT Meter data
    ctmeter_storage: EnvoyMeterData | None = None  #: Storage CT Meter data
    ctmeter_production_phases: dict[str, EnvoyMeterData] | None = (
        None  #: Production CT Meter Individual phase data
    )
    ctmeter_consumption_phases: dict[str, EnvoyMeterData] | None = (
        None  #: Consumption CT Meter Individual phase data
    )
    ctmeter_storage_phases: dict[str, EnvoyMeterData] | None = (
        None  #: Storage CT Meter Individual phase data
    )
    dry_contact_status: dict[str, EnvoyDryContactStatus] = field(default_factory=dict)
    dry_contact_settings: dict[str, EnvoyDryContactSettings] = field(
        default_factory=dict
    )
    inverters: dict[str, EnvoyInverter] = field(default_factory=dict)
    tariff: EnvoyTariff | None = None
    # Raw data is exposed so we can __eq__ the data to see if
    # anything has changed and consumers of the library can
    # avoid dispatching data if nothing has changed.
    raw: dict[str, Any] = field(default_factory=dict)
