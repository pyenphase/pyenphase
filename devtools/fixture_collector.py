import asyncio
import json
import logging
import os
import zipfile

from pyenphase.envoy import Envoy

logging.basicConfig(level=logging.DEBUG)


async def main() -> None:
    envoy = Envoy(os.environ.get("ENVOY_HOST", "envoy.local"))

    await envoy.setup()

    username = os.environ.get("ENVOY_USERNAME")
    password = os.environ.get("ENVOY_PASSWORD")
    token = os.environ.get("ENVOY_TOKEN")

    await envoy.authenticate(username=username, password=password, token=token)

    target_dir = f"enphase-{envoy.firmware}"
    try:
        os.mkdir(target_dir)
    except FileExistsError:
        pass

    end_points = [
        "/info",
        "/api/v1/production",
        "/api/v1/production/inverters",
        "/production.json",
        "/production",
        "/ivp/ensemble/power",
        "/ivp/ensemble/inventory",
        "/ivp/ensemble/dry_contacts",
        "/ivp/ss/dry_contact_settings",
    ]

    for end_point in end_points:
        try:
            json_dict = await envoy.request(end_point)
        except Exception:
            continue  # nosec
        file_name = end_point[1:].replace("/", "_")
        with open(os.path.join(target_dir, file_name), "w") as fixture_file:
            fixture_file.write(json.dumps(json_dict))

    print(f"Fixtures written to {target_dir}")

    zip_file_name = f"{target_dir}.zip"
    with zipfile.ZipFile(zip_file_name, "w") as zip_file:
        for file_name in os.listdir(target_dir):
            zip_file.write(os.path.join(target_dir, file_name), file_name)

    print(f"Zip file written to {zip_file_name}")


asyncio.run(main())
