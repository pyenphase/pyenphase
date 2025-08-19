# System_Consumption data

This is the aggregated energy consumption by the house, as reported by the Envoy, class {py:class}`~pyenphase.models.system_consumption.EnvoySystemConsumption`. This is often referred to as total consumption. It is only available for metered Envoy with an installed and configured consumption CT Meter, either for net or total consumption.

```python
    data: EnvoyData = await envoy.update()

    if data.system_consumption:
        print(f'Watts: {data.system_consumption.watts_now}')
        print(f'TodaysEnergy: {data.system_consumption.watt_hours_today}')
        print(f'LifetimeEnergy {data.system_consumption.watt_hours_lifetime}')
        print(f'Last7DaysEnergy {data.system_consumption.watt_hours_last_7_days}')
```

## System_Consumption_Phases

For [metered Envoy with multi-phase installations](./phase_data.md#phase-data), consumption phase data is available in Envoy class {py:class}`~pyenphase.EnvoyData.system_consumption_phases` keyed by {py:class}`~pyenphase.const.PhaseNames`.

```python
    from pyenphase.const import PhaseNames, PHASENAMES

    data: EnvoyData = await envoy.update()

    if Envoy.phase_count > 1:
        for phase in data.system_consumption_phases and data.system_consumption_phases:
            print(f'{phase} Watts: {data.system_consumption_phases[phase].watts_now}')
            print(f'{phase} TodaysEnergy: {data.system_consumption_phases[phase].watt_hours_today}')
            print(f'{phase} LifetimeEnergy {system_consumption_phases.[phase].watt_hours_lifetime}')
            print(f'{phase} Last7DaysEnergy {system_consumption_phases.[phase].watt_hours_last_7_days}')

        # report specific phase data  by using PhaseNames (for phase 1)
        print(
            f'Value watt_hours_lifetime : {data.system_consumption_phases[PhaseNames.PHASE_1].watt_hours_lifetime}'
        )
        # report specific phase data by using phase index 0-2 (for phase 1)
        print(
            f'Value watt_hours_lifetime : {data.system_consumption_phases[PHASENAMES[0]].watt_hours_lifetime}'
        )

```
