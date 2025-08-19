# Known Issues

Issues have been reported with data, these vary by firmware versions. Newer firmware may solve these or introduce new issues.

## Production & Consumption data

| data                | envoy <br> type [^1] | issue                                    | in firmware |
| ------------------- | -------------------- | ---------------------------------------- | ----------- |
| whToday             | Mtr                  | late reset some time after midnight      |
|                     |                      | reset to non-zero value                  |
|                     |                      | sudden value step changes                |
| whLastSevenDays     | Mtr                  | sudden value step changes                |
| watt_hours_lifetime | NoCT                 | reset to zero when reaching 1.19 mW      | \<8.x       |
|                     | Std                  | 1.19 MWh value stepdown                  |             |
| all                 | NoCT                 | stalled values in V1 Production Endpoint | >= 8.2.4264 |

[^1]: Std: Envoy standard, not metered. Mtr: Envoy metered. NoCT: Envoy metered without installed and configured C.T

## Inverter device data

The [inverter device data](./endpoint_json.md#ivppdmdevice_data) includes a `deviceDataLimit` which seems to be set to a fixed 50. If more inverters are installed, then only data for the first `deviceDataLimit` inverters is included. This results in missed inverter data. If reported `deviceCount` equals `deviceDataLimit` inverter data will fall back to [`/api/v1/production/inverters`](endpoint_json.md#apiv1productioninverters) to avoid data loss for some inverters. Result is that no device detail data is available for all inverters.
