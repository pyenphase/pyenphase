# Initialization

Access to the Envoy device requires specifying its ip address or dns name when creating an Instance of the [Envoy class](#pyenphase.Envoy).

Next the envoy serial number and active firmware version should be obtained to identify which authentication method is required. Use the [setup method](#pyenphase.Envoy.setup).

Once the firmware version is known, authentication can take place using the required parameters for the firmware. The [authenticate method](#pyenphase.Envoy.authenticate) requires a username and password and/or a JWT Token. What the username and password are and if the token is required [depends on the firmware](./usage_authentication.md#authentication) active in the Envoy.

Upon successful authentication the data collection can be initiated by using the [probe method](#pyenphase.Envoy.probe). This will gather and set all required information for the data collection.[^1]

Upon probe completion the data can be collected (repeatedly) using the [update method](#pyenphase.Envoy.update).

```python
from pyenphase import Envoy, EnvoyData

envoy = Envoy(host_ip_or_name)
await envoy.setup()
print(f'Envoy {envoy.host} running {envoy.firmware}, sn: {envoy.serial_number}')

await envoy.authenticate(username=username, password=password, token=token)

await envoy.probe()
print(f'Phases: {envoy.phase_count}')

while True:
    data: EnvoyData = await envoy.update()

    print(f'Watts: {data.system_production.watts_now}')
    print(f'TodaysEnergy: {data.system_production.watt_hours_today}')
    print(f'LifetimeEnergy {data.system_production.watt_hours_lifetime}')
    print(f'Last7DaysEnergy {data.system_production.watt_hours_last_7_days}')

    await asyncio.sleep(some_time)
```

For all available data refer to [Data](./data.md).

[^1]: The probe method will be called by the update method if not called before. It needs to be called only once to initiate data collection parameters.
