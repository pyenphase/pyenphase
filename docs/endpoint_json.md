# Endpoint JSON

This section describes the Envoy data used by the library.

Enphase's installer resource web-site has descriptions of the IQ Gateway local api. As this is a dynamic resource, best use the filters for communication device and select the Envoy or IQ Gateway types. This [example link](https://enphase.com/installers/resources/documentation/communication) selects communication documents (at least one time). Use product filters for Envoy and `Design and Tech briefs` for topic filter.

A wealth of information on the Enphase local Envoy api is available from [Matthew1471's github repository](https://github.com/Matthew1471/Enphase-API), which is an excellent resource.

## /api/v1/production

### description

This is the endpoint used for production data of an Envoy non-metered or Envoy metered without CT installed. It only contains aggregated phase data. Data is measured/calculated by the Envoy.

Also see [Known Issue](known_issues.md#production--consumption-data).

### JSON

```{literalinclude} ./json_data/api_v1_production.json

```

## /api/v1/production/inverters

### description

This is the endpoint used for basic inverter production data.

### JSON

```{literalinclude} ./json_data/api_v1_production.json

```

## /ivp/pdm/device_data

### description

This is the endpoint used for detailed inverter data.

Also see [Known Issue](known_issues.md#inverter-device-data).

### JSON

```{literalinclude} ./json_data/ivp_pdm_device_data.json

```

## /production.json?details=1

### description

This is the default endpoint for production and consumption data. It contains data for aggregated and individual phases. Data is measured/calculated by the Envoy. Individual phase data is in the `lines` segment.

- For non-metered Envoy the `type: "eim"` sections are not present.
- For Envoy-metered without a [_production_ CT](data_ctmeter.md#ct-model):
  - the `production` `"type": "eim"`, `"measurementType": "production"`, `activeCount` will be zero.
- For Envoy-metered with:
  - a [_net-consumption_ CT](data_ctmeter.md#ct-model), the _total-consumption_ data is calculated by the Envoy.
  - a [_total-consumption_ CT](data_ctmeter.md#ct-model), the _net-consumption_ data is calculated by the Envoy.
- For Envoy-metered without any _consumption_ CT, the
  - `consumption` `type: "eim"` `"measurementType": "net-consumption"` `activeCount` will be zero.
  - `consumption` `type: "eim"` `"measurementType": "total-consumption"` `activeCount` will be zero.

Also see [Known Issue](known_issues.md#production--consumption-data).

### JSON

```{literalinclude} ./json_data/production_details.json

```

## /production

### description

This is an endpoint for production and consumption data used when older firmware is running in the Envoy and the [standard endpoint](#productionjsondetails1) is not providing data. It only contains data for aggregated phases, no individual phase data is available. Data is measured/calculated by the Envoy.

- For non-metered Envoy the `type: "eim"` sections are not present.
- For Envoy-metered without a [_production_ CT](data_ctmeter.md#ct-model):
  - the `production` `"type": "eim"`, `"measurementType": "production"`, `activeCount` will be zero.
- For Envoy-metered with:
  - a [_net-consumption_ CT](data_ctmeter.md#ct-model), the _total-consumption_ data is calculated by the Envoy.
  - a [_total-consumption_ CT](data_ctmeter.md#ct-model), the _net-consumption_ data is calculated by the Envoy.
- For Envoy-metered without any _consumption_ CT, the
  - `consumption` `type: "eim"` `"measurementType": "net-consumption"` `activeCount` will be zero.
  - `consumption` `type: "eim"` `"measurementType": "total-consumption"` `activeCount` will be zero.

### Known issues

Also see [Known Issue](known_issues.md#production--consumption-data).

### JSON

```{literalinclude} ./json_data/production.json

```
