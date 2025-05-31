# Inverter data

Individual [inverter data](#pyenphase.models.inverter.EnvoyInverter), available for model as of firmware 3.9. are reported in `inverters: dict[str, EnvoyInverter]` attribute.

```python
for inverter in data.inverters:
    print (f'{inverter} sn: {data.inverters[inverter].serial_number}')
    print (f'{inverter} watts: {data.inverters[inverter].last_report_watts}')
    print (f'{inverter} max watts: {data.inverters[inverter].max_report_watts}')
    print (f'{inverter} last report: {data.inverters[inverter].last_report_date}')
```

If the `/ivp/pdm/device_data` endpoint is supported, then extra data is available per inverter

::: note
  The fields (`dc_voltage`, `dc_current`, `ac_voltage`, `ac_current`, `ac_frequency`, `temperature`) will be `None` if the endpoint is not supported.
:::

```python
for inverter in data.inverters:
    print (f'{inverter} panel output: {data.inverters[inverter].dc_voltage}V @ {data.inverters[inverter].dc_current}A')
    print (f'{inverter} output: {data.inverters[inverter].ac_voltage}V @ {data.inverters[inverter].ac_current}A {data.inverters[inverter].ac_frequency}Hz')
    print (f'{inverter} temperature: {data.inverters[inverter].temperature}°C')
```
