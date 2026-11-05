# Envoy Options

When using default values for the {py:class}`pyenphase.Envoy` parameters, the available features and standard operating model is determined by the {py:meth}`pyenphase.Envoy.probe` method. For the majority of the Envoy configurations this will meet the needs.

For use with configurations which have special needs, maybe conflicting with automatic determination, or testing experimental features, the {py:attr}`~pyenphase.const.EnvoyOptions` are available that can be set during instantiation of {py:class}`pyenphase.Envoy`.

## V2_ACB_MODE

Envoy inverter data from [/api/v1/production/inverters](#endpoint_inverters) include inverter data and ACB data, if ACB is installed. These are identified by the `devType` field values of 1 and 11. Prior to v3.0 this was not recognized and the ACB data is reported as if they are inverters.

As of v3 the ACB data is not included with the inverter data. For backward compatibility and to continue to collect ACB data as inverter, the {py:attr}`~pyenphase.const.EnvoyOptions.V2_ACB_MODE` option can be set in `envoy_options` parameter of {py:class}`~pyenphase.envoy.Envoy`.

## NO_SOLAR

Originally the Envoy configurations were solar centric. It is assumed that all installations have inverters configured and this is part of the {py:meth}`pyenphase.Envoy.probe` logic. Recent reports however show Enphase battery installations in combination with different brand solar installations. The Envoy is installed for battery usage, but not for solar generation. This results in `NO_SOLAR` configurations that (may) lack the [/production](endpoint_json.md#productionjsondetails1) responses.

The reports show that the production endpoints don't respond at all and will time-out. The production updater will attempt each of the 3 endpoints 2 times, which leads to a very slow startup of the communication. When used with [Home Assistant](https://www.home-assistant.io/integrations/enphase_envoy/) this may even lead to integration load failures due to elapsed time exceeding the maximum startup time. The {py:attr}`~pyenphase.const.EnvoyOptions.NO_SOLAR` option can be set in the `envoy_options` parameter of {py:type}`~pyenphase.envoy.Envoy` to skip the production updater attempting to request the involved endpoints.

On this first release of the option, it has to be set by the caller. In a future version it may become an automatic enablement based on the presence of inverters in the probed data. Currently there is not enough data to warrant a flawless automatic mechanism.

Production data may report data from [/api/v1/production](endpoint_json.md#apiv1production). What these values represent in such a configuration is unclear. Consumption data is not reported. Use CT data if these are installed.

Do NOT enable this option if ACB batteries are installed, these report through /production as well.
