# Enphase Ensemble

Enphase ensemble [^1] provides information on installed battery storage and how it is used for optional EV charging or power provision.

[^1]: Older name, more recent name `Enphase Energy System`.

## Enphase Enpower data

The Enphase Enpower [^2] connects the home to grid power, the Encharge storage system, and solar PV. Information on it can be obtained from the {py:attr}`~pyenphase.models.enpower.EnvoyEnpower`.

[^2]: Older Name, more recent name IQ System Controller

The Envoy class provides the methods {py:meth}`~pyenphase.Envoy.go_off_grid` and {py:meth}`~pyenphase.Envoy.go_on_grid` to control the grid connection.

```python
        status = await envoy.go_off_grid()
        if status["mains_admin_state"] != "open":
            #error going off grid



        status = await envoy.go_on_grid()
        if status["mains_admin_state"] != "closed":
            #error going on grid

```

{py:meth}`~pyenphase.Envoy.open_dry_contact` and {py:meth}`~pyenphase.Envoy.close_dry_contact` allows to to control the dry contacts.

```python
status = await envoy.close_dry_contact(id)
print(f"{envoy.data.dry_contact_status[id].status}")


status = await envoy.open_dry_contact(id)
print(f"{envoy.data.dry_contact_status[id].status}")
```

Dry Contact information is available in the {py:attr}`~pyenphase.EnvoyData.dry_contact_status` and {py:attr}`~pyenphase.EnvoyData.dry_contact_settings`.

{py:meth}`~pyenphase.Envoy.update_dry_contact` can be used to update settings, use with care and only if fully aware of impact!

```python
new_setting: dict[str, Any] = {}
new_setting["id"] = id
new_setting["load_name"] = load_name

status = await envoy.update_dry_contact(new_setting)
print(status)
```

## Generator data

Systems with an Enpower and a standby generator installed report generator data. Availability is signaled by the {py:attr}`~pyenphase.const.SupportedFeatures.GENERATOR` and {py:attr}`~pyenphase.const.SupportedFeatures.GENERATOR_SCHEDULE` supported feature flags.

- Generator status (admin, operational relay state, admin mode, schedule state, generator present) is available in {py:attr}`~pyenphase.EnvoyData.generator`, modeled by {py:attr}`~pyenphase.models.generator.EnvoyGenerator`.
- Generator configuration (name plate rating, manufacturer, model, start method, warm-up/cool-down minutes) is available in {py:attr}`~pyenphase.EnvoyData.generator_config`, modeled by {py:attr}`~pyenphase.models.generator.EnvoyGeneratorConfig`.
- The generator exercise schedule and default state-of-charge settings are available in {py:attr}`~pyenphase.EnvoyData.generator_schedule`, modeled by {py:attr}`~pyenphase.models.generator.EnvoyGeneratorSchedule`. The schedule is only available if the {py:attr}`~pyenphase.const.SupportedFeatures.GENERATOR_SCHEDULE` flag is set. If the flag is set, generator_schedule may return None when issues exist with the schedule data.
- The generator operation mode ("off", "on" or "auto") is available in {py:attr}`~pyenphase.EnvoyData.generator_mode`, modeled by {py:attr}`~pyenphase.models.generator.EnvoyGeneratorMode`, on firmware exposing the `/ivp/ss/gen_mode` endpoint.

The Envoy class provides the method {py:meth}`~pyenphase.Envoy.set_generator_mode` to control the generator operation mode, {py:meth}`~pyenphase.Envoy.update_generator_schedule` to change the exercise schedule and default state-of-charge settings, and {py:meth}`~pyenphase.Envoy.set_generator_charge_from_generator` to allow or disallow charging batteries from the generator.

```{note}
The generator schedule will only be available when configured in the Envoy using the Enphase tools. If not setup, the {py:attr}`~pyenphase.const.SupportedFeatures.GENERATOR_SCHEDULE` flag will not be set and the {py:attr}`~pyenphase.EnvoyData.generator_schedule` will be `None`. The {py:meth}`~pyenphase.Envoy.update_generator_schedule` can not be used either until a schedule is configured in the Envoy.

Once a schedule is configured in the Envoy, rerun {py:attr}`pyenphase.Envoy.probe` and {py:attr}`pyenphase.Envoy.update` to make the schedule known in the data model. If your application does not specifically use {py:meth}`pyenphase.Envoy.probe` but rather the automatic execution of it by first use of {py:meth}`pyenphase.Envoy.update`, you will need to re-instantiate the Envoy class, which in its simplest form is re-starting your application.
```

{py:meth}`~pyenphase.Envoy.update_generator_schedule` and {py:meth}`~pyenphase.Envoy.set_generator_charge_from_generator` send the whole document to the Envoy, as these endpoints do not support partial updates. The document is built from the data in {py:attr}`~pyenphase.EnvoyData`, with only the specified settings changed. ({py:meth}`~pyenphase.Envoy.set_generator_mode` is a single command endpoint and does not work this way.) {py:meth}`~pyenphase.Envoy.update_generator_schedule` takes a dict of settings to change, so a single setting can be changed without specifying the others:

```python
await envoy.update_generator_schedule({"exercise_day": "Sat", "exercise_start": 945})
```

Both return the reply from the Envoy, which is the resulting document. The stored data is updated from it as well, so either can be used to verify what was applied. If the Envoy does not return a complete document, the stored data is left at the last known state instead of an optimistic one and {py:exc}`EnvoyCommunicationError` is raised; the update was sent in that case, so use {py:meth}`~pyenphase.Envoy.update` to establish the actual state.

Both also accept `refresh`, which re-reads the document from the Envoy right before the changes are merged into it:

```python
await envoy.update_generator_schedule({"exercise_day": "Sat"}, refresh=True)
```

Use it when the Enphase cloud or app may have changed settings since the last data collection, so values from stale data are not sent back.

Be aware that when the Envoy returns an incomplete document as a refresh reply, the stored data for the generator_schedule is set to None to reflect the now current state in the Envoy and raises {py:exc}`EnvoyFeatureNotAvailable`.

On systems with Enphase batteries, note that `default_start_soc` and `default_stop_soc` are always part of the schedule document and are applied by the firmware as the active generator start/stop state of charge, as reported in {py:attr}`~pyenphase.EnvoyData.generator`. Values held in {py:attr}`~pyenphase.EnvoyData.generator_schedule` at the time of the call are sent, so if another application changed them since the last data collection, the update will set them back. Use `refresh=True`, call {py:meth}`~pyenphase.Envoy.update` first, or include the wanted SOC values in the settings to change. The generator starts at `default_start_soc` and stops at `default_stop_soc`, so the start value must be lower than the stop value; the resulting pair is validated against the stored values for whichever of the two is not being changed.

On systems without Enphase batteries the Envoy accepts a `charge_from_generator` write with HTTP 200 but normalizes the value back to `true`; do not assume `false` persisted. The returned document and the updated {py:attr}`~pyenphase.EnvoyData.generator_config` report the effective value.

```python
if envoy.data.generator:
    print(f"Generator relay: {envoy.data.generator.oper_state}")

if envoy.data.generator_mode:
    print(f"Generator mode: {envoy.data.generator_mode.gen_cmd}")

    # switch the generator to auto (start on grid loss)
    await envoy.set_generator_mode("auto")

if envoy.data.generator_config:
    print(
        f"Generator: {envoy.data.generator_config.manufacturer} {envoy.data.generator_config.model}"
    )

if schedule := envoy.data.generator_schedule:
    print(
        f"Exercise: every {schedule.exercise_freq_in_weeks} week(s) on "
        f"{schedule.exercise_day} at minute {schedule.exercise_start} "
        f"for {schedule.exercise_duration} minutes"
    )
```

## Enphase AC Battery (ACB) data

Both ACB aggregate and per-device battery data are exposed:

- Aggregate ACB power and SOC are available in {py:attr}`~pyenphase.EnvoyData.acb_power`, modeled by {py:attr}`~pyenphase.models.acb.EnvoyACBPower`.
- Combined Encharge + ACB SOC/capacity is available in {py:attr}`~pyenphase.EnvoyData.battery_aggregate`, modeled by {py:attr}`~pyenphase.models.acb.EnvoyBatteryAggregate`.
- Per-device ACB data is available in {py:attr}`~pyenphase.EnvoyData.acb_inventory`, keyed by serial number and modeled by {py:attr}`~pyenphase.models.acb.EnvoyACB`.
- The number of ACB batteries reported in production storage can be read from {py:attr}`~pyenphase.Envoy.acb_count`.

Per-device ACB fields include state and sensor values such as `sleep_enabled`, `sleep_state`, `sleep_min_soc`, `sleep_max_soc`, `percent_full`, `charge_status`, `communicating`, `operating`, `producing`, `last_report_watts`, `max_report_watts`, and `last_report_date`.

```python
print(f"ACB count: {envoy.acb_count}")

if envoy.data.acb_inventory:
    for serial, acb in envoy.data.acb_inventory.items():
        print(serial, acb.sleep_state, acb.percent_full, acb.last_report_watts)
```

ACB sleep control is available with {py:meth}`~pyenphase.Envoy.set_acb_sleep` and {py:meth}`~pyenphase.Envoy.clear_acb_sleep`.

When using `sleep_min_soc` and `sleep_max_soc`, the battery will charge or discharge to reach the configured target boundary before entering sleep mode. For example, if current SOC is above `sleep_max_soc`, it will discharge down to that level, and if SOC is below `sleep_min_soc`, it will charge up to that level.

ACB per-device telemetry from `/inventory` is relatively slow-moving on some systems (observed around 10-15 minutes). This is generally fine for metadata and control-state tracking, but fields like `sleep_enabled`, `percent_full`, and `charge_status` may lag by one reporting interval.

```python
await envoy.set_acb_sleep(
    [
        {
            "serial_num": "122000000001",
            "sleep_min_soc": 10,
            "sleep_max_soc": 20,
        }
    ]
)

await envoy.clear_acb_sleep(["122000000001"])
```

Both ACB control methods require ACB support on the gateway and validate inputs before sending requests.

## Envoy Encharge data

The Enphase Encharge controls battery charge and discharge. Information on it can be obtained from {py:attr}`~pyenphase.models.encharge.EnvoyEncharge` for individual batteries, {py:attr}`~pyenphase.models.encharge.EnvoyEnchargePower` and {py:attr}`~pyenphase.models.encharge.EnvoyEnchargeAggregate` for all batteries aggregated.

The Envoy class provides the methods {py:meth}`~pyenphase.Envoy.enable_charge_from_grid`, {py:meth}`~pyenphase.Envoy.disable_charge_from_grid`, {py:meth}`~pyenphase.Envoy.set_storage_mode` and {py:meth}`~pyenphase.Envoy.set_reserve_soc`.

```python

        status = await envoy.enable_charge_from_grid(id)
        print(f"{envoy.data.tariff.storage_settings.charge_from_grid}")
        print (status)


        status = await envoy.disable_charge_from_grid(id)
        print(f"{envoy.data.tariff.storage_settings.charge_from_grid}")
        print (status)


        status = await envoy.set_storage_mode(mode: EnvoyStorageMode)
        print(f"{envoy.data.tariff.data.tariff.storage_settings.mode}")
        print (status)

```

On firmware where optimized schedules are supported, passing `disable_optimized_schedules=True` to `set_storage_mode` will also set `opt_schedules` to `False`. When `opt_schedules` is `True`, writes to `storage_settings.mode` are accepted by the gateway and return HTTP 200, but are silently ignored by the battery controller.

Note that the Enlighten cloud service may overwrite a locally-set mode within one to two minutes by pushing its own tariff configuration to the gateway. See [Known Issues](./known_issues.md#enlighten-cloud-overwriting-locally-set-battery-mode) for details.

```python
        status = await envoy.set_reserve_soc(value: int)
        print(f"{envoy.data.tariff.storage_settings.reserved_soc}")
        print (status)

```

## IQ Metered Collar data

The Enphase IQ Meter Collar is a meter socket adapter with an integrated microgrid interconnection device (MID) and current
sensors for energy consumption metering. The CT sensors in the collar provide the [net-consumption](./data_ctmeter.md#consumption-ct-options) data.

The MID status is available in the {py:attr}`~pyenphase.models.collar.EnvoyCollar` data object.

## C6 Combiner data

The C6 Combiner status is available in the {py:attr}`~pyenphase.models.c6combiner.EnvoyC6CC` data object.
