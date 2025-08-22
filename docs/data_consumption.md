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

For [metered Envoy with multi-phase installations](./phase_data.md#phase-data), consumption phase data is available in Envoy attribute {py:attr}`~pyenphase.EnvoyData.system_consumption_phases` keyed by {py:class}`~pyenphase.const.PhaseNames`.

```python
    from pyenphase.const import PhaseNames, PHASENAMES

    data: EnvoyData = await envoy.update()

    if envoy.phase_count > 1 and data.system_consumption_phases:
        for phase in data.system_consumption_phases:
            print(f'{phase} Watts: {data.system_consumption_phases[phase].watts_now}')
            print(f'{phase} TodaysEnergy: {data.system_consumption_phases[phase].watt_hours_today}')
            print(f'{phase} LifetimeEnergy {data.system_consumption_phases[phase].watt_hours_lifetime}')
            print(f'{phase} Last7DaysEnergy {data.system_consumption_phases[phase].watt_hours_last_7_days}')

        # report specific phase data  by using PhaseNames (for phase 1)
        print(f'Value watt_hours_lifetime : {data.system_consumption_phases[PhaseNames.PHASE_1].watt_hours_lifetime}')

        # report specific phase data by using phase index 0-2 (for phase 1)
        print(f'Value watt_hours_lifetime : {data.system_consumption_phases[PHASENAMES[0]].watt_hours_lifetime}')
```

## Data sources

The data is provided by one of the [updaters](updaters.md) below, ordered in their probe sequence.

This data set is identified by the {py:class}`pyenphase.const.SupportedFeatures` flags {py:attr}`~pyenphase.const.SupportedFeatures.TOTAL_CONSUMPTION` or {py:attr}`~pyenphase.const.SupportedFeatures.NET_CONSUMPTION`, based on which consumption CT is installed. The first updater probe that returns either of the two feature flags will be used.

### {py:class}`~pyenphase.updaters.production.EnvoyProductionJsonUpdater`

This is the default updater for consumption data. It provides data for aggregated phases and individual phases. Data is measured/calculated by the Envoy.

|                                                                                               |                                                                                                                                                           |     |
| --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | --- |
| endpoint                                                                                      | [`/production.json?details=1`](endpoint_json.md#productionjsondetails1)                                                                                   |     |
| json path aggregated                                                                          | `consumption[?(@.type=='eim' && @.activeCount > 0 && (@.measurementType == 'total-consumption' \|\| @.measurementType == 'net-consumption')))]`           |     |
| json path phases                                                                              | `consumption[?(@.type=='eim' && @.activeCount > 0 && ((@.measurementType == 'total-consumption' \|\| @.measurementType == 'net-consumption'))].lines[\*]` |     |
|                                                                                               |                                                                                                                                                           |     |
| data                                                                                          | json node                                                                                                                                                 | uom |
| {py:attr}`~pyenphase.models.system_consumption.EnvoySystemConsumption.watt_hours_lifetime`    | whLifetime                                                                                                                                                | Wh  |
| {py:attr}`~pyenphase.models.system_consumption.EnvoySystemConsumption.watt_hours_last_7_days` | whLastSevenDays                                                                                                                                           | Wh  |
| {py:attr}`~pyenphase.models.system_consumption.EnvoySystemConsumption.watt_hours_today`       | whToday                                                                                                                                                   | Wh  |
| {py:attr}`~pyenphase.models.system_consumption.EnvoySystemConsumption.watts_now`              | wNow                                                                                                                                                      | W   |

### {py:class}`~pyenphase.updaters.production.EnvoyProductionUpdater`

This is an alternative updater for consumption data if the standard updater data is not available. It only provides data for aggregated phases. Data is measured/calculated by the Envoy.

|                                                                                               |                                                                                                                                                 |     |
| --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | --- |
| endpoint                                                                                      | [`/production`](endpoint_json.md#production)                                                                                                    |     |
| json path                                                                                     | `consumption[?(@.type=='eim' && @.activeCount > 0 && (@.measurementType == 'total-consumption' \|\|  @.measurementType == 'net-consumption'))]` |     |
| data                                                                                          | json node                                                                                                                                       | uom |
| {py:attr}`~pyenphase.models.system_consumption.EnvoySystemConsumption.watt_hours_lifetime`    | whLifetime                                                                                                                                      | Wh  |
| {py:attr}`~pyenphase.models.system_consumption.EnvoySystemConsumption.watt_hours_last_7_days` | whLastSevenDays                                                                                                                                 | Wh  |
| {py:attr}`~pyenphase.models.system_consumption.EnvoySystemConsumption.watt_hours_today`       | whToday                                                                                                                                         | Wh  |
| {py:attr}`~pyenphase.models.system_consumption.EnvoySystemConsumption.watts_now`              | wNow                                                                                                                                            | W   |
