"""
Create test fixture file set for pyenphase by scanning known endpoints on Envoy.

execute python fixture_collector.py --help for directons

Copy this file to the Home Assistant config folder. Open a terminal on your HA system
Navigate to the config folder and execute python fixture_collector.py

Alternatively copy and execute this file to a system with pyenphase installed and
network connectivity to your Home Assistant config folder and the Envoy.
"""

import argparse
import asyncio
import getpass
import json
import logging
import os
import zipfile

from pyenphase.envoy import DEFAULT_HEADERS, Envoy
from pyenphase.exceptions import (
    EnvoyAuthenticationRequired,
    EnvoyFirmwareFatalCheckError,
)

# logging.basicConfig(level=logging.WARNING)

_LOGGER = logging.getLogger(__name__)


async def main(
    envoy_address: str | None,
    username: str | None,
    password: str | None,
    token: str | None,
    verbose: bool = False,
    label: str = "",
    clean: bool = False,
) -> None:
    envoy = Envoy(os.environ.get("ENVOY_HOST", envoy_address or "envoy.local"))
    try:
        await envoy.setup()
    except EnvoyFirmwareFatalCheckError as err:
        print(f"Could not connect to Envoy: {err.status_code} {err.status}")
        return None

    try:
        await envoy.authenticate(username=username, password=password, token=token)
    except EnvoyAuthenticationRequired:
        print("Could not athenticate with Envoy")
        return None

    target_dir = f"enphase-{envoy.firmware}{label}"
    try:
        os.mkdir(target_dir)
    except FileExistsError:
        pass

    end_points = [
        "/info",
        "/api/v1/production",
        "/api/v1/production/inverters",
        "/production.json",
        "/production.json?details=1",
        "/production",
        "/ivp/ensemble/power",
        "/ivp/ensemble/inventory",
        "/ivp/ensemble/dry_contacts",
        "/ivp/ensemble/status",
        "/ivp/ensemble/secctrl",
        "/ivp/ss/dry_contact_settings",
        "/admin/lib/tariff",
        "/ivp/ss/gen_config",
        "/ivp/ss/gen_schedule",
        "/ivp/sc/pvlimit",
        "/ivp/ss/pel_settings",
        "/ivp/ensemble/generator",
        "/ivp/meters",
        "/ivp/meters/readings",
        "/ivp/pdm/device_data",
    ]

    assert envoy.auth  # nosec

    for end_point in end_points:
        url = envoy.auth.get_endpoint_url(end_point)
        if verbose:
            print(end_point)
        try:
            response = await envoy._client.get(
                url,
                headers={**DEFAULT_HEADERS, **envoy.auth.headers},
                cookies=envoy.auth.cookies,
                follow_redirects=True,
                auth=envoy.auth.auth,
                timeout=envoy._timeout,
            )
        except Exception as ex:
            _LOGGER.debug("Error getting %s", end_point, exc_info=ex)
            continue
        file_name = end_point[1:].replace("/", "_").replace("?", "_").replace("=", "_")
        with open(os.path.join(target_dir, file_name), "w") as fixture_file:
            fixture_file.write(response.text)

        with open(
            os.path.join(target_dir, f"{file_name}_log.json"), "w"
        ) as metadata_file:
            metadata_file.write(
                json.dumps(
                    {
                        "headers": dict(response.headers.items()),
                        "code": response.status_code,
                    }
                )
            )

    if not clean or verbose:
        print(f"Fixtures written to {target_dir}")

    zip_file_name = f"{target_dir}.zip"
    with zipfile.ZipFile(zip_file_name, "w") as zip_file:
        for file_name in os.listdir(target_dir):
            zip_file.write(os.path.join(target_dir, file_name), file_name)
            if clean:
                os.remove(os.path.join(target_dir, file_name))

    print(f"Zip file written to {zip_file_name}")

    if clean:
        try:
            os.rmdir(target_dir)
            if verbose:
                print(f"Removed {target_dir}")
        except OSError as err:
            print(f"Could not clean folder: {err.strerror}")
        except FileNotFoundError:
            pass


def _read_ha_config(file_path: str) -> dict[str, list[str | None]]:
    result: dict[str, list[str | None]] = {}
    try:
        with open(file_path) as fp:
            content = json.load(fp)
    except (FileNotFoundError, ValueError):
        return result

    if content:
        for entry in content["data"]["entries"]:
            if entry["domain"] != "enphase_envoy" or entry["source"] == "ignore":
                continue
            data = entry["data"]
            unique_id = entry["unique_id"]
            result[unique_id] = [
                data["host"],
                data["username"],
                data["password"],
                data["token"],
            ]

    return result


if __name__ == "__main__":
    description = (
        "Scan Enphase Envoy for endpoint list usable for pyenphase test fixtures. \
        Creates output folder envoy_<firmware>[label] with results of scan.\
        Zips content of created folder into envoy_<firmware>[label].zip.\
        "
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-d", "--debug", help="Enable debug logging", action="store_true"
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "-c",
        "--clean",
        help="Remove created folder, but keep zip file",
        action="store_true",
    )
    parser.add_argument(
        "-l", "--label", help="Label to append to output folder and zip file names"
    )
    parser.add_argument(
        "-r",
        "--readhaconfig",
        const=".",
        nargs="?",
        dest="ha_config_folder",
        help="Read envoyname, username, password and token from HA config folder.\
            Use -r path_to_ha_config_folder. Default is current folder.\
                Overrides any specified username, password and token.",
    )

    parser.add_argument(
        "-e",
        "--envoyname",
        default="envoy.local",
        help="Envoy Name or IP address. IP is preferred, default is envoy.local",
    )
    parser.add_argument(
        "-u", "--username", help="Username (for Envoy or for Enphase token website)"
    )
    parser.add_argument(
        "-p", "--password", help="Password (blank or for Enphase token website)"
    )
    parser.add_argument(
        "-t", "--token", help="Enphase owner token or @path_to_file to read from file"
    )

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    host = args.envoyname
    username: str | None = args.username
    password: str | None = args.password
    read_ha_config: str = args.ha_config_folder
    verbose: bool = args.verbose

    config_entries: dict[str, list[str | None]] = {}
    target_ha_file: str = ""

    if args.ha_config_folder:
        target_ha_file = os.path.join(read_ha_config, ".storage/core.config_entries")
        config_entries = _read_ha_config(target_ha_file)
    else:
        username = args.username
        password = args.password
        token = args.token
        if not username:
            username = os.environ.get("ENVOY_USERNAME", input("Enter the Username: "))
        if not password:
            password = os.environ.get(
                "ENVOY_PASSWORD", getpass.getpass("Enter the Password: ")
            )
        if not token:
            token = os.environ.get("ENVOY_TOKEN", getpass.getpass("Enter the token: "))
        if token and token[0] == "@":
            try:
                with open(token[1:]) as f:
                    token = f.read()
            except FileExistsError:
                token = None
        config_entries.update({"unknown": [host, username, password, token]})

    for sn, configs in config_entries.items():
        host, username, password, token = configs
        if verbose:
            print(f"Using {host} sn: {sn}, {target_ha_file}")

        asyncio.run(
            main(
                envoy_address=host,
                username=username,
                password=password,
                token=token,
                verbose=verbose,
                label=args.label or "",
                clean=args.clean,
            )
        )
