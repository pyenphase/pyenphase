# Advanced Usage

## Bring your own endpoint

The pyenphase package can be used to obtain Envoy data from endpoints not already collected. Access to these endpoint is enabled by the [Authorization level](./usage_authentication.md#authorization-levels) set during authentication. Data is returned directly to the caller and not stored in the Envoy data model.

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

The package can be extended by registering an additional `updater` as a sub class of `EnvoyUpdater`. Such an updater can serve as an alternative data source for existing data sources and provide requested data if other updaters don't. The added updater can only store data in one of the existing data attributes of [EnvoyData](#pyenphase.EnvoyData) or store the raw data in Envoy's [`raw`](./data_raw.md#raw-data) attribute.

An updater requires 2 methods. A `probe` method which is used to initialize the updater and is only called once and signals capability to provide the data, and an `update` method which is called repeatidly to collect the data. Each may collect the same or different data based on the needs. The updater will have to provide same data as other updaters for the data attributes in scope.

### Example: Extend EnvoySystemProduction

The [EnvoySystemProduction](#pyenphase.models.system_production.EnvoySystemProduction) class provides overall [production data](./data_production.md) reported by the Envoy. The data is sourced from various endpoints based on Envoy type and the firmware running in the Envoy. This package does not include reporting from Envoy Legacy HTML pages.[^1]

[^1]: Prime intent during design was to work with [Home Assistant](https://www.home-assistant.io/) and Home Assistant has an [architectural rule denying the use of webscraping](https://github.com/home-assistant/architecture/blob/master/adr/0004-webscraping.md) for core integrations. Though it allows scraping for custom integrations. This package however can be used to build any application, hence this example.

#### Legacy Envoy SystemProduction

This example will get production data from legacy Envoy html production page and report it in the existing EnvoySystemProduction class also used for other Envoy versions. First step is to define a data model as a sub-class of [EnvoySystemProduction](#pyenphase.models.system_production.EnvoySystemProduction) and its method to obtain the data from the returned Envoy html. In below example the method 'from_production_legacy' provides this. The returned data should be the EnvoysSystemProduction class members.

```python
from pyenphase import EnvoyData, EnvoySystemProduction, register_updater
from pyenphase.const import URL_PRODUCTION, SupportedFeatures
from pyenphase.envoy import get_updaters
from pyenphase.exceptions import ENDPOINT_PROBE_EXCEPTIONS

# regex to find production data in html page
_KEY_TO_REGEX = {
    "watts_now": r"<td>Current.*</td>\s*<td>\s*(\d+|\d+\.\d+)\s*(W|kW|MW)</td>",
    "watt_hours_last_7_days": r"<td>Past Week</td>\s*<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>",
    "watt_hours_today": r"<td>Today</td>\s*<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>",
    "watt_hours_lifetime": r"<td>Since Installation</td>\s*<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>",
}

class LegacyEnvoySystemProduction(EnvoySystemProduction):
    """Get production data from legacy Envoy html"""
    def from_production_legacy(cls, text: str) -> EnvoySystemProduction:
        """Legacy parser."""
        data: dict[str, int] = {
            "watts_now": 0,
            "watt_hours_today": 0,
            "watt_hours_last_7_days": 0,
            "watt_hours_lifetime": 0,
        }

        # extract the date from the html using regex
        for key, regex in _KEY_TO_REGEX.items():
            if match := re.search(regex, text, re.MULTILINE):
                unit = match.group(2).lower()
                value = float(match.group(1))
                # scale units to w or wh
                if unit.startswith("k"):
                    value *= 1000
                elif unit.startswith("m"):
                    value *= 1000000
                data[key] = int(value)
        return cls(**data)
```

#### LegacyProductionScraper

Next define the actual updater as a subclass of [EnvoyUpdater](#pyenphase.updaters.base.EnvoyUpdater). The updater will collect the data and use above model to report the data.

```python
class LegacyProductionScraper(EnvoyUpdater):
```

##### Probe

As described before, the `probe` method is called once at initialization to detect and configure all that is needed. It is passed the bit mask (flags) of already `SupportedFeatures` by other updaters. If the feature this updater provides is already provided by an other updater, ours should exit and leave it to the other updater. In this example the feature flag is `SupportedFeatures.PRODUCTION`. If not set yet, the updater should configure and return `SupportedFeatures.PRODUCTION` flag set to signal the Envoy class it should be used to obtain data or None if not. Returning a set SupportedFeatures flag will cause the update method to be used during data collection.

To collect the data the EnvoyUpdater class provides the methods `_probe_request(endpoint)` and `_json_probe_request(endpoint)`. These methods can be used retrieve text/html or json data.

```python
    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe the Envoy for for Production HTML and return PRODUCTION SupportedFeature."""
        if SupportedFeatures.PRODUCTION in discovered_features:
            # Already discovered from another updater, leave alone
            return None
        try:
            # get html data from the envoy using the probe_request
            response = await self._probe_request(URL_PRODUCTION)
            data = response.text
        except ENDPOINT_PROBE_EXCEPTIONS:
            return None

        # check if response contains what we expect
        if "Since Installation" not in data:
            return None

        # remember and return PRODUCTION as my supported feature.
        self._supported_features |= SupportedFeatures.PRODUCTION
        return self._supported_features
```

##### Update

The `update` method is called at each update cycle to provide the actual data. It is passed the EnvoyData class to store the data to. The data colloction methods provided by the EnvoyUpdater class are `_json_request(endpoint)` and `_request(endpoint)`. Typically the method uses a data model to extract the data from the response.

```python
    async def update(self, envoy_data: EnvoyData) -> None:
        """Update the Envoy for this updater."""
        # Get the HTML data from the Envoy
        response = await self._request(URL_PRODUCTION)
        production_data = response.text

        # Store the data as is in the raw json of the EnvoyData
        envoy_data.raw[URL_PRODUCTION] = production_data

        # Store data in Envoy data using our data model.
        envoy_data.system_production = (
            LegacyEnvoySystemProduction.from_production_legacy(production_data)
        )
```

##### Register updater

To make the updater available for use, it must be registered with the Envoy using `register_updater`. Upon completion of the registration perform the usual setup, authentication and probe of the Envoy and start data collection.

```python
    # Initialize Envoy, setup and authenticate
    envoy = Envoy(host)

    # register our updater for legacy envoy
    remove = register_updater(LegacyProductionScraper)
    assert LegacyProductionScraper in get_updaters()

    # setup and authenticate with Envoy
    await envoy.setup()
    await envoy.authenticate(username=username, password=password, token=token)

    # probe what endpoints are available
    await envoy.probe()

    # get data, the production values now fill from html
    data: EnvoyData = await envoy.update()

    # remove our updater from the envoy
    remove()
    assert LegacyProductionScraper not in get_updaters()

```

Registering the updater inserts it at the end of the updaters giving priority to existing updaters to return production (in this example) data. If all prior ones fail, the newly registered one will be used. Adding a new one only makes sense for cases where the endpoint is not successfully accessed by the other ones. This is implemented by the use of the SupportedFeatures flags.

### Example: New attribute EnvoyHomeInformation

The previous example [Extend EnvoySystemProduction](#example-extend-envoysystemproduction) added a new data source for an existing attribute. Similarly a datasource for a new attribute can be added by registering an updater. The process is the same as the previous example with only difference being no existing EnvoyData attribute available and the EnvoyData.raw is to be used. This example will add retrieval of data from the Envoy Home endpoint /home.json.

#### EnvoyHomeInformation

The datamodel to use is new and designed towards the needs.

```python
from pyenphase import EnvoyData, EnvoySystemProduction, register_updater
from pyenphase.const import URL_PRODUCTION, SupportedFeatures
from pyenphase.envoy import get_updaters
from pyenphase.exceptions import ENDPOINT_PROBE_EXCEPTIONS

@dataclass(slots=True)
class EnvoyHomeInformation():
    """Get home data from Envoy"""

    software_build_epoch: int
    timezone: str

    @classmethod
    def from_home(cls, data: dict[str, Any]):
        """Initialize from the Home API."""
        return cls(
            software_build_epoch=data["software_build_epoch"],
            timezone=data["timezone"],
        )
```

#### EnvoyHome

As described, the updater is a subclass of [EnvoyUpdater](#pyenphase.updaters.base.EnvoyUpdater) and provides `probe` and `update` methods. As this is a new attribute no SupportedFeatures flags exists for it. The next higher flag is used to signal back this updater has data to provide. [^2]

[^2]: When adding multiple new unique features make sure flags are unique by adding more left shits as needed `myflag = 1 << (len(SupportedFeatures) + 1)`.

```python
class EnvoyHome(EnvoyUpdater):
    async def probe(
        self, discovered_features: SupportedFeatures
    ) -> SupportedFeatures | None:
        """Probe the Envoy for home information."""
        myflag = 1 << len(SupportedFeatures)
        if myflag & discovered_features:
            # Already discovered from another updater
            return None
        try:
            home_json: dict[str, Any] = await self._json_probe_request("/home.json")
        except ENDPOINT_PROBE_EXCEPTIONS:
            return None

        # our data not found in the page
        if "software_build_epoch" not in home_json:
            return None

        # signal we can provide this data
        self._supported_features |= myflag
        return self._supported_features


    async def update(self, envoy_data: EnvoyData) -> None:
        """Update the Envoy for this /home.json."""
        home_data = await self._json_request("/home.json")
        # No EnoyData attribute, only return raw as is
        envoy_data.raw["/home.json"] = home_data
```

As there's no EnvoyData attribute to store the `EnvoyHome` data it should be obtained by the application using the model.

```python
    # Initialize Envoy, setup and authenticate
    envoy = Envoy(host)

    # register our updater for legacy envoy
    remove = register_updater(EnvoyHome)
    assert EnvoyHome in get_updaters()

    # setup and authenticate with Envoy
    await envoy.setup()
    await envoy.authenticate(username=username, password=password, token=token)

    # probe what endpoints are available
    await envoy.probe()

    # get data, the production values now fill from html
    data: EnvoyData = await envoy.update()

    # obtain our data from raw using the model
    home_info: EnvoyHomeInformation = (
        EnvoyHomeInformation.from_home(data.raw['/home.json'])
    )
    print(f'Home info: {home_info.timezone}')


```
