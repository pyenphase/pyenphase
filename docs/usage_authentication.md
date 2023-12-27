# Authentication

Before firmware 7, authentication was based on username/password. In these cases either `Envoy` or `Installer` usernames with a blank password or a known username/password can be used. The token is not utilized. The authentication module will calculate the passwords for these 2 accounts, if left blank, based on the serial number retrieved by the setup method.

As of firmware 7, token based authentication is required. The authentication module can retrieve the token from the Enlighten website using the retrieved Envoy serial number and the Enlighten username and password which need to be specified. If the token is known, it can be specified and it will be used instead of obtaining one from the internet.

```python
envoy = Envoy(host_ip_or_name)
await envoy.setup()
await envoy.authenticate(username=username, password=password, token=token)

```

## Obtain and renew token

Upon completion of the authentication, the token can be requested and stored for later re-use in authentication. The application should check for [token expiry](#pyenphase.auth.EnvoyTokenAuth.expire_timestamp) and request timely [renewal](#pyenphase.auth.EnvoyTokenAuth.refresh). Until the token is expired it can be used with each authenticate request.

```python
from pyenphase import Envoy
from pyenphase.auth import EnvoyTokenAuth

token: str = "get token from some storage"

envoy = Envoy(host_ip_or_name)
await envoy.setup()
await envoy.authenticate(username=username, password=password, token=token)

assert isinstance(envoy.auth, EnvoyTokenAuth)
expire_time = envoy.auth.expire_timestamp

if expire_time < (datetime.now() - timedelta(days=7)):
    await self.envoy.auth.refresh()

token = envoy.auth.token
# save token in some storage

```

## Re-Authentication

When authentication is omitted or data requests experience an authorization failure (401 or 403) an `EnvoyAuthenticationRequired` error is returned. When this occurs, authentication should be repeated.

```python
    try:
        data: EnvoyData = await envoy.update()

    except EnvoyAuthenticationRequired:
        await envoy.authenticate(username=username, password=password,token=token)
```

## Authorization levels

Enphase accounts are either home-owner or installer/DIY accounts. The Home owner account provides access to the data information endpoints. The installer account has in addition access to configuration and setup endpoints as well [^2]. The authentication class provides the methods `is_consumer` and `manager_token` to determine the nature of the account.

```python
assert isinstance(envoy.auth, EnvoyTokenAuth)
token = envoy.auth.token
if envoy.auth.manager_token:
    ...
if envoy.auth.is_consumer:
    ...
```

[^2]: Data provided by pyenphase is only sourced from endpoints that allow access by at least Home owner accounts. The Envoy [Request method](#pyenphase.Envoy.request) allows access to [additional endpoints](./advanced.md#bring-your-own-endpoint), provided the user account has the required authorization level.

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
        if expire_time < now.timestamp():
            await self.envoy.auth.refresh()
        else:
            # potential outage, get firmware
            await envoy.setup()
            # authenticate without token to get new one
            await envoy.authenticate(username=username, password=password)
            # if firmware changed on us force re-init of data updaters
            if firmware != envoy.firmware:
                envoy.probe()
```
