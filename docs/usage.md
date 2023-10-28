# Usage

The pyenphase package provides the Envoy class to collect data from [Enphase IQ Gateway](https://enphase.com/en-us/products-and-services/envoy-and-combiner) (formerly known as Envoy). To use this package, import it:

```python
import pyenphase
```

## Initialization

Access to the Envoy device requires specifying a username and password or a JWT Token. What these are and if the token is required depends on the firmware active in the Envoy. What features and data are offered by the Envoy depends on the Envoy type and firmware.

The active firmware version can be obtained without any authentication and is the first setup in the initialization.

Once the firmware version is known, authentication can take place using the required parameters for the firmware.

Upon successful authentication the data can be collected.

```python
from pyenphase import Envoy, EnvoyData

envoy = Envoy(host_ip_or_name)
await envoy.setup()
print(f'Envoy {envoy.host} running {envoy.firmware}, sn: {envoy.serial_number}')

await envoy.authenticate(username=username, password=password, token=token)

while True:
    data: EnvoyData = await envoy.update()

    print(f'Watts: {data.system_production.watts_now}')
    print(f'TodaysEnergy: {data.system_production.watt_hours_today}')
    print(f'LifetimeEnergy {data.system_production.watt_hours_lifetime}')
    print(f'Last7DaysEnergy {data.system_production.watt_hours_last_7_days}')

    time.sleep(some_time)
```

## Authentication

Before firmware 7, authentication was based on username/password. In these cases either `Envoy` or `Installer` usernames with a blank password or a known username/password can be used. The token is not utilized. The authentication module will calculate the passwords for these 2 accounts based on the serial number retrieved by the setup method.

With firmware 7, token based authentication is required. The authentication module can retrieve the token from the Enlighten website using the Enlighten username and password, which need to be specified. If the token is known, it can be specified and it will be used instead of obtaining one from the internet.

```python
envoy = Envoy(host_ip_or_name)
await envoy.setup()
await envoy.authenticate(username=username, password=password, token=token)
```

### Re-Authentication

When authorization is omitted or data requests experience an authorization failure (401 or 403) an `EnvoyAuthenticationRequired` error is returned. When this occurs, authorization should be repeated.

```python
    try:
        data: EnvoyData = await envoy.update()

    except EnvoyAuthenticationRequired:
        await envoy.authenticate(username=username, password=password)
```

### Obtain and renew token

Upon completion of the authentication the token can be requested and stored for later re-use in authentication. The application should check for token expiry and request timely renewal. Until the token is expired it can be used with each authenticate request.

```python
from pyenphase import Envoy
from pyenphase.auth import EnvoyTokenAuth

token: str = None

envoy = Envoy(host_ip_or_name)
await envoy.setup()
await envoy.authenticate(username=username, password=password, token=token)

assert isinstance(envoy.auth, EnvoyTokenAuth)
token = envoy.auth.token
expire_time = envoy.auth.expire_timestamp

while True:
    try:
        data: EnvoyData = await envoy.update()

    except EnvoyAuthenticationRequired:
        if expire_time < now.timestamp():
            # token expired, refresh it
            await self.envoy.auth.refresh()
        else:
            # some envoy outage
            await envoy.authenticate(username=username, password=password,token=token)
```

### Authorized levels

Enphase accounts are either home-owner or installer/DIY accounts. The Home owner account provides access to the data information endpoints. The installer account has in addition access to configuration and setup endpoints as well. The authentication class provides the methods `is_consumer` and `manager_token` to determine the nature of the account.

```python
assert isinstance(envoy.auth, EnvoyTokenAuth)
token = envoy.auth.token
if envoy.auth.manager_token:
    ...
if envoy.auth.is_consumer:
    ...
```

### Authentication over firmware update

A special case of Envoy outage is the firmware update. These get pushed by Enphase, not frequently and not always at an expected moment. It will cause an outage of the Envoy during the patching process and an authentication error when communication is restored. Re-authentication as described above may work with existing token or it may fail and a new token would be needed. Furthermore the firmware version has changed and it may have impact on behavior. The Firmware version is only obtained in the setup method of the Envoy, this needs a repeat as well in this case.

```python
from pyenphase import Envoy, EnvoyData

envoy = Envoy(host_ip_or_name)
await envoy.setup()
firmware=envoy.firmware

await envoy.authenticate(username=username, password=password, token=token)

while True:
    try:
        data: EnvoyData = await envoy.update()

    except EnvoyAuthenticationRequired:
        expire_time = envoy.auth.expire_timestamp
        if expire_time <> now.timestamp():
            await self.envoy.auth.refresh()
        else:
            # potential outage, get firmware
            await envoy.setup()
            # authenticate without token to get new one
            await envoy.authenticate(username=username, password=password)
            # if firmware changed on us for re-init of data updaters
            if firmware != envoy.firmware:
                envoy.probe()
```

The probe method shown in above example is normally called one-time by envoy.update() for initialization and is never repeated once it's done. After a firmware update the client either needs to restart or force the probe to re-initialize all data collections with up-to-date information.

## Data

The pyenphase package collects data from a specific set of endpoint on the Envoy. The set is based on the home owner [authorization level](#authorized-levels) as common denominator. Additional endpoints [can be obtained](#bring-your-own-endpoint), but require application logic.

### System_Production data

This is the solar production data reported by the Envoy, class `EnvoySystemProduction`.

```python
    data: EnvoyData = await envoy.update()

    print(f'Watts: {data.system_production.watts_now}')
    print(f'TodaysEnergy: {data.system_production.watt_hours_today}')
    print(f'LifetimeEnergy {data.system_production.watt_hours_lifetime}')
    print(f'Last7DaysEnergy {data.system_production.watt_hours_last_7_days}')
```

The source of the data differs by Envoy type and firmware level. For metered Envoy types with configured current transformer (CT) production meter data comes from the /production endpoint with CT meter data. For non-metered Envoy types data comes from the `/api/v1/production` endpoint as calculated by the Envoy from inverter data.

### System_Consumption data

This is the energy consumption by the house reported by the Envoy, class `EnvoySystemConsumption`. It is only available for metered Envoy with installed and configured consumption CT Meter.

```python
    data: EnvoyData = await envoy.update()

    if data.system_consumption:
        print(f'Watts: {data.system_consumption.watts_now}')
        print(f'TodaysEnergy: {data.system_consumption.watt_hours_today}')
        print(f'LifetimeEnergy {data.system_consumption.watt_hours_lifetime}')
        print(f'Last7DaysEnergy {data.system_consumption.watt_hours_last_7_days}')
```

### Production and Consumption Phase data

Only available for metered Envoy with installed and configured CT meter in `three` phase mode and more then 1 phase active. It is reported for solar production and house consumption if these are enabled. Data is in [system_production_phases: dict[str,EnvoySystemProduction]](#system_production-data) and [system_consumption_phases: dict[str,EnvoySystemConsumption]](#system_consumption-data). Phases are named `L1`, `L2`, and `L3`.

```python
    data: EnvoyData = await envoy.update()

    if Envoy.phase_count > 1:
        for phase in data.system_production_phases:
            print(f'{phase} Watts: {data.system_production_phases[phase].watts_now}')
            print(f'{phase} TodaysEnergy: {data.system_production_phases[phase].watt_hours_today}')
            print(f'{phase} LifetimeEnergy {data.system_production_phases[phase].watt_hours_lifetime}')
            print(f'{phase} Last7DaysEnergy {data.system_production_phases[phase].watt_hours_last_7_days}')
```

### Inverter data

Individual inverter data, available for model as of firmware 3.9. are reported in `inverters: dict[str, EnvoyInverter]` attribute.

```python
for inverter in data.inverters:
    print (f'{inverter} sn: {data.inverters[inverter].serial_number}')
    print (f'{inverter} watts: {data.inverters[inverter].last_report_watts}')
    print (f'{inverter} max watts: {data.inverters[inverter].max_report_watts}')
    print (f'{inverter} last report: {data.inverters[inverter].last_report_date}')
```

### Encharge data

tbd

### Enpower data

tbd

### Raw data

All data for all endpoints is stored as received in the `raw: dict[str, Any]` attribute, keyed by the endpoint path.

```JSON
{
    "/production": {
        ...
    },
    "/api/v1/production/inverters": [{
        ...
    )],
    ...
}
```

## Bring your own endpoint

The pyenphase package can be used to obtain Envoy data from endpoints not already collected. Access to these endpoint is enabled by the [Authentication level](#authorized-levels) set during authentication. Data is returned directly to the caller and not stored in the Envoy data model.

```python
envoy = Envoy(host_ip_or_name)
await envoy.setup()
await envoy.authenticate(username=username, password=password, token=token)

myresponse: httpx.Response = await envoy.request('/my/own/endpoint')
status_code = response.status_code
if status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
    # authentication error

content = myresponse.content

```

## Register updater

The package can be extended by registering an additional `updater` based on a sub class of `EnvoyUpdater`. Such an updater can serve as an additional data source for existing data attributes. It can only store data in Envoy's [`raw`](#raw-data) attribute or in one of the existing data attributes. New attributes can not be added by an appender.

An updater requires 2 methods. A `probe` method which is used to initialize the updater and is only called once, and an `update` method which is collecting the data. Each may collect the same or different data based on the needs. The updater will have to provide same data and features as other updaters for the data attribute.

## Envoy methods and properties

Include some autogenerated list here
