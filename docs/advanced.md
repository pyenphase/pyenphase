# Advanced Usage

## Bring your own endpoint

The pyenphase package can be used to obtain Envoy data from endpoints not already collected. Access to these endpoint is enabled by the [Authentication level](./usage_authentication.md#authorized-levels) set during authentication. Data is returned directly to the caller and not stored in the Envoy data model.

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

The package can be extended by registering an additional `updater` based on a sub class of `EnvoyUpdater`. Such an updater can serve as an additional data source for existing data attributes. It can only store data in Envoy's [`raw`](./data_raw.md#raw-data) attribute or in one of the existing data attributes. New attributes can not be added by an appender.

An updater requires 2 methods. A `probe` method which is used to initialize the updater and is only called once, and an `update` method which is collecting the data. Each may collect the same or different data based on the needs. The updater will have to provide same data and features as other updaters for the data attribute.
