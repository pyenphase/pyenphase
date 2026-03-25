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

The [inverter device data](endpoint_json.md#ivppdmdevice_data) includes a `deviceDataLimit` that appears to be fixed at 50. If more inverters are installed, only data for the first `deviceDataLimit` inverters is included, resulting in missing inverter data. When the reported `deviceCount` is greater than or equal to `deviceDataLimit`, data falls back to [/api/v1/production/inverters](endpoint_json.md#apiv1productioninverters) to avoid data loss; device detail data will then be unavailable for all inverters.

## Daily Outage at 11 PM

Each day, shortly after 11 PM local time, the Envoy performs some internal resets and cleanups. These cause the Envoy to become unresponsive. How long this outage lasts, varies by hardware type and/or firmware version.

Pyenphase uses retries when a request fails. Default retry setup is no more then 50 seconds elapsed, or 4 attempts. Each try uses the [specified timeout](#pyenphase.Envoy) or a 45 seconds default. With the default timeout of 45 seconds, this results in maximum 2 attempts, 1 retry. Or upto 4 attenmpts if the failure occurs quicker.

To overcome the 11 PM outage, a relaxed retry scheme is used between 11:00 PM and 11:20 PM. During that time interval, 360 seconds elapsed time and/or 10 retry attempts are allowed before a failure is returned.
