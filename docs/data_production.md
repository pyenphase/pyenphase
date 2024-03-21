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

For metered Envoy with installed and configured CT meter `three` phase mode and more then 1 phase active, data for individual phases is also reported, see [Phase Data](./phase_data.md#phase-data).
