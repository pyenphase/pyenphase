# Requests

The pyenphase package can be used to send any request to the Envoy. Either to obtain data from endpoints not already collected, or send PUT or POST requests to the Envoy. Access to the used endpoints is enabled by the [Authorization level](./usage_authentication.md#authorization-levels) set during authentication. The request response is returned to the caller and not stored in the Envoy data model.

```python
envoy = Envoy(host_ip_or_name)
await envoy.setup()
await envoy.authenticate(username=username, password=password, token=token)

myresponse: aiohttp.ClientResponse = await envoy.request('/my/own/endpoint')
status_code = myresponse.status

myjson_data = await myresponse.json()

await envoy.close()
```

You can run the package using {py:meth}`Envoy.request() <pyenphase.Envoy.request>` only (without calling [probe](usage_intro.md#probe) and [update](usage_intro.md#update)), which provides an API into the Envoy without using the internally pre-configured data collections.

## ClientResponse

{py:meth}`Envoy.request() <pyenphase.Envoy.request>` returns an [aiohttp.ClientResponse](https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientResponse) as the result. [^1]

[^1]: This is a breaking change from version 1 where an httpx.Response was returned.

To access the response data, use [aiohttp.ClientResponse.read()](https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientResponse.read) for the raw bytes, [aiohttp.ClientResponse.text()](https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientResponse.text) for a decoded `str`, or [aiohttp.ClientResponse.json()](https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientResponse.json) for a parsed JSON object.

Note that `ClientResponse.json()` uses Python’s standard decoder `json.loads` by default. To use a different decoder, pass it via the `loads=` parameter, for example:

```python
import orjson
myjson_data = await myresponse.json(loads=orjson.loads)
```
