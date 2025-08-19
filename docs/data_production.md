# System_Production data

This is the aggregated solar production data, as reported by the Envoy, class {py:class}`~pyenphase.models.system_production.EnvoySystemProduction`.

```python
    data: EnvoyData = await envoy.update()

    print(f'Watts: {data.system_production.watts_now}')
    print(f'TodaysEnergy: {data.system_production.watt_hours_today}')
    print(f'LifetimeEnergy {data.system_production.watt_hours_lifetime}')
    print(f'Last7DaysEnergy {data.system_production.watt_hours_last_7_days}')
```

The source of the data differs by Envoy type and firmware level. For metered Envoy types with configured current transformer (CT) production meter data comes from the /production endpoint with CT meter data. For non-metered Envoy types data comes from the `/api/v1/production` endpoint as calculated by the Envoy from inverter data.

## System_Production_Phases

For [metered Envoy with multi-phase installations](./phase_data.md#phase-data), production phase data is available in Envoy class {py:class}`~pyenphase.EnvoyData.system_production_phases` keyed by {py:class}`~pyenphase.const.PhaseNames`.

```python
from pyenphase.const import PhaseNames, PHASENAMES

data: EnvoyData = await envoy.update()

# if more then 1 phase reported then get phase data
if Envoy.actual_phase_count > 1 and data.system_production_phases:
    # Get data by looping over phase data
    for phase in data.system_production_phases:
        print(f'{phase} Watts: {data.system_production_phases[phase].watts_now}')
        print(f'{phase} TodaysEnergy: {data.system_production_phases[phase].watt_hours_today}')
        print(f'{phase} LifetimeEnergy {data.system_production_phases[phase].watt_hours_lifetime}')
        print(f'{phase} Last7DaysEnergy {data.system_production_phases[phase].watt_hours_last_7_days}')

    # report specific phase data by using PhaseNames (for phase 1)
    print(
        f'watt_hours_lifetime : {data.system_production_phases[PhaseNames.PHASE_1].watt_hours_lifetime}'
    )
    # report specific phase data by using phase index 0-2 (for phase 1)
    print(
        f'watt_hours_lifetime : {data.system_production_phases[PHASENAMES[0]].watt_hours_lifetime}'
    )

```
