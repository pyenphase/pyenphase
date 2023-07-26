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

    end_points = [
        "/ivp/livedata/status",
        "/production.json",
        "/ivp/meters",
        "/ivp/meters/readings",
        "/api/v1/production/inverters",
        "/ivp/livedata/status" "/ivp/meters/reports/consumption",
    ]

    for end_point in end_points:
        try:
            json_dict = await envoy.request("/ivp/livedata/status")
        except Exception as e:
            print(e)
            continue
        print((end_point, "=" * 80))
        pprint(json_dict)
        print((end_point, "=" * 80))


asyncio.run(main())
