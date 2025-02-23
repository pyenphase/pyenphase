# Usage

The pyenphase package provides the [Envoy class](#pyenphase.Envoy) to collect data from [Enphase IQ Gateway](https://enphase.com/en-us/products-and-services/envoy-and-combiner). To use this package, import classes and modules from it:

```python
from pyenphase import Envoy, EnvoyData

envoy: Envoy = Envoy(host)
await envoy.setup()

await envoy.authenticate(username=username, password=password, token=token)
data: EnvoyData = await envoy.update()
```

```{toctree}
:maxdepth: 3
:hidden:

usage_intro
usage_authentication
requests
advanced

```
