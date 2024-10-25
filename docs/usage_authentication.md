# Authentication

## Introduction

Before firmware 7, authentication was based on username/password using Digest. Either `Envoy` or `Installer` usernames with a blank password or a known username/password can be used. If the password is left blank, the authentication module will calculate the password for the 2 named accounts, based on the Envoy serial number.

As of firmware 7, token based authentication is required. The authentication module can retrieve the token from the Enlighten website using the Envoy serial number, the Enlighten username and password, which all need to be specified. If a token is known, it can be specified and it will be used instead of obtaining one from the Enlighten website. Even if a token is known, it's best practice to also specify username and password to enable automatic refresh of an expired token.

Based on the firmware version retrieved from the envoy in envoy.setup(), the [envoy.authenticate](#pyenphase.Envoy.authenticate) method will determine which of the 2 authentication methods to use.

This example will work with both firmware <7 and >=7. In the first case specify the local Envoy username `envoy`, in the latter case specify the Enlighten cloud credentials and the required token will be obtained from the Enlighten cloud.

```python
envoy = Envoy(host_ip_or_name)
await envoy.setup()
await envoy.authenticate(username=username, password=password)

```

For firmware >= 7 and a known token, specifying it will use it and skip reaching out to the Enlghten cloud.

```python
envoy = Envoy(host_ip_or_name)
await envoy.setup()
await envoy.authenticate(username=username, password=password, token=token)
```

## Obtain, re-use and renew token

Upon completion of the authentication, the token can be requested and stored for later reuse in authentication. At a next application startup, pass the stored token to envoy.authenticate, in addition to the username and password. Until the token is expired it can be used with each authenticate request. If the token is expired while using it in authentication, an exception [EnvoyAuthenticationError](#pyenphase.exceptions.EnvoyAuthenticationError) is returned. In that case redo the authentication without specifying a token to force getting a new one.

```python
from pyenphase import Envoy
from pyenphase.auth import EnvoyTokenAuth

token: str = "get token from some storage"

envoy = Envoy(host_ip_or_name)
await envoy.setup()
try:
    await envoy.authenticate(username=username, password=password, token=token)
except EnvoyAuthenticationError as exp:
    await envoy.authenticate(username=username, password=password)

```

The application should check for [token expiry](#pyenphase.auth.EnvoyTokenAuth.expire_timestamp) and request timely [renewal](#pyenphase.auth.EnvoyTokenAuth.refresh). Make sure to store a refreshed token again, access it using the [token property](#pyenphase.auth.EnvoyTokenAuth.token).

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
    # save token in some storage for later re-use

```

Enlighten user accounts can be type 'owner' or 'installer'. Token lifetime for an owner account is 1 year, while installer lifetime is 12 hours.

## Re-Authentication

When authentication is omitted or data requests experience an authorization failure (HTTP status 401 or 403) an [EnvoyAuthenticationRequired](#pyenphase.exceptions.EnvoyAuthenticationRequired) error is returned. When this occurs, authentication should be repeated.

```python
    try:
        data: EnvoyData = await envoy.update()

    except EnvoyAuthenticationRequired:
        await envoy.authenticate(username=username, password=password,token=token)
```

## Authentication over firmware update

A special case is the firmware update. These get pushed by Enphase, not frequently and not always at an expected moment. It will cause an outage of the Envoy during the patching process and an authentication error when communication is restored. Re-authentication as described above may work with existing token or it may fail and a new token would be needed. If the firmware upgrade changes from <7 to >=7, Enlighten credentials need to replace the local Envoy username/password.

Furthermore the firmware version has changed and it may have impact on behavior. The Firmware version is only obtained in the setup method of the Envoy, this needs a repeat as well in this case.

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
        # is token expired. if so refresh
        expire_time = envoy.auth.expire_timestamp
        if expire_time < now.timestamp():
            await self.envoy.auth.refresh()
        else:
            # potential outage, get firmware
            await envoy.setup()
            # if firmware changed on us force re-init of data updaters
            if firmware != envoy.firmware:
                # authenticate without token to get new one
                await envoy.authenticate(username=username, password=password)
                # re-init communication based on new firmware
                envoy.probe()
```

## Authorization levels

Enphase accounts are either home-owner or DIY/installer accounts. The Home owner account provides access to the data information endpoints. The DIY/installer accounts have in addition access to configuration and setup endpoints as well [^2]. The authentication class provides the property `token_type` to determine the nature of the account. This returns `owner` or `installer` based on the token type.

```python
assert isinstance(envoy.auth, EnvoyTokenAuth)
token = envoy.auth.token
if envoy.auth.token_type == "user":
    ...
else:
    ...
```

[^2]: Data provided by pyenphase is only sourced from endpoints that allow access by at least Home owner accounts. The Envoy [Request method](#pyenphase.Envoy.request) allows access to [additional endpoints](./advanced.md#bring-your-own-endpoint), provided the user account has the required authorization level.
