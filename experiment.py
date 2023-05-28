import asyncio
import os

import httpx
from awesomeversion import AwesomeVersion

from pyenphase.envoy import Envoy


async def main() -> None:
    envoy = Envoy("envoy.local")

    await envoy.setup()

    if envoy.firmware >= AwesomeVersion("7.0.0"):
        username = os.environ.get("ENVOY_USERNAME")
        password = os.environ.get("ENVOY_PASSWORD")
        token = os.environ.get("ENVOY_TOKEN")
        await envoy.authenticate(username=username, password=password, token=token)

    if envoy.auth is not None:
        print(envoy.auth.token)

    # Test https://enphase.com/download/iq-gateway-access-using-local-apis-or-local-ui-token-based-authentication-tech-brief endpoints

    prod: httpx.Response = await envoy.request("/production.json")
    print(prod.text)

    meter_details: httpx.Response = await envoy.request("/ivp/meters")
    print(meter_details.text)

    meter_readings: httpx.Response = await envoy.request("/ivp/meters/readings")
    print(meter_readings.text)

    inverters: httpx.Response = await envoy.request("/api/v1/production/inverters")
    print(inverters.text)

    meters_live: httpx.Response = await envoy.request("/ivp/livedata/status")
    print(meters_live.text)

    load_consumption: httpx.Response = await envoy.request(
        "/ivp/meters/reports/consumption"
    )
    print(load_consumption.text)


asyncio.run(main())
