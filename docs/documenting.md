# Coding for documentation

This documentation is build from written materials as well as from the source code. The written materials augment what is available in the source code and provide examples or how-to's. Using good commenting practices in the code greatly helps with improving this documentation as well.

## Autodoc

The library is configured to use [Sphynx](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) to auto-document the source code and utilizes the [Napoleon](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html) extension to parse Numpy and Google style docstrings. In your IDE use tools like autoDocstring for VSCode to generate sphinx-notype docstring skeletons. [^1]

[^1]: Sphinx-notype seems a balance between effort and information provision.

### Docstring

Example of a docstring generated with autoDoc and [included in this documentation](#pyenphase.models.system_production.EnvoySystemProduction.from_v1_api) and types automatically added:

```python
    @classmethod
    def from_v1_api(cls, data: dict[str, Any]) -> EnvoySystemProduction:
        """
        Initialize from the V1 API.

        :param data:  JSON reply from api/v1/production endpoint
        :return: Lifetime, last seven days, todays energy and current power for solar production
        """
```

To add links to other modules from the docstring, use ":class:`path_to_some_class`" or ":any:`function_name`". This allows to refer to other modules to avoid repeating similar documentation.

```python
    def __init__(
        self,
        _client: httpx.AsyncClient,
        host: str,
    ) -> None:
        """
        Class for querying and determining the Envoy firmware version.

        :param client: httpx AsyncClient not verifying SSL
            certificates, see :class:`pyenphase.ssl`.
        :param host: Envoy DNS name or IP address
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
    """
    Flags for each feature supported

    :param enum: Feature Name
    """
    INVERTERS = 1  #: Can report Inverters
    METERING = 2  #: Can report CT Meter data
```

These can also be placed on the line before the attribute and consist of multiple lines

```python

#: Alias for :any:`create_no_verify_ssl_context`
#:
#: .. code-block:: python
#:
#:     import httpx
#:     from pyenphase.ssl import NO_VERIFY_SSL_CONTEXT
#:
#:     client = httpx.AsyncClient(verify=NO_VERIFY_SSL_CONTEXT)
#:
NO_VERIFY_SSL_CONTEXT = create_no_verify_ssl_context()
```

### Classes

Use the \_\_init\_\_ of a class to document the class parameters.

```python
   def __init__(
        self,
        self,
        host: str,
        host: str,
        cloud_username: str | None = None,
        cloud_username: str | None = None,
        cloud_password: str | None = None,
        cloud_password: str | None = None,
        envoy_serial: str | None = None,
        envoy_serial: str | None = None,
        token: str | None = None,
        token: str | None = None,
    ) -> None:
        """
        Class to authenticate with Envoy using Tokens.

        Use with Envoy firmware 7.x and newer

        :param host: local Envoy DNS name or IP Address
        :param cloud_username: Enlighten Cloud username, required to obtain new
            token when token is not specified or expired, defaults to None
        :param cloud_password: Enlighten Cloud password, required to obtain new
            token when token is not specified or expired, defaults to None
        :param envoy_serial: Envoy serial number, required to obtain new
            token when token is not specified or expired, defaults to None
        :param token: Token to use with authentication, if not specified,
            one will be obtained from Enlighten cloud if username, password
            and serial are specified, defaults to None
        """
```

## Documentation structure

### index.md

This is the documentation backbone, building the table of content and including all the individual documentation markdown files. As it's a markdown file itself, it is utilizing [sphynx directives](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html) to achieve this. In the markdown file place the directive in a fenced block with the directive between {}. The syntax between the fences is now as described for the sphynx directives.

Below example creates a main TOC entry for 'Installation & Usage' with 3 sub entries. The content of the 3 sub entries is read from the markdown files with the same names, these file must be present in same folder. Headers in the included files are relative to the caption and should start with a top level header.

    ```{toctree}
    :caption: Installation & Usage
    :maxdepth: 3

    installation
    usage
    advanced

    ```

### Auto-documenting from code

The majority of the markdown files contain descriptive text. To generate documentation from the [Docstrings and comments](#autodoc) in the code files, use a fenced `{eval-rst}` using [Autodoc directives](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#directives). Below example will auto-document the `EnvoyTokenAuth` class from the file auth.py.

    ```{eval-rst}
    .. autoclass:: pyenphase.auth.EnvoyTokenAuth
    :members:
    :undoc-members:
    :show-inheritance:
    :member-order: bysource
    :class-doc-from: init
    ```

The headers, order and Docstring in the specified classes, modules and functions will generate the documentation for classes, methods and properties. Include a section for each module or class to document. For `autoclass` directives make sure to add `:class-doc-from: init` in order for the Docstring of \_\_init\_\_ to be used in the documentation generation.

#### model_autodoc.md

This file generates the `Classes, methods and properties` section from the Docstrings. It is imported by index.md under the header 'Data & Reference'. In model_autodoc.md, include an entry for each module or class to be included in the documentation.

### conf.py

This is the overall setup for the document generation. Any extension to use in document creation, should be added here.

    extensions = [
        "myst_parser",
        "sphinx.ext.autodoc",
        "sphinx.ext.napoleon",
        "sphinx_autodoc_typehints",
    ]

## Build the docs locally

To test build the docs, change the working directory to the /docs folder in your project working folder. In there use

    make clean
    make html

The output is created in /docs/build/html. Open `index.html` in there to inspect the documentation locally.
