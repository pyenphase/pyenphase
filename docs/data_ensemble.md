# Enphase Ensemble

Enphase ensemble [^1] provides information on installed battery storage and how it is used for optional EV charging or power provision.

[^1]: Older name, more recent name `Enphase Energy System`.

## Enphase Enpower data

The Enphase Enpower [^2] connects the home to grid power, the Encharge storage system, and solar PV. Information on it can be obtained from the [EnvoyEnpower](#pyenphase.models.enpower.EnvoyEnpower).

[^2]: Older Name, more recent name IQ System Controller

The Envoy class provides the methods [Go_Off_Grid](#pyenphase.Envoy.go_off_grid) and [Go_On_Grid](#pyenphase.Envoy.go_on_grid) to control the grid connection.

```python
        status = await envoy.go_off_grid()
        if status["mains_admin_state"] != "open":
            #error clogoing off grid



        status = await envoy.go_off_grid()
        if status["mains_admin_state"] != "closed":
            #error clogoing off grid

```

[Open_dry_contact](#pyenphase.Envoy.open_dry_contact) and [close_dry_contact](#pyenphase.Envoy.close_dry_contact) allows to to control the dry contacts.

```python

        status = await envoy.close_dry_contact(id)
        print(f"{envoy.data.dry_contact_status[id].status}")


        status = await envoy.open_dry_contact(id)
        print(f"{envoy.data.dry_contact_status[id].status}")

```

Dry Contact information is available in the [EnvoyData.dry_contact_status](#pyenphase.EnvoyData.dry_contact_status) and [Envoy.dry_contact_settings](#pyenphase.EnvoyData.dry_contact_settings).

[Envoy.update_dry_contact](#pyenphase.Envoy.update_dry_contact) can be used to update settings, use with care and only if fully aware of impact!

```python

        new_setting: dict[str, Any] = {}
        new_setting['id'] = id
        new_setting['load_name'] = load_name

        status = await envoy.update_dry_contact(new_setting)
        print (status)


```

## Envoy Encharge data

The Enphase Encharge controls battery charge and discharge. Information on it can be obtained from [EnvoyEncharge](#pyenphase.models.encharge.EnvoyEncharge) for individual batteries, [EnvoyEnchargePower](#pyenphase.models.encharge.EnvoyEnchargePower) and [EnvoyEnchargeAggregate](#pyenphase.models.encharge.EnvoyEnchargeAggregate) for all batteries aggregated.

The Envoy class provides the methods [Envoy.enable_charge_from_grid](#pyenphase.Envoy.enable_charge_from_grid), [Envoy.disable_charge_from_grid](#pyenphase.Envoy.disable_charge_from_grid), [Envoy.set_storage_mode](#pyenphase.Envoy.set_storage_mode) and [set_reserve_soc](#pyenphase.Envoy.set_reserve_soc).

```python

        status = await envoy.enable_charge_from_grid(id)
        print(f"{envoy.data.tariff.storage_settings.charge_from_grid}")
        print (status)


        status = await envoy.disable_charge_from_grid(id)
        print(f"{envoy.data.dry_contact_status[id].status}")
        print (status)


        status = await envoy.set_storage_mode(mode: EnvoyStorageMode)
        print(f"{envoy.data.tariff.data.tariff.storage_settings.mode}")
        print (status)

        status = await envoy.set_reserve_soc(value: int)
        print(f"{envoy.data.tariff.storage_settings.reserved_soc}")
        print (status)

```

## IQ Metered Collar data

The Enphase IQ Meter Collar is a meter socket adapter with an integrated microgrid interconnection device (MID) and current
sensors for energy consumption metering. The CT sensors in the collar provide the [net-consumption](./data_ctmeter.md#consumption-ct-options) data.

The MID status is available in the [EnvoyCollar](#pyenphase.models.collar.EnvoyCollar) data object.

## C6 Combiner data

The C6 Combiner status is available in the [EnvoyC6CC](#pyenphase.models.c6combiner.EnvoyC6CC) data object.
