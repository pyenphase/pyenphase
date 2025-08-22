# Phase data

For a metered Envoy with installed and configured current transformers (CT meters) in `three`‑phase mode and more than one active phase, data for individual phases is reported for solar production in {py:attr}`pyenphase.EnvoyData.system_production_phases` and house consumption in {py:attr}`pyenphase.EnvoyData.system_consumption_phases`.

Upon completion of the [probe](usage_intro.md#data-collection) call, the phase setup is available. The {py:attr}`~pyenphase.Envoy.phase_count`, {py:attr}`~pyenphase.Envoy.ct_meter_count`, {py:attr}`~pyenphase.Envoy.phase_mode`, and {py:attr}`~pyenphase.Envoy.consumption_meter_type` are available from the Envoy model.

Phase names are enumerated as `L1`, `L2`, and `L3` by {py:class}`pyenphase.const.PhaseNames`. Phase modes are enumerated as `single`, `split`, and `three` by {py:class}`pyenphase.models.meters.EnvoyPhaseMode`. CT meter types are enumerated as `production`, `storage`, `net-consumption`, and `total-consumption` by {py:class}`pyenphase.models.meters.CtType`.

Be aware that `phase_count` and `phase_mode` apply for all configured CTs. The metered Envoy can, however, be configured with only 1, 2, or all 3 CT types. In this case, the unused CT data in `system_production_phases`, `system_consumption_phases`, or `ctmeter_storage_phases` will be `None`.

The Envoy property {py:attr}`pyenphase.Envoy.active_phase_count` returns how many phases are present in the production/consumption reports. This is 0 for `single` configurations.

```python

from pyenphase import Envoy

envoy = Envoy(host_ip_or_name)
await envoy.setup()
print(f'Envoy {envoy.host} running {envoy.firmware}, sn: {envoy.serial_number}')

await envoy.authenticate(username=username, password=password, token=token)

await envoy.probe()

print(f'Number of configured Phases: {envoy.phase_count}')
print(f'Number of configured CT meters: {envoy.ct_meter_count}')
print(f'Phases are configured in: {envoy.phase_mode} mode')
print(f'Phases reported in production/consumption: {envoy.active_phase_count}')

```
