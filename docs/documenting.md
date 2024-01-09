# Coding for documentation

This documentation is build from written materials as well as from the source code. The written materials augment what is available in the source code and provide examples or howto's. Using good commenting practices in the code greatly helps with improving this documentation as well.

## Autodoc

The module is configured to use [Sphynx](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) to auto-document the source code and utilizes the [Napoleon](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html) extension to parse Numpy and Google style docstrings. In your IDE use tools like autoDocstring for VSCode to generate sphinx-notype docstring skeletons. [^1]

[^1]: Sphinx-notype seems a balance between effort and information provision.

### Docstring

Example of a docstring generated with autoDoc and [included in this documentation](#pyenphase.models.system_production.EnvoySystemProduction.from_v1_api) and types automatically added:

```python
    @classmethod
    def from_v1_api(cls, data: dict[str, Any]) -> EnvoySystemProduction:
        """Initialize from the V1 API.

        :param data:  JSON reply from api/v1/production endpoint
        :return: Lifetime, last seven days, todays energy and current power for solar production
        """
```

### Attributes

Postfix attributes with a `#: Comment` to provide descriptions that are used in [generated documentation](#EnvoySystemProduction)

```python
@dataclass(slots=True)
class EnvoySystemProduction:
    """Model for the Envoy's production data."""

    watt_hours_lifetime: int  #: Lifetime Energy produced
    watt_hours_last_7_days: int  #: Energy produced in previous 7 days (not including today)
    watt_hours_today: int  #: Energy produced since start of day
    watts_now: int  #: Current Power production
```

Similar for enumerations

```python
class SupportedFeatures(enum.IntFlag):
    """ Flags for each feature supported

    :param enum: Feature Name
    """
    INVERTERS = 1  #: Can report Invertrs
    METERING = 2  #: Can report CT Meter data
```
