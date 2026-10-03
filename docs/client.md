# Client

The Envoy class uses an [aiohttp client session](https://docs.aiohttp.org/en/stable/client_reference.html)
for HTTP communication. [By default](./usage_intro.md#setup) pyenphase will create one to use. The caller can optionally specify a client session when constructing the {py:class}`pyenphase.Envoy`.

```python
import aiohttp

from pyenphase import Envoy, EnvoyData
from pyenphase.ssl import NO_VERIFY_SSL_CONTEXT

timeout = aiohttp.ClientTimeout(total=5.0, connect=1.0, sock_read=1.0)
connector = aiohttp.TCPConnector(ssl=NO_VERIFY_SSL_CONTEXT)
client = aiohttp.ClientSession(timeout=timeout, connector=connector)

envoy = Envoy(host_ip_or_name, client=client)
await envoy.setup()
```

In above example, a clientsession is created and specified when constructing the Envoy.

## Close

Client sessions need to be closed before application exit. To close the client session created by pyenphase use {py:meth}`pyenphase.Envoy.close` .
If an aiohttp ClientSession was provided when constructing the Envoy, {py:meth}`pyenphase.Envoy.close` will not close it; the caller should close it external from pyenphase.

```python
from pyenphase import Envoy, EnvoyData

envoy = Envoy(host_ip_or_name)
await envoy.setup()
print(f"Envoy {envoy.host} running {envoy.firmware}, sn: {envoy.serial_number}")

await envoy.authenticate(username=username, password=password, token=token)

data: EnvoyData = await envoy.update()

await envoy.close()
```

## Current client

The client in use can be obtained using the property {py:attr}`pyenphase.Envoy.current_client`.

```python
if (client := envoy.current_client) and not client.closed:
    ...
```

## New client

If the need exists to replace the client used by pyenphase, use {py:meth}`pyenphase.Envoy.new_client`. Similar to constructing the {py:class}`pyenphase.Envoy`, an optional aiohttp client session can be specified. If not specified, pyenphase will create a new one. If the active session was created by pyenphase, it will be closed before it is replaced by the new one.

```python
import aiohttp

from pyenphase import Envoy, EnvoyData
from pyenphase.ssl import NO_VERIFY_SSL_CONTEXT

envoy = Envoy(host_ip_or_name)
await envoy.setup()
await envoy.authenticate(username=username, password=password, token=token)
data: EnvoyData = await envoy.update()

# replace client created by pyenphase
timeout = aiohttp.ClientTimeout(total=5.0, connect=1.0, sock_read=1.0)
connector = aiohttp.TCPConnector(ssl=NO_VERIFY_SSL_CONTEXT)
client = aiohttp.ClientSession(timeout=timeout, connector=connector)

await envoy.new_client(client)
```
