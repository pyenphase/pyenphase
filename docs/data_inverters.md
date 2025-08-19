# Inverter data

Individual inverter data, available for all Envoy models as of firmware 3.9., class {py:class}`~pyenphase.models.inverter.EnvoyInverter`.

```python
for inverter in data.inverters:
    print (f'{inverter} sn: {data.inverters[inverter].serial_number}')
    print (f'{inverter} watts: {data.inverters[inverter].last_report_watts}')
    print (f'{inverter} max watts: {data.inverters[inverter].max_report_watts}')
    print (f'{inverter} last report: {data.inverters[inverter].last_report_date}')
    print (f'{inverter} panel output: {data.inverters[inverter].dc_voltage}V @ {data.inverters[inverter].dc_current}A')
    print (f'{inverter} output: {data.inverters[inverter].ac_voltage}V @ {data.inverters[inverter].ac_current}A {data.inverters[inverter].ac_frequency}Hz')
    print (f'{inverter} temperature: {data.inverters[inverter].temperature}°C')
    print (f'{inverter} energy produced: {data.inverters[inverter].energy_produced} mWh')
    print (f'{inverter} energy produced today: {data.inverters[inverter].energy_today} Wh')
    print (f'{inverter} lifetime energy produced: {data.inverters[inverter].lifetime_energy} Wh')
```

```{note}
If the `/ivp/pdm/device_data` endpoint is not supported by the Envoy firmware, the attribute values `dc_voltage`, `dc_current`, `ac_voltage`, `ac_current`, `ac_frequency`, `temperature`, `energy_produced`, `energy_today`, `lifetime_energy` from the inverter details will be `None`.
```

## Data sources

The data is provided by one of the [updaters](updaters.md) below, ordered in their probe sequence.

The base data set is identified by the {py:class}`pyenphase.const.SupportedFeatures` flag {py:attr}`~pyenphase.const.SupportedFeatures.INVERTERS` and {py:attr}`~pyenphase.const.SupportedFeatures.DETAILED_INVERTERS` for inverter details. First updater probe that returns the {py:attr}`~pyenphase.const.SupportedFeatures.INVERTERS` feature flag will be used.

### {py:class}`~pyenphase.updaters.device_data_inverters.EnvoyDeviceDataInvertersUpdater`

This is the default updater for inverter data. It provides data for individual inverter production data as well as inverter device details. Data is measured/calculated by the Envoy.

|                                                                                                |                                                              |     |
| ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | --- |
| endpoint                                                                                       | [`/ivp/pdm/device_data`](endpoint_json.md#ivppdmdevice_data) |     |
| json path                                                                                      | [?(@.devName=='pcu')]                                        |     |
|                                                                                                |                                                              |     |
| data                                                                                           | json node                                                    | uom |
| {py:attr}`serial_number <pyenphase.models.inverter.EnvoyInverter.serial_number>`               | serial_number                                                |     |
| {py:attr}`last_report_date <pyenphase.models.inverter.EnvoyInverter.last_report_date>`         | last_report_date                                             |     |
| {py:attr}`last_report_watts <pyenphase.models.inverter.EnvoyInverter.last_report_watts>`       | last_report_watts                                            | W   |
| {py:attr}`max_report_watts <pyenphase.models.inverter.EnvoyInverter.max_report_watts>`         | max_report_watts                                             | W   |
| {py:attr}`dc_voltage <pyenphase.models.inverter.EnvoyInverter.dc_voltage>`                     | dc_voltage                                                   | V   |
| {py:attr}`dc_current <pyenphase.models.inverter.EnvoyInverter.dc_current>`                     | dc_current                                                   | A   |
| {py:attr}`ac_voltage <pyenphase.models.inverter.EnvoyInverter.ac_voltage>`                     | ac_voltage                                                   | V   |
| {py:attr}`ac_frequency <pyenphase.models.inverter.EnvoyInverter.ac_frequency>`                 | ac_frequency                                                 | Hz  |
| {py:attr}`temperature <pyenphase.models.inverter.EnvoyInverter.temperature>`                   | temperature                                                  | C   |
| {py:attr}`lifetime_energy <pyenphase.models.inverter.EnvoyInverter.lifetime_energy>`           | lifetime_energy                                              | Wh  |
| {py:attr}`energy_produced <pyenphase.models.inverter.EnvoyInverter.energy_produced>`           | energy_produced                                              | Wh  |
| {py:attr}`energy_today <pyenphase.models.inverter.EnvoyInverter.energy_today>`                 | energy_today                                                 | Wh  |
| {py:attr}`last_report_duration <pyenphase.models.inverter.EnvoyInverter.last_report_duration>` | last_report_duration                                         | s   |

### {py:class}`~pyenphase.updaters.api_v1_production_inverters.EnvoyApiV1ProductionInvertersUpdater`

This is the updater for base inverter data. It only provides data for individual inverter production data. Data is measured/calculated by the Envoy.

|                                                                                                |                                                                             |     |
| ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | --- |
| endpoint                                                                                       | [`/api/v1/production/inverters`](endpoint_json.md#apiv1productioninverters) |     |
| json path                                                                                      | $                                                                           |     |
|                                                                                                |                                                                             |     |
| data                                                                                           | json node                                                                   | uom |
| {py:attr}`serial_number <pyenphase.models.inverter.EnvoyInverter.serial_number>`               | serial_number                                                               |     |
| {py:attr}`last_report_date <pyenphase.models.inverter.EnvoyInverter.last_report_date>`         | last_report_date                                                            |     |
| {py:attr}`last_report_watts <pyenphase.models.inverter.EnvoyInverter.last_report_watts>`       | last_report_watts                                                           | W   |
| {py:attr}`max_report_watts <pyenphase.models.inverter.EnvoyInverter.max_report_watts>`         | max_report_watts                                                            | W   |
| {py:attr}`dc_voltage <pyenphase.models.inverter.EnvoyInverter.dc_voltage>`                     | not available                                                               |     |
| {py:attr}`dc_current <pyenphase.models.inverter.EnvoyInverter.dc_current>`                     | not available                                                               |     |
| {py:attr}`ac_voltage <pyenphase.models.inverter.EnvoyInverter.ac_voltage>`                     | not available                                                               |     |
| {py:attr}`ac_frequency <pyenphase.models.inverter.EnvoyInverter.ac_frequency>`                 | not available                                                               |     |
| {py:attr}`temperature <pyenphase.models.inverter.EnvoyInverter.temperature>`                   | not available                                                               |     |
| {py:attr}`lifetime_energy <pyenphase.models.inverter.EnvoyInverter.lifetime_energy>`           | not available                                                               |     |
| {py:attr}`energy_produced <pyenphase.models.inverter.EnvoyInverter.energy_produced>`           | not available                                                               |     |
| {py:attr}`energy_today <pyenphase.models.inverter.EnvoyInverter.energy_today>`                 | not available                                                               |     |
| {py:attr}`last_report_duration <pyenphase.models.inverter.EnvoyInverter.last_report_duration>` | not available                                                               |     |
