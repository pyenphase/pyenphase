"""Model for an envoy."""

from dataclasses import dataclass, field
from typing import Any

from .acb import EnvoyACBPower, EnvoyBatteryAggregate
from .c6combiner import EnvoyC6CC
from .collar import EnvoyCollar
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
    #: IQ Meter collar, only for Envoy with IQ Meter Collar integrated consumption metering installed
    collar: EnvoyCollar | None = None
    #: Envoy C6 Combiner controller
    c6cc: EnvoyC6CC | None = None
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
    #: CT power & energy values, only for Envoy metered with CT installed.
    #: Keyed by :any:`CtType`
    ctmeters: dict[str, EnvoyMeterData] = field(default_factory=dict)
    #: CT power & energy phase values, only for Envoy metered with CT installed.
    #: Keyed by :any:`CtType` and  :any:`PhaseNames`
    ctmeters_phases: dict[str, dict[str, EnvoyMeterData]] = field(default_factory=dict)
    # these are still here for backward compatibility
    #: Production CT power & energy values, only for Envoy metered with production CT installed
    #:
    #: May be deprecated in a future version, use :any:`ctmeters` [:any:`CtType.PRODUCTION`] instead
    #:
    ctmeter_production: EnvoyMeterData | None = None
    #: Consumption CT power & energy values, only for Envoy metered with consumption CT installed
    #:
    #: May be deprecated in a future version, use :any:`ctmeters` [:any:`CtType.TOTAL_CONSUMPTION`] or :any:`ctmeters` [:any:`CtType.NET_CONSUMPTION`] instead
    #:
    ctmeter_consumption: EnvoyMeterData | None = None
    #: Storage CT power & energy values, only for Envoy metered with storage CT installed
    #:
    #: May be deprecated in a future version, use :any:`ctmeters` [:any:`CtType.STORAGE`] instead
    #:
    ctmeter_storage: EnvoyMeterData | None = None
    #: Individual phase production CT power & energy values, keyed by :any:`PhaseNames`,
    #: only for Envoy metered with production CT installed
    #:
    #: May be deprecated in a future version, use :any:`ctmeters_phases` [:any:`CtType.PRODUCTION`] instead
    #:
    ctmeter_production_phases: dict[str, EnvoyMeterData] | None = None
    #: Individual phase consumption CT power & energy values, keyed by :any:`PhaseNames`,
    #: only for Envoy metered with consumption installed
    #:
    #: May be deprecated in a future version, use :any:`ctmeters_phases` [:any:`CtType.TOTAL_CONSUMPTION`] or :any:`ctmeters_phases` [:any:`CtType.NET_CONSUMPTION`] instead
    #:
    ctmeter_consumption_phases: dict[str, EnvoyMeterData] | None = None
    #: Individual phase storage CT power & energy values, keyed by :any:`PhaseNames`,
    #: only for Envoy metered with storage CT installed
    #:
    #: May be deprecated in a future version, use :any:`ctmeters_phases` [:any:`CtType.STORAGE`] instead
    #:
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
