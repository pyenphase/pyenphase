# Deprecations

## Future deprecations

### V2_acb_mode

As of pyenphase v3, acb data is not included in inverter data when the {py:obj}`~pyenphase.envoy.Envoy``.v2_acb_mode` parameter is set to False and {py:attr}`~pyenphase.const.EnvoyOptions.V2_ACB_MODE` is not set. For backward compatibility the `v2_acb_mode` parameter defaults to True, so acb battery data remains included in inverter data by default.

In a future version the v2_acb_mode parameter will be deprecated and the default setting of True will change to False. To be in control of this setting, start using {py:attr}`~pyenphase.const.EnvoyOptions.V2_ACB_MODE` with `envoy_options` to select v2 ACB mode and replace current use of `v2_acb_mode` by the use of {py:type}`~pyenphase.envoy.Envoy``.envoy_options` parameter.

## Deprecated

### Python 3.10

Support for Python 3.10 is dropped as of V6.0

### ctmeter_production, ctmeter_consumption and ctmeter_storage records

In v5.0 has:

- ctmeter_production: EnvoyMeterData | None = None
- ctmeter_consumption: EnvoyMeterData | None = None
- ctmeter_storage: EnvoyMeterData | None = None
- ctmeter_production_phases: dict[str, EnvoyMeterData | None] | None = None
- ctmeter_consumption_phases: dict[str, EnvoyMeterData | None] | None = None
- ctmeter_storage_phases: dict[str, EnvoyMeterData | None] | None = None

Removed.

These were marked for deprecation in v2.4.0 and replaced by:

- {py:attr}`pyenphase.EnvoyData.ctmeters`
- {py:attr}`pyenphase.EnvoyData.ctmeters_phases`
