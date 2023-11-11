# Inverter data

Individual [inverter data](#pyenphase.models.inverter.EnvoyInverter), available for model as of firmware 3.9. are reported in `inverters: dict[str, EnvoyInverter]` attribute.

```python
for inverter in data.inverters:
    print (f'{inverter} sn: {data.inverters[inverter].serial_number}')
    print (f'{inverter} watts: {data.inverters[inverter].last_report_watts}')
    print (f'{inverter} max watts: {data.inverters[inverter].max_report_watts}')
    print (f'{inverter} last report: {data.inverters[inverter].last_report_date}')
```
