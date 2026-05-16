"""
Minimal example for sleeping and waking Enphase ACB devices.

How to use:

1. Configure credentials in one of these ways:
    - Set ENVOY_HOST, ENVOY_USERNAME, ENVOY_PASSWORD, and optionally ENVOY_TOKEN
    - Or create private_data/envoy_defaults.json with host/username/password

2. Sleep one ACB:
    python devtools/acb_sleep_example.py sleep 121917000087 --sleep-min-soc 95 --sleep-max-soc 100

3. Sleep multiple ACBs:
    python devtools/acb_sleep_example.py sleep 121917000087 122047098091 --sleep-min-soc 95 --sleep-max-soc 100

4. Wake one ACB:
    python devtools/acb_sleep_example.py wake 121917000087

5. Wake multiple ACBs:
    python devtools/acb_sleep_example.py wake 121917000087 122047098091

Notes:
- The sleep action sends PUT /admin/lib/acb_config.
- The wake action sends DELETE /admin/lib/acb_config.
- Values like 95..100 match the ACB sleep-window pattern documented from local testing.

"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from pyenphase import Envoy
from pyenphase.exceptions import EnvoyError

DEFAULTS_PATH = (
    Path(__file__).resolve().parents[1] / "private_data" / "envoy_defaults.json"
)


def load_private_defaults() -> dict[str, str]:
    if not DEFAULTS_PATH.exists():
        return {}

    with DEFAULTS_PATH.open("r", encoding="utf-8") as fp:
        data = json.load(fp)

    return {
        "host": str(data.get("host", "")),
        "username": str(data.get("username", "")),
        "password": str(data.get("password", "")),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Minimal example for sleeping or waking Enphase ACB devices."
    )
    parser.add_argument(
        "action",
        choices=["sleep", "wake"],
        help="Use 'sleep' to send PUT /admin/lib/acb_config or 'wake' to send DELETE.",
    )
    parser.add_argument(
        "serials",
        nargs="+",
        help="One or more ACB serial numbers.",
    )
    parser.add_argument(
        "--sleep-min-soc",
        type=int,
        default=95,
        help="Sleep minimum SOC for the sleep action. Default: 95",
    )
    parser.add_argument(
        "--sleep-max-soc",
        type=int,
        default=100,
        help="Sleep maximum SOC for the sleep action. Default: 100",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    private_defaults = load_private_defaults()

    host = os.getenv("ENVOY_HOST", private_defaults.get("host", "envoy.local"))
    username = os.getenv("ENVOY_USERNAME", private_defaults.get("username", ""))
    password = os.getenv("ENVOY_PASSWORD", private_defaults.get("password", ""))
    token = os.getenv("ENVOY_TOKEN")

    envoy = Envoy(host)

    try:
        await envoy.setup()
        await envoy.authenticate(username=username, password=password, token=token)
        await envoy.update()

        if args.action == "sleep":
            payload = [
                {
                    "serial_num": serial_num,
                    "sleep_min_soc": args.sleep_min_soc,
                    "sleep_max_soc": args.sleep_max_soc,
                }
                for serial_num in args.serials
            ]
            print("Sending sleep request:")
            print(payload)
            result = await envoy.set_acb_sleep(payload)
        else:
            print("Sending wake request:")
            print(args.serials)
            result = await envoy.clear_acb_sleep(args.serials)

        print("Envoy response:")
        print(result)
    finally:
        await envoy.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (ValueError, EnvoyError) as err:
        print(f"Error: {err}")
        sys.exit(1)
