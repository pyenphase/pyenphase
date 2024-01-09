# Raw data

All data for all endpoints is stored as received in the `raw: dict[str, Any]` attribute, keyed by the endpoint path.[^1] Raw can be used for quick check if anything changed between data collections.

```json
{
    "/api/v1/production": {
        "wattHoursToday": 2900,
        "wattHoursSevenDays": 15195,
        "wattHoursLifetime": 8485676,
        "wattsNow": 887
    },
    "/api/v1/production/inverters": [{
        "serialNumber": "122212345678",
        "lastReportDate": 1703592785,
        "devType": 1, "lastReportWatts": 31,
        "maxReportWatts": 98
    }, {
        "serialNumber": "122212345679",
        "lastReportDate": 1703592815,
        "devType": 1,
        "lastReportWatts": 39,
        "maxReportWatts": 172
    }
}

```

[^1]: Example only showing 2 endpoints. Production data is provided in [EnvoySystemProduction](#EnvoySystemProduction) class, Inverter data in [EnvoyInverter](#EnvoyInverter) class.

```python
previous_data: EnvoyData
new_data: EnvoyData = envoy.update()
if new_data != previous_data:
    production_data = new_data.raw["/api/v1/production"]

    previous_data = new_data
```
