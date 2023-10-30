# System_Production data

This is the solar production data reported by the Envoy, class [EnvoySystemProduction](#pyenphase.models.system_production.EnvoySystemProduction).

```python
    data: EnvoyData = await envoy.update()

    print(f'Watts: {data.system_production.watts_now}')
    print(f'TodaysEnergy: {data.system_production.watt_hours_today}')
    print(f'LifetimeEnergy {data.system_production.watt_hours_lifetime}')
    print(f'Last7DaysEnergy {data.system_production.watt_hours_last_7_days}')
```

The source of the data differs by Envoy type and firmware level. For metered Envoy types with configured current transformer (CT) production meter data comes from the /production endpoint with CT meter data. For non-metered Envoy types data comes from the `/api/v1/production` endpoint as calculated by the Envoy from inverter data.

## Production Phase data

Only available for metered Envoy with installed and configured CT meter in `three` phase mode and more then 1 phase active. It is reported for solar [production](#pyenphase.models.system_production.EnvoySystemProduction) and house [consumption](#pyenphase.models.system_consumption.EnvoySystemConsumption) if these are enabled. Data is in [system_production_phases: dict[str,EnvoySystemProduction]](#system_production-data). Phases are named `L1`, `L2`, and `L3`.

```python
    data: EnvoyData = await envoy.update()

    if Envoy.phase_count > 1:
        for phase in data.system_production_phases:
            print(f'{phase} Watts: {data.system_production_phases[phase].watts_now}')
            print(f'{phase} TodaysEnergy: {data.system_production_phases[phase].watt_hours_today}')
            print(f'{phase} LifetimeEnergy {data.system_production_phases[phase].watt_hours_lifetime}')
            print(f'{phase} Last7DaysEnergy {data.system_production_phases[phase].watt_hours_last_7_days}')
```
