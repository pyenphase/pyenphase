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

Each day, shortly after 11 PM local Envoy time, the Envoy performs some internal resets and cleanups. These cause the Envoy to become unresponsive. How long this outage lasts, varies by hardware type and/or firmware version.

Pyenphase uses retries when a request fails. Default retry setup is no more than 240 seconds elapsed, or 6 attempts. Each try uses the timeout specified in {py:class}`pyenphase.Envoy` or a 45 seconds default. With the default timeout of 45 seconds, this results in maximum 6 attempts, 5 retries. Or up to 6 attempts if the failure occurs quicker.

If this 11 PM outage still results in errors, use the {py:meth}`pyenphase.Envoy.set_retry_policy` method to set a more relaxed retry scheme.

## Enlighten cloud overwriting locally-set battery mode

The Enlighten cloud service maintains a persistent outbound connection to the IQ Gateway and periodically pushes tariff configuration to it. When a local API write via {py:meth}`pyenphase.Envoy.set_storage_mode` sets a mode that differs from the cloud-held configuration, the cloud will typically overwrite it within one to two minutes. The overwrite is identifiable in the tariff response: the `date` field is updated to a timestamp that was not written by the local PUT request, `opt_schedules` is restored to `true`, and the mode reverts to `self-consumption`. Enphase have confirmed this behaviour is intentional.

Blocking the IQ Gateway's outbound internet access at the network level prevents the cloud push and causes locally-set modes to persist. Note that this also prevents the Enlighten platform from receiving monitoring data from the gateway.
