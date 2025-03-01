# Requests

The pyenphase package can be used to send any request to the Envoy. Either to obtain data from endpoints not already collected, or send PUT or POST requests to the Envoy. Access to the used endpoints is enabled by the [Authorization level](./usage_authentication.md#authorization-levels) set during authentication. The request response is returned to the caller and not stored in the Envoy data model.

```python
envoy = Envoy(host_ip_or_name)
await envoy.setup()
await envoy.authenticate(username=username, password=password, token=token)

myresponse: httpx.Response = await envoy.request('/my/own/endpoint')
status_code = myresponse.status_code
if status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
    # authentication error

content = myresponse.content

```

You can run the package only using requests only (without calling probe and update), which provides an API into the Envoy without using the internally pre-configured data collections.
