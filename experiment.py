import asyncio
import os

from awesomeversion import AwesomeVersion

from pyenphase.envoy import Envoy


async def main() -> None:
    envoy = Envoy("envoy.local")

    await envoy.setup()

    if envoy.firmware >= AwesomeVersion("7.0.0"):
        username = os.environ.get("ENVOY_USERNAME")
        password = os.environ.get("ENVOY_PASSWORD")
        await envoy.authenticate(username, password)

    if envoy.auth is not None:
        print(envoy.auth.token)


asyncio.run(main())
