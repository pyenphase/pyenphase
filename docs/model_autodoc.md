# Classes, methods and properties

<!---
```{eval-rst}
.. automodule:: pyenphase
  :members:
```

```{eval-rst}
.. automodule:: pyenphase.updaters.base
  :members:

```

```{eval-rst}
.. automodule:: pyenphase.firmware
  :members:

```

## Const
```{eval-rst}
.. automodule:: pyenphase.const
  :members:

```

## Exceptions
```{eval-rst}
.. automodule:: pyenphase.exceptions
  :members:

```
-->

```{eval-rst}
.. autoclass:: pyenphase.Envoy
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
  :class-doc-from: init
```

```{eval-rst}
.. autoclass:: pyenphase.auth.EnvoyAuth
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
  :class-doc-from: init
```

```{eval-rst}
.. autoclass:: pyenphase.auth.EnvoyTokenAuth
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
  :class-doc-from: init
```

```{eval-rst}
.. autoclass:: pyenphase.auth.EnvoyLegacyAuth
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
  :class-doc-from: init
```

```{eval-rst}
.. autoclass:: pyenphase.firmware.EnvoyFirmware
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

```{eval-rst}
.. autoclass:: pyenphase.EnvoyData
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

```{eval-rst}
.. automodule:: pyenphase.const
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

```{eval-rst}
.. automodule:: pyenphase.models.common
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource

```

# Updaters

## Base class

```{eval-rst}
.. automodule:: pyenphase.updaters.base
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

## production

```{eval-rst}
.. automodule:: pyenphase.updaters.production
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

```{eval-rst}
.. automodule:: pyenphase.updaters.api_v1_production
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

## Inverters

```{eval-rst}
.. automodule:: pyenphase.updaters.api_v1_production_inverters
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource

```

## EnvoyEnsemble

```{eval-rst}
.. automodule:: pyenphase.updaters.ensemble
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource

```

## EnvoyTariff

```{eval-rst}
.. automodule:: pyenphase.updaters.tariff
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource

```

## Current Transformers

```{eval-rst}
.. automodule:: pyenphase.updaters.meters
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource

```

# Models

## EnvoySystemProduction

```{eval-rst}
.. autoclass:: pyenphase.models.system_production.EnvoySystemProduction
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

## EnvoySystemConsumption

```{eval-rst}
.. autoclass:: pyenphase.models.system_consumption.EnvoySystemConsumption
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

## EnvoyInverter

```{eval-rst}
.. autoclass:: pyenphase.models.inverter.EnvoyInverter
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource

```

## EnvoyEncharge

```{eval-rst}
.. autoclass:: pyenphase.models.encharge.EnvoyEncharge
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

## EnvoyEnchargeAggregate

```{eval-rst}
.. autoclass:: pyenphase.models.encharge.EnvoyEnchargeAggregate
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

## EnvoyEnchargePower

```{eval-rst}
.. autoclass:: pyenphase.models.encharge.EnvoyEnchargePower
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

## EnvoyEnpower

```{eval-rst}
.. autoclass:: pyenphase.models.enpower.EnvoyEnpower
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

## ACBPower

```{eval-rst}
.. autoclass:: pyenphase.models.acb.EnvoyACBPower
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

## Envoy Aggregate Battery SOC

```{eval-rst}
.. autoclass:: pyenphase.models.acb.EnvoyBatteryAggregate
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

## EnvoyDryContactSettings

```{eval-rst}
.. automodule:: pyenphase.models.dry_contacts
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

## CT Meters

```{eval-rst}
.. automodule:: pyenphase.models.meters
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

# Utilities

## Json

```{eval-rst}
.. autoclass:: pyenphase.json.json_loads
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: bysource
```

## SSL

```{eval-rst}
.. automodule:: pyenphase.ssl
  :members:
  :show-inheritance:
  :member-order: bysource
```

# Exceptions

```{eval-rst}
.. automodule:: pyenphase.exceptions
  :members:
  :show-inheritance:
  :member-order: bysource

```

<!---




```{eval-rst}
.. autoclass:: pyenphase.const.PhaseNames
  :members:

```

```{eval-rst}
.. autoclass:: pyenphase.models.inverter.EnvoyInverter
  :members:

```

```{eval-rst}
.. autoclass:: pyenphase.models.encharge.EnvoyEncharge
  :members:

```

```{eval-rst}
.. autoclass:: pyenphase.models.encharge.EnvoyEnchargeAggregate
  :members:

```

```{eval-rst}
.. autoclass:: pyenphase.models.encharge.EnvoyEnchargePower
  :members:

```

```{eval-rst}
.. autoclass:: pyenphase.models.enpower.EnvoyEnpower
  :members:

```

```{eval-rst}
.. autoclass:: pyenphase.models.dry_contacts.EnvoyDryContactSettings
  :members:

```

```{eval-rst}
.. autoclass:: pyenphase.models.dry_contacts.EnvoyDryContactStatus
  :members:

```

```{eval-rst}
.. autoclass:: pyenphase.updaters.tariff.EnvoyTariff
  :members:

```

-->
