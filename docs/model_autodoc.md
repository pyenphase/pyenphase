# Classes, methods and properties

```{eval-rst}
.. autoclass:: pyenphase.Envoy
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
  :class-doc-from: init
```

```{eval-rst}
.. autoclass:: pyenphase.auth.EnvoyAuth
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
  :class-doc-from: init
```

```{eval-rst}
.. autoclass:: pyenphase.auth.EnvoyTokenAuth
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
  :class-doc-from: init
```

```{eval-rst}
.. autoclass:: pyenphase.auth.EnvoyLegacyAuth
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
  :class-doc-from: init
```

```{eval-rst}
.. autoclass:: pyenphase.firmware.EnvoyFirmware
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
  :class-doc-from: init
```

```{eval-rst}
.. autoclass:: pyenphase.EnvoyData
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
```

```{eval-rst}
.. automodule:: pyenphase.const
  :members:
  :exclude-members: SupportedFeatures
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical

```

```{eval-rst}
.. automodule:: pyenphase.models.common
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
  :exclude-members: CommonProperties

```

```{include} updaters.md

```

## Supported Features

```{eval-rst}
.. autoclass:: pyenphase.const.SupportedFeatures
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
```

## Common Properties

```{eval-rst}
.. autoclass:: pyenphase.models.common.CommonProperties
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical

```

## Base class

```{eval-rst}
.. autoclass:: pyenphase.updaters.base.EnvoyUpdater
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
  :private-members:
  :class-doc-from: init
```

## production

```{eval-rst}
.. automodule:: pyenphase.updaters.production
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
```

```{eval-rst}
.. automodule:: pyenphase.updaters.api_v1_production
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
```

## Inverters

```{eval-rst}
.. automodule:: pyenphase.updaters.api_v1_production_inverters
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical

```

## EnvoyEnsemble

```{eval-rst}
.. automodule:: pyenphase.updaters.ensemble
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical

```

## EnvoyTariff

```{eval-rst}
.. automodule:: pyenphase.updaters.tariff
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical

```

## Current Transformers

```{eval-rst}
.. automodule:: pyenphase.updaters.meters
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical

```

# Models

## EnvoySystemProduction

```{eval-rst}
.. autoclass:: pyenphase.models.system_production.EnvoySystemProduction
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
```

## EnvoySystemConsumption

```{eval-rst}
.. autoclass:: pyenphase.models.system_consumption.EnvoySystemConsumption
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
```

## EnvoyInverter

```{eval-rst}
.. autoclass:: pyenphase.models.inverter.EnvoyInverter
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical

```

## EnvoyEncharge

```{eval-rst}
.. autoclass:: pyenphase.models.encharge.EnvoyEncharge
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
```

## EnvoyEnchargeAggregate

```{eval-rst}
.. autoclass:: pyenphase.models.encharge.EnvoyEnchargeAggregate
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
```

## EnvoyEnchargePower

```{eval-rst}
.. autoclass:: pyenphase.models.encharge.EnvoyEnchargePower
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
```

## EnvoyEnpower

```{eval-rst}
.. autoclass:: pyenphase.models.enpower.EnvoyEnpower
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
```

## EnvoyACBPower

```{eval-rst}
.. autoclass:: pyenphase.models.acb.EnvoyACBPower
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
```

## Envoy Aggregate Battery SOC

```{eval-rst}
.. autoclass:: pyenphase.models.acb.EnvoyBatteryAggregate
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
```

## Envoy Dry Contacts

```{eval-rst}
.. automodule:: pyenphase.models.dry_contacts
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
```

## EnvoyCollar

```{eval-rst}
.. automodule:: pyenphase.models.collar
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical

```

## EnvoyC6CC

```{eval-rst}
.. automodule:: pyenphase.models.c6combiner
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical

```

## CT Meters

```{eval-rst}
.. automodule:: pyenphase.models.meters
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
```

## Interface data

```{eval-rst}
.. autoclass:: pyenphase.models.home.EnvoyInterfaceInformation
  :members:
  :undoc-members:
  :show-inheritance:
  :member-order: alphabetical
```

# Utilities

## JSON

Helper functions for JSON.

```{eval-rst}
.. autofunction:: pyenphase.json.json_loads
```

## SSL

```{eval-rst}
.. automodule:: pyenphase.ssl
  :members: NO_VERIFY_SSL_CONTEXT, SSL_CONTEXT, create_no_verify_ssl_context, create_default_ssl_context
  :show-inheritance:

```

# Exceptions

```{eval-rst}
.. automodule:: pyenphase.exceptions
  :members:
  :show-inheritance:
  :member-order: alphabetical

```
