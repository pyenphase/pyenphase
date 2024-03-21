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

For metered Envoy with installed and configured CT meter in `three` phase mode and more then 1 phase active, data for individual phases is also reported, see [Phase Data](./phase_data.md#phase-data)
