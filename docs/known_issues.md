# Known Issues

Issues have been reported with data; these vary by firmware version. Newer firmware may resolve these or introduce new issues.

## Production & Consumption data

| data                | envoy <br> type [^1] | issue                                    | in firmware |
| ------------------- | -------------------- | ---------------------------------------- | ----------- |
| whToday             | Mtr                  | late reset some time after midnight      |             |
|                     |                      | reset to non-zero value                  |             |
|                     |                      | sudden value step changes                |             |
| whLastSevenDays     | Mtr                  | sudden value step changes                |             |
| watt_hours_lifetime | NoCT                 | reset to zero when reaching 1.19 MWh     | \<8.x       |
|                     | Std                  | 1.19 MWh value stepdown                  |             |
| all                 | NoCT                 | stalled values in V1 Production Endpoint | >= 8.2.4264 |

[^1]: Std: Envoy standard (not metered). Mtr: Envoy metered. NoCT: Envoy metered without installed and configured CTs.

## Inverter device data

The [inverter device data](./endpoint_json.md#ivp-pdm-device_data) includes a `deviceDataLimit` that appears to be fixed at 50. If more inverters are installed, only data for the first `deviceDataLimit` inverters is included, resulting in missing inverter data. When the reported `deviceCount` is greater than or equal to `deviceDataLimit`, data falls back to [/api/v1/production/inverters](./endpoint_json.md#api-v1-production-inverters) to avoid data loss; device detail data will then be unavailable for all inverters.
