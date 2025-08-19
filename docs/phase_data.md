# Phase data

For metered Envoy with installed and configured current transformers (CT meters) in `three` phase mode and more then 1 phase active, data for individual phases is reported for solar [production](#pyenphase.EnvoyData.system_production_phases) and house [consumption](#pyenphase.EnvoyData.system_consumption_phases). Configurations in `split` mode do not report multiple phases in their production and consumption data.

Upon completion of the [probe](usage_intro.md#data-collection) call, the phase setup is available. The [number of configured phases](#pyenphase.Envoy.phase_count), the [number of configured CT meters](#pyenphase.Envoy.ct_meter_count), the [phase mode configured](#pyenphase.Envoy.phase_mode) and [type of consumption CT](#pyenphase.Envoy.consumption_meter_type) are available from the envoy model.

Phase names are enumerated as `L1`, `L2`, and `L3` by `pyenphase.const.PhaseNames`. Phase modes are enumerated as `single`, `split` and `three` by `pyenphase.models.meters.EnvoyPhaseMode`. The CT meter types are enumerated as `production`, ``storage`, `net-consumption` and `total-consumption` by `pyenphase.models.meters.CtType`.

Be aware that `phase_count` and `phase_mode` applies for all configured CT's. The Envoy metered can however be configured with only 1, 2 or all 3 CT. In this case the not used CT data in `system_production_phases` or `system_consumption_phases` or `system_storage_phases` will be `None`

The Envoy property [active_phase_count](#pyenphase.Envoy.active_phase_count) reports the number of phases reported in the production and consumption report. This will be 0 for `single` and `split` phase use and the actual used phases for `three` mode.

```python

from pyenphase import Envoy
from pyenphase.const import PhaseNames
from pyenphase.models.meters import CtType, EnvoyPhaseMode

envoy = Envoy(host_ip_or_name)
await envoy.setup()
print(f'Envoy {envoy.host} running {envoy.firmware}, sn: {envoy.serial_number}')

await envoy.authenticate(username=username, password=password, token=token)

await envoy.probe()

print(f'Number of configured Phases: {envoy.phase_count}')
print(f'Number of configured CT meters: {envoy.ct_meter_count}')
print(f'Phases are configured in: {envoy.phase_mode} mode')
print(f'Phases reported in production/consumption: {envoy.active_phase_count} mode')

```
