import asyncio
import logging
import os
from pprint import pprint
import json

from pyenphase.envoy import Envoy

logging.basicConfig(level=logging.DEBUG)


async def main() -> None:
    envoy = Envoy(os.environ.get("ENVOY_HOST", "envoy.local"))

    await envoy.setup()

    username = os.environ.get("ENVOY_USERNAME")
    password = os.environ.get("ENVOY_PASSWORD")
    token = os.environ.get("ENVOY_TOKEN")

    await envoy.authenticate(username=username, password=password, token=token)

    # Test https://enphase.com/download/iq-gateway-access-using-local-apis-or-local-ui-token-based-authentication-tech-brief endpoints

    # print(await envoy.update())

    try:
        os.mkdir("enphase")
    except FileExistsError:
        pass

    end_points = [
        "/ivp/livedata/status",
        "/api/v1/production",
        "/api/v1/production/inverters",
        "/production.json",
        "/production",
        "/ivp/meters",
        "/ivp/meters/readings",
        "/ivp/meters/reports/consumption",
        "/ivp/ensemble/inventory",
        "/ivp/ensemble/dry_contacts",
        "/ivp/ss/dry_contact_settings",
    ]

    for end_point in end_points:
        print((end_point, "=" * 80))
        try:
            json_dict = await envoy.request(end_point)
        except Exception as e:
            print(e)
            continue
        pprint(json_dict)
        file_name = end_point[1:].replace("/", "_")
        with open(f"enphase/{file_name}.txt") as fixture_file:
            fixture_file.write(json.dumps(json_dict))
        print((end_point, "=" * 80))


asyncio.run(main())
