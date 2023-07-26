import asyncio
import logging
import os
from pprint import pprint

import httpx

from pyenphase.envoy import Envoy

logging.basicConfig(level=logging.DEBUG)


async def main() -> None:
    envoy = Envoy("envoy.local")

    await envoy.setup()

    username = os.environ.get("ENVOY_USERNAME")
    password = os.environ.get("ENVOY_PASSWORD")
    token = os.environ.get("ENVOY_TOKEN")

    await envoy.authenticate(username=username, password=password, token=token)

    # Test https://enphase.com/download/iq-gateway-access-using-local-apis-or-local-ui-token-based-authentication-tech-brief endpoints

    live: httpx.Response = await envoy.request("/ivp/livedata/status")
    print(("LIVE", "=" * 80))
    pprint(live)

    prod: httpx.Response = await envoy.request("/production.json")
    print("PRODUCTION", "=" * 80)
    pprint(prod)

    meter_details: httpx.Response = await envoy.request("/ivp/meters")
    print("=" * 80)
    pprint(meter_details)

    meter_readings: httpx.Response = await envoy.request("/ivp/meters/readings")
    print("=" * 80)
    pprint(meter_readings)

    inverters: httpx.Response = await envoy.request("/api/v1/production/inverters")
    print("=" * 80)
    pprint(inverters)

    meters_live: httpx.Response = await envoy.request("/ivp/livedata/status")
    print("=" * 80)
    pprint(meters_live)

    load_consumption: httpx.Response = await envoy.request(
        "/ivp/meters/reports/consumption"
    )
    print("=" * 80)
    pprint(load_consumption)


asyncio.run(main())
