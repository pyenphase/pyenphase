# Enphase Ensemble

Enphase Ensemble [^1] provides information on installed battery storage and how it is used for optional EV charging or power provision.

[^1]: Older name, more recent name `Enphase Energy System`.

## Enphase Enpower data

The Enphase Enpower [^2] connects the home to grid power, the Encharge storage system, and solar PV. Information on it can be obtained from [EnvoyEnpower](#pyenphase.models.enpower.EnvoyEnpower).

[^2]: Older name, more recent name IQ System Controller.

The Envoy class provides [go_off_grid](#pyenphase.Envoy.go_off_grid) and [go_on_grid](#pyenphase.Envoy.go_on_grid) to control the grid connection.

```python
status = await envoy.go_off_grid()
if status["mains_admin_state"] != "open":
    raise RuntimeError("Failed to go off-grid")

status = await envoy.go_on_grid()
if status["mains_admin_state"] != "closed":
    raise RuntimeError("Failed to go on-grid")
```

[open_dry_contact](#pyenphase.Envoy.open_dry_contact) and [close_dry_contact](#pyenphase.Envoy.close_dry_contact) can be used to control dry contacts.

```python
status = await envoy.close_dry_contact(id)
print(envoy.data.dry_contact_status[id].status)

status = await envoy.open_dry_contact(id)
print(envoy.data.dry_contact_status[id].status)
```

Dry contact information is available in [EnvoyData.dry_contact_status](#pyenphase.EnvoyData.dry_contact_status) and [EnvoyData.dry_contact_settings](#pyenphase.EnvoyData.dry_contact_settings).

[Envoy.update_dry_contact](#pyenphase.Envoy.update_dry_contact) can be used to update settings. Use with care and only if fully aware of the impact.

```python
from typing import Any

new_setting: dict[str, Any] = {
        "id": id,
        "load_name": load_name,
}

status = await envoy.update_dry_contact(new_setting)
print(status)
```

## Enphase AC Battery (ACB) data

The ACB integration exposes both aggregate and per-device battery data:

- Aggregate ACB power and SOC are available in [EnvoyData.acb_power](#pyenphase.EnvoyData.acb_power), modeled by [EnvoyACBPower](#pyenphase.models.acb.EnvoyACBPower).
- Combined Encharge + ACB SOC/capacity is available in [EnvoyData.battery_aggregate](#pyenphase.EnvoyData.battery_aggregate), modeled by [EnvoyBatteryAggregate](#pyenphase.models.acb.EnvoyBatteryAggregate).
- Per-device ACB data is available in [EnvoyData.acb_inventory](#pyenphase.EnvoyData.acb_inventory), keyed by serial number and modeled by [EnvoyACB](#pyenphase.models.acb.EnvoyACB).
- The number of ACB batteries reported in production storage can be read from [Envoy.acb_count](#pyenphase.Envoy.acb_count).

Per-device ACB fields include state and sensor values such as `sleep_enabled`, `sleep_state`, `sleep_min_soc`, `sleep_max_soc`, `percent_full`, `charge_status`, `communicating`, `operating`, `producing`, `last_report_watts`, `max_report_watts`, and `last_report_date`.

```python
print(f"ACB count: {envoy.acb_count}")

if envoy.data.acb_inventory:
    for serial, acb in envoy.data.acb_inventory.items():
        print(serial, acb.sleep_state, acb.percent_full, acb.last_report_watts)
```

ACB sleep control is available with [Envoy.set_acb_sleep](#pyenphase.Envoy.set_acb_sleep) and [Envoy.clear_acb_sleep](#pyenphase.Envoy.clear_acb_sleep).

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

Both ACB control methods require ACB support on the gateway and validate input ranges before sending requests.

## Envoy Encharge data

The Enphase Encharge controls battery charge and discharge. Information on it can be obtained from [EnvoyEncharge](#pyenphase.models.encharge.EnvoyEncharge) for individual batteries, [EnvoyEnchargePower](#pyenphase.models.encharge.EnvoyEnchargePower), and [EnvoyEnchargeAggregate](#pyenphase.models.encharge.EnvoyEnchargeAggregate) for all batteries aggregated.

The Envoy class provides [Envoy.enable_charge_from_grid](#pyenphase.Envoy.enable_charge_from_grid), [Envoy.disable_charge_from_grid](#pyenphase.Envoy.disable_charge_from_grid), [Envoy.set_storage_mode](#pyenphase.Envoy.set_storage_mode), and [Envoy.set_reserve_soc](#pyenphase.Envoy.set_reserve_soc).

```python
status = await envoy.enable_charge_from_grid()
print(envoy.data.tariff.storage_settings.charge_from_grid)
print(status)

status = await envoy.disable_charge_from_grid()
print(envoy.data.tariff.storage_settings.charge_from_grid)
print(status)

status = await envoy.set_storage_mode(mode)
print(envoy.data.tariff.storage_settings.mode)
print(status)

status = await envoy.set_reserve_soc(value)
print(envoy.data.tariff.storage_settings.reserved_soc)
print(status)
```

## IQ Metered Collar data

The Enphase IQ Meter Collar is a meter socket adapter with an integrated microgrid interconnection device (MID) and current sensors for energy consumption metering. The CT sensors in the collar provide [net-consumption](./data_ctmeter.md#consumption-ct-options) data.

The MID status is available in [EnvoyCollar](#pyenphase.models.collar.EnvoyCollar).

## C6 Combiner data

The C6 Combiner status is available in [EnvoyC6CC](#pyenphase.models.c6combiner.EnvoyC6CC).
