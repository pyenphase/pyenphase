"""Model for an envoy."""

from dataclasses import dataclass, field
from typing import Any

from .acb import EnvoyACBPower, EnvoyBatteryAggregate
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
    """
    Data Model for an envoy.

    Data is extract from raw data requested from Envoy. All raw
    data is also available as-received in :any:`raw`. For details
    on data models refer to the individual model descriptions.
    """

    #: dict of found Encharge device information, keyed by Encharge serial number.
    encharge_inventory: dict[str, EnvoyEncharge] | None = None
    #: dict of Enpower device power and charge state, keyed by Enpower serial number.
    encharge_power: dict[str, EnvoyEnchargePower] | None = None
    #: Aggregated data for all Encharge devices
    encharge_aggregate: EnvoyEnchargeAggregate | None = None
    #: EnchargePower device information
    enpower: EnvoyEnpower | None = None
    #: Power and soc for aggregated ACB batteries
    acb_power: EnvoyACBPower | None = None
    #: aggregated Enphase and ACB battery SOC and total capacity
    battery_aggregate: EnvoyBatteryAggregate | None = None
    #: Consumption power & energy values, only for Envoy metered with CT installed
    system_consumption: EnvoySystemConsumption | None = None
    #: Solar Production power & energy values
    system_production: EnvoySystemProduction | None = None
    #: Individual phase consumption power & energy values, keyed by :any:`PhaseNames`,
    #: only for Envoy metered with CT installed
    system_consumption_phases: dict[str, EnvoySystemConsumption | None] | None = None
    #: Individual phase solar production power & energy values, keyed by :any:`PhaseNames`,
    #: only for Envoy metered with CT installed
    system_production_phases: dict[str, EnvoySystemProduction | None] | None = None
    #: Net consumption power & energy values, a.k.a. grid import/export,
    #: only for Envoy metered with CT installed
    system_net_consumption: EnvoySystemConsumption | None = None
    #: Individual phase Net consumption power & energy values, keyed by :any:`PhaseNames`,
    #: only for Envoy metered with CT installed
    system_net_consumption_phases: dict[str, EnvoySystemConsumption | None] | None = (
        None
    )
    #: Production CT power & energy values , only for Envoy metered with production CT installed
    ctmeter_production: EnvoyMeterData | None = None  #: Production CT Meter data
    #: Consumption CT power & energy values , only for Envoy metered with consumption CT installed
    ctmeter_consumption: EnvoyMeterData | None = None  #: Consumption CT Meter data
    #: Storage CT power & energy values , only for Envoy metered with storage CT installed
    ctmeter_storage: EnvoyMeterData | None = None  #: Storage CT Meter data
    #: Individual phase production ct power & energy values, keyed by :any:`PhaseNames`,
    #: only for Envoy metered with production CT installed
    ctmeter_production_phases: dict[str, EnvoyMeterData] | None = None
    #: Individual phase consumption ct power & energy values, keyed by :any:`PhaseNames`,
    #: only for Envoy metered with consumption installed
    ctmeter_consumption_phases: dict[str, EnvoyMeterData] | None = None
    #: Individual phase storage ct power & energy values, keyed by :any:`PhaseNames`,
    #: only for Envoy metered with storage CT installed
    ctmeter_storage_phases: dict[str, EnvoyMeterData] | None = None
    #: dict of Dry contact relay status, keyed by relay ID
    dry_contact_status: dict[str, EnvoyDryContactStatus] = field(default_factory=dict)
    #: dict of Dry contact relay settings, keyed by relay ID
    dry_contact_settings: dict[str, EnvoyDryContactSettings] = field(
        default_factory=dict
    )
    #: dict of Solar inverter data, keyed by inverter serial-number
    inverters: dict[str, EnvoyInverter] = field(default_factory=dict)
    #: Tariff information from Envoy
    tariff: EnvoyTariff | None = None
    # Raw data is exposed so we can __eq__ the data to see if
    # anything has changed and consumers of the library can
    # avoid dispatching data if nothing has changed.
    #: All request responses received from Envoy in last :any:`Envoy.update`, keyed by endpoint
    raw: dict[str, Any] = field(default_factory=dict)
