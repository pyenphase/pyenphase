# System_Production data

This is the aggregated solar production data, as reported by the Envoy, class {py:class}`~pyenphase.models.system_production.EnvoySystemProduction`.

```python
    data: EnvoyData = await envoy.update()

    print(f'Watts: {data.system_production.watts_now}')
    print(f'TodaysEnergy: {data.system_production.watt_hours_today}')
    print(f'LifetimeEnergy {data.system_production.watt_hours_lifetime}')
    print(f'Last7DaysEnergy {data.system_production.watt_hours_last_7_days}')
```

## System_Production_Phases

For [metered Envoy with multi-phase installations](./phase_data.md#phase-data), production phase data is available in Envoy class {py:class}`~pyenphase.EnvoyData.system_production_phases` keyed by {py:class}`~pyenphase.const.PhaseNames`.

```python
from pyenphase.const import PhaseNames, PHASENAMES

data: EnvoyData = await envoy.update()

# if more then 1 phase reported then get phase data
if envoy.actual_phase_count > 1 and data.system_production_phases:
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

## Data sources

The data is provided by one of the [updaters](updaters.md) below, ordered in their probe sequence.

This data set is identified by the {py:class}`pyenphase.const.SupportedFeatures` flag {py:attr}`~pyenphase.const.SupportedFeatures.PRODUCTION`. First updater probe that returns the feature flag will be used.

### {py:class}`~pyenphase.updaters.production.EnvoyProductionJsonUpdater`

This is the default updater for production data. It provides data for aggregated phases and individual phases. Data is measured/calculated by the Envoy.

|                                                                                             |                                                                         |     |
| ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | --- |
| endpoint                                                                                    | [`/production.json?details=1`](endpoint_json.md#productionjsondetails1) |     |
| json path aggregated                                                                        | `production[?(@.type=='eim' && @.activeCount > 0)]`                     |     |
| json path phases                                                                            | `production[?(@.type=='eim' && @.activeCount > 0)].lines[*]`            |     |
|                                                                                             |                                                                         |     |
| class data                                                                                  | json node                                                               | uom |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watt_hours_lifetime`    | whLifetime                                                              | Wh  |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watt_hours_last_7_days` | whLastSevenDays                                                         | Wh  |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watt_hours_today`       | whToday                                                                 | Wh  |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watts_now`              | wNow                                                                    | W   |

### {py:class}`~pyenphase.updaters.production.EnvoyProductionUpdater`

This is an alternative updater for production data if the standard updater data is not available. It only provides data for aggregated phases. Data is measured/calculated by the Envoy.

|                                                                                             |                                                     |     |
| ------------------------------------------------------------------------------------------- | --------------------------------------------------- | --- |
| endpoint                                                                                    | [`/production`](endpoint_json.md#production)        |     |
| json path                                                                                   | `production[?(@.type=='eim' && @.activeCount > 0)]` |     |
| class data                                                                                  | json node                                           | uom |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watt_hours_lifetime`    | whLifetime                                          | Wh  |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watt_hours_last_7_days` | whLastSevenDays                                     | Wh  |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watt_hours_today`       | whToday                                             | Wh  |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watts_now`              | wNow                                                | W   |

### {py:class}`~pyenphase.updaters.api_v1_production.EnvoyApiV1ProductionUpdater`

This is an alternative updater for production data for non-metered Envoy or Envoy metered without installed CT. Previous updaters don't return data for this type. It only provides data for aggregated phases. Data is measured/calculated by the Envoy.

|                                                                                             |                                                            |     |
| ------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | --- |
| endpoint                                                                                    | [`/api/v1/production`](./endpoint_json.md#apiv1production) |     |
| json path                                                                                   | `$`                                                        |     |
| class data                                                                                  | json node                                                  | uom |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watt_hours_lifetime`    | wattHoursLifetime                                          | Wh  |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watt_hours_last_7_days` | wattHoursSevenDays                                         | Wh  |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watt_hours_today`       | wattHoursToday                                             | Wh  |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watts_now`              | wattsNow                                                   | W   |

For Envoy metered without CT installed, and firmware 8.2.8.2.4264 or newer, there is stalled values in V1 Production Endpoint. When /info is_meter is set, fallback to inverters section in production endpoint using next updater.

### {py:class}`~pyenphase.updaters.production.EnvoyProductionJsonFallbackUpdater`

This is an alternative updater for production data for non-metered Envoy or Envoy metered without CT installed. The {py:class}`~pyenphase.updaters.api_v1_production.EnvoyApiV1ProductionUpdater` updater does not return data for some firmware versions. In that case, this updater falls back to the `inverters` section in the production report. It only provides data for aggregated phases. Data is measured/calculated by the Envoy.
| | | |
| ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | --- |
| endpoint | `/production.json?details=1` or `/production` | |
| json path | `production[?(@.type=='inverters' && @.activeCount > 0)]` | |
| class data | json node | uom |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watt_hours_lifetime` | whLifetime | Wh |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watt_hours_last_7_days` | not in report,<br>use unreliable whLastSevenDays from type=='eim' | |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watt_hours_today` | not in report,<br>use unreliable whToday from type=='eim' | |
| {py:attr}`~pyenphase.models.system_production.EnvoySystemProduction.watts_now` | wNow | W |
