# Data

The pyenphase package collects {py:class}`~pyenphase.EnvoyData` from a specific set of endpoints on the Envoy. The set is based on the home owner [authorization level](./usage_authentication.md#authorization-levels) as common denominator. Additional endpoints [can be obtained](./requests.md#requests), but require application logic.

Firmware version, system serial-number and part-number are collected from `/info` endpoint. Other endpoints are:

```{include} ../src/pyenphase/const.py
:start-after : Include in docs from here
:end-before : Include in docs to here
:literal:
```

```{toctree}
:maxdepth: 3
:hidden:

data_production

data_consumption

phase_data

data_inverters

data_ensemble

data_ctmeter

data_raw

endpoint_json

known_issues

```
