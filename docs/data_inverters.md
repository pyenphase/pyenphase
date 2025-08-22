# Inverter data

Individual inverter data, available for all Envoy models as of firmware 3.9, class {py:class}`~pyenphase.models.inverter.EnvoyInverter`.

```python

for sn, inv in data.inverters.items():
    print(f'{sn} sn: {inv.serial_number}')
    print(f'{sn} watts: {inv.last_report_watts}')
    print(f'{sn} max watts: {inv.max_report_watts}')
    print(f'{sn} last report: {inv.last_report_date}')
    print(f'{sn} panel output: {inv.dc_voltage}V @ {inv.dc_current}A')
    print(f'{sn} output: {inv.ac_voltage}V @ {inv.ac_current}A {inv.ac_frequency}Hz')
    print(f'{sn} temperature: {inv.temperature}°C')
    print(f'{sn} energy produced: {inv.energy_produced} Wh')
    print(f'{sn} energy produced today: {inv.energy_today} Wh')
    print(f'{sn} lifetime energy produced: {inv.lifetime_energy} Wh')
```

```{note}
If the `/ivp/pdm/device_data` endpoint is not supported by the Envoy firmware, the attribute values `dc_voltage`, `dc_current`, `ac_voltage`, `ac_current`, `ac_frequency`, `temperature`, `energy_produced`, `energy_today`, `lifetime_energy` from the inverter details will be `None`.
```

## Data sources

The data is provided by one of the [updaters](updaters.md) below, ordered in their probe sequence.

The base data set is identified by the {py:class}`pyenphase.const.SupportedFeatures` flag {py:attr}`~pyenphase.const.SupportedFeatures.INVERTERS` and {py:attr}`~pyenphase.const.SupportedFeatures.DETAILED_INVERTERS` for inverter details. First updater probe that returns the {py:attr}`~pyenphase.const.SupportedFeatures.INVERTERS` feature flag will be used.

### {py:class}`~pyenphase.updaters.device_data_inverters.EnvoyDeviceDataInvertersUpdater`

This is the default updater for inverter data. It provides data for individual inverter production data as well as inverter device details. Data is measured/calculated by the Envoy.

|                                                                          |                                                              |     |
| ------------------------------------------------------------------------ | ------------------------------------------------------------ | --- |
| endpoint                                                                 | [`/ivp/pdm/device_data`](endpoint_json.md#ivppdmdevice_data) |     |
| json path                                                                | `[?(@.devName=='pcu')]`                                      |     |
|                                                                          |                                                              |     |
| data                                                                     | json node                                                    | uom |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.serial_number`        | `sn`                                                         |     |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.last_report_date`     | `channels[0].lastReading.endDate`                            |     |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.last_report_watts`    | `channels[0].watts.now`                                      | W   |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.max_report_watts`     | `channels[0].watts.max`                                      | W   |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.dc_voltage`           | `channels[0].lastReading.dcVoltageINmV`                      | V   |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.dc_current`           | `channels[0].lastReading.dcCurrentINmA`                      | A   |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.ac_voltage`           | `channels[0].lastReading.acVoltageINmV`                      | V   |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.ac_current`           | `channels[0].lastReading.acCurrentInmA`                      | A   |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.ac_frequency`         | `channels[0].lastReading.acFrequencyINmHz`                   | Hz  |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.temperature`          | `channels[0].lastReading.channelTemp`                        | °C  |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.lifetime_energy`      | `channels[0].lifetime.joulesProduced/3600`                   | Wh  |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.energy_produced`      | `channels[0].lastReading.joulesProduced/duration/3.6`        | Wh  |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.energy_today`         | `channels[0].wattHours.today`                                | Wh  |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.last_report_duration` | `channels[0].lastReading.duration`                           | s   |

```{note}
Raw fields for dc/ac voltage/current/frequency are provided in milli‑units (mV, mA, mHz) by the endpoint and are converted to V/A/Hz by the model.
```

### {py:class}`~pyenphase.updaters.api_v1_production_inverters.EnvoyApiV1ProductionInvertersUpdater`

This is the updater for base inverter data. It only provides data for individual inverter production data. Data is measured/calculated by the Envoy.

|           |                                                                             |     |
| --------- | --------------------------------------------------------------------------- | --- |
| endpoint  | [`/api/v1/production/inverters`](endpoint_json.md#apiv1productioninverters) |     |
| json path | $                                                                           |     |
|           |                                                                             |     |
| data      | json node                                                                   | uom |

| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.serial_number` | `serialNumber` | |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.last_report_date` | `lastReportDate` | |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.last_report_watts` | `lastReportWatts` | W |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.max_report_watts` | `maxReportWatts` | W |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.dc_voltage` | not available | |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.dc_current` | not available | |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.ac_voltage` | not available | |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.ac_current` | not available | |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.ac_frequency` | not available | |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.temperature` | not available | |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.lifetime_energy` | not available | |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.energy_produced` | not available | |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.energy_today` | not available | |
| {py:attr}`~pyenphase.models.inverter.EnvoyInverter.last_report_duration` | not available | |
