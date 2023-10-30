# System_Consumption data

This is the energy consumption by the house reported by the Envoy, class [EnvoySystemConsumption](#pyenphase.models.system_consumption.EnvoySystemConsumption). It is only available for metered Envoy with installed and configured consumption CT Meter.

```python
    data: EnvoyData = await envoy.update()

    if data.system_consumption:
        print(f'Watts: {data.system_consumption.watts_now}')
        print(f'TodaysEnergy: {data.system_consumption.watt_hours_today}')
        print(f'LifetimeEnergy {data.system_consumption.watt_hours_lifetime}')
        print(f'Last7DaysEnergy {data.system_consumption.watt_hours_last_7_days}')
```

## Consumption Phase data

Only available for metered Envoy with installed and configured CT meter in `three` phase mode and more then 1 phase active. It is reported for solar [production](#pyenphase.models.system_production.EnvoySystemProduction) and house [consumption](#pyenphase.models.system_consumption.EnvoySystemConsumption) if these are enabled. Data is in [system_consumption_phases: dict[str,EnvoySystemConsumption]](#system_consumption-data). Phases are named `L1`, `L2`, and `L3`.

```python
    data: EnvoyData = await envoy.update()

    if Envoy.phase_count > 1:
        for phase in data.system_consumption_phases:
            print(f'{phase} Watts: {data.system_consumption_phases[phase].watts_now}')
            print(f'{phase} TodaysEnergy: {data.system_consumption_phases[phase].watt_hours_today}')
            print(f'{phase} LifetimeEnergy {system_consumption_phases.[phase].watt_hours_lifetime}')
            print(f'{phase} Last7DaysEnergy {system_consumption_phases.[phase].watt_hours_last_7_days}')
```
