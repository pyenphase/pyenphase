import asyncio
import json
import logging
import os

from pyenphase.envoy import Envoy

logging.basicConfig(level=logging.DEBUG)


async def main() -> None:
    envoy = Envoy(os.environ.get("ENVOY_HOST", "envoy.local"))

    await envoy.setup()

    username = os.environ.get("ENVOY_USERNAME")
    password = os.environ.get("ENVOY_PASSWORD")
    token = os.environ.get("ENVOY_TOKEN")

    await envoy.authenticate(username=username, password=password, token=token)

    try:
        os.mkdir("enphase")
    except FileExistsError:
        pass

    end_points = [
        "/info",
        "/api/v1/production",
        "/api/v1/production/inverters",
        "/production.json",
        "/production",
    ]

    for end_point in end_points:
        try:
            json_dict = await envoy.request(end_point)
        except Exception as e:
            continue
        file_name = end_point[1:].replace("/", "_")
        with open(f"enphase/{file_name}") as fixture_file:
            fixture_file.write(json.dumps(json_dict))


asyncio.run(main())
