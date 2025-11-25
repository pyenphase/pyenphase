# Endpoint JSON

This section describes the Envoy data used by the library.

Enphase's installer resource website documents the IQ Gateway local API. As it’s a dynamic resource, use the filters for “Communication Device” and select the Envoy or IQ Gateway types. This [example link](https://enphase.com/installers/resources/documentation/communication) pre-selects communication documents. Use the product filters for Envoy and the “Design and Tech Briefs” topic filter.

A wealth of information on the Enphase local Envoy api is available from [Matthew1471's github repository](https://github.com/Matthew1471/Enphase-API), which is an excellent resource.

The endpoints used by the library are:

```{include} ../src/pyenphase/const.py
:start-after: Include in docs from here
:end-before: Include in docs to here
:literal:
```

## /info

### description

This endpoint is accessible without token authorization and provides information on system serial-number, part-numbers, running packages, firmware version and build date. It returns an xml formatted data set.

### xml

```{literalinclude} ./json_data/info.xml
:language: xml
```

## /home

### description

This endpoint is accessible without token authorization and provides information on configured network interfaces and communication. It is used to retrieve active network device when using {py:attr}`~pyenphase.Envoy.interface_settings`.

### json

```{literalinclude} ./json_data/home.json
:language: json
```

## /api/v1/production

### description

This endpoint is used for production data of a non‑metered Envoy or a metered Envoy without CTs installed. It only contains aggregated phase data. Data is measured/calculated by the Envoy.

Also see [Known Issues](known_issues.md#production--consumption-data).

### JSON

```{literalinclude} ./json_data/api_v1_production.json
:language: json
```

## /api/v1/production/inverters

### description

This is the endpoint used for basic inverter production data.

### JSON

```{literalinclude} ./json_data/api_v1_production_inverters.json
:language: json

```

## /ivp/meters

### description

This is the endpoint used for installed CT meters configuration.

### JSON

```{literalinclude} ./json_data/ivp_meters.json
:language: json

```

## /ivp/meters/readings

### description

This is the endpoint used for CT meter readings.

### JSON

```{literalinclude} ./json_data/ivp_meters_readings.json
:language: json

```

## /ivp/pdm/device_data

### description

This is the endpoint used for detailed inverter data.

Also see [Known Issues](known_issues.md#inverter-device-data).

### JSON

```{literalinclude} ./json_data/ivp_pdm_device_data.json
:language: json

```

## /production.json?details=1

### description

This is the default endpoint for production and consumption data. It contains data for aggregated and individual phases. Data is measured/calculated by the Envoy. Individual phase data is in the `lines` segment.

- For non-metered Envoy, the `type: "eim"` sections are not present.
- For Envoy-metered without a [_production_ CT](data_ctmeter.md#ct-model):
  - the `production` item where `type == "eim"` and `measurementType == "production"` has `activeCount == 0`.
- For Envoy-metered with:
  - a [_net-consumption_ CT](data_ctmeter.md#ct-model), the _total-consumption_ data is calculated by the Envoy.
  - a [_total-consumption_ CT](data_ctmeter.md#ct-model), the _net-consumption_ data is calculated by the Envoy.
- For Envoy-metered without any _consumption_ CT:
  - the `consumption` item where `type == "eim"` and `measurementType == "net-consumption"` has `activeCount == 0`;
  - the `consumption` item where `type == "eim"` and `measurementType == "total-consumption"` has `activeCount == 0`.

Also see [Known Issues](known_issues.md#production--consumption-data).

### JSON

```{literalinclude} ./json_data/production_details.json
:language: json

```

## /production

### description

This is an endpoint for production and consumption data used when older firmware is running in the Envoy and the [standard endpoint](#productionjsondetails1) is not providing data. It only contains data for aggregated phases, no individual phase data is available. Data is measured/calculated by the Envoy.

- For non-metered Envoy, the `type: "eim"` sections are not present.
- For Envoy-metered without a [_production_ CT](data_ctmeter.md#ct-model):
  - the `production` item where `type == "eim"` and `measurementType == "production"` has `activeCount == 0`.
- For Envoy-metered with:
  - a [_net-consumption_ CT](data_ctmeter.md#ct-model), the _total-consumption_ data is calculated by the Envoy.
  - a [_total-consumption_ CT](data_ctmeter.md#ct-model), the _net-consumption_ data is calculated by the Envoy.
- For Envoy-metered without any _consumption_ CT:
  - the `consumption` item where `type == "eim"` and `measurementType == "net-consumption"` has `activeCount == 0`;
  - the `consumption` item where `type == "eim"` and `measurementType == "total-consumption"` has `activeCount == 0`.

### Known issues

Also see [Known Issues](known_issues.md#production--consumption-data).

### JSON

```{literalinclude} ./json_data/production.json
:language: json

```
