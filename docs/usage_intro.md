# Data collection

## Setup

Access to the Envoy device requires specifying its ip address or dns name when creating an Instance of the [Envoy class](#pyenphase.Envoy).

Next the envoy serial number and active firmware version should be obtained to identify which authentication method is required. Use the [setup method](#pyenphase.Envoy.setup).

Once the firmware version is known, [authentication](./usage_authentication.md#authentication) can take place using the required parameters for the firmware. The [authenticate method](#pyenphase.Envoy.authenticate) requires a username, password, and, in some cases, a JWT Token—[depending on the active firmware](./usage_authentication.md#authentication).

```python
from pyenphase import Envoy, EnvoyData

envoy = Envoy(host_ip_or_name)
await envoy.setup()
print(f'Envoy {envoy.host} running {envoy.firmware}, sn: {envoy.serial_number}')

await envoy.authenticate(username=username, password=password, token=token)

```

## Close

The Envoy class uses an [aiohttp client session](https://docs.aiohttp.org/en/stable/client_reference.html)
for http communication. The caller can optionally specify a client session when [instantiating the class](#pyenphase.Envoy).
If no client session is specified, pyenphase will create one.

The client session created by pyenphase must be closed at application exit. Use [envoy.close()](#pyenphase.Envoy.close) to close the created session.

```python
from pyenphase import Envoy, EnvoyData

envoy = Envoy(host_ip_or_name)
await envoy.setup()
print(f'Envoy {envoy.host} running {envoy.firmware}, sn: {envoy.serial_number}')

await envoy.authenticate(username=username, password=password, token=token)

data: EnvoyData = await envoy.update()

await envoy.close()
```

## Update

Upon authentication completion, the data can be collected (repeatedly) using the [update method](#pyenphase.Envoy.update).

```python

while True:
    data: EnvoyData = await envoy.update()

    print(f'Watts: {data.system_production.watts_now}')
    print(f'TodaysEnergy: {data.system_production.watt_hours_today}')
    print(f'LifetimeEnergy: {data.system_production.watt_hours_lifetime}')
    print(f'Last7DaysEnergy: {data.system_production.watt_hours_last_7_days}')

    await asyncio.sleep(some_time)
```

For all available data refer to [Data](./data.md).

## Probe

When data is first collected, the update method will perform a probe of the Envoy to determine what data is actually available. This may vary by model or running firmware version. This probing also provides the data for various envoy properties.

If the need exists to inspect properties before first data collection, use the [probe method](#pyenphase.Envoy.probe).

```python
from pyenphase import Envoy, EnvoyData

envoy = Envoy(host_ip_or_name)
await envoy.setup()
print(f'Envoy {envoy.host} running {envoy.firmware}, sn: {envoy.serial_number}')

await envoy.authenticate(username=username, password=password, token=token)

await envoy.probe()
print(f'Phases: {envoy.phase_count}')

production_ct = 'installed' if envoy.production_meter_type else 'not installed'
consumption_ct = 'installed' if envoy.consumption_meter_type else 'not installed'
print(f'This envoy has Production CT {production_ct} and Consumption CT {consumption_ct}')

```
