import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from pyenphase import Envoy
from pyenphase.models.acb import EnvoyACB

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


async def read_envoy_json(envoy: Envoy, endpoint: str) -> Any | None:
    """Read arbitrary Envoy endpoint as JSON and return None on failures."""
    try:
        async with await envoy.request(endpoint) as response:
            payload = await response.read()
            return json.loads(payload.decode("utf-8"))
    except Exception as err:
        print(f"Failed reading {endpoint}: {err}")
        return None


def parse_int(value: Any) -> int | None:
    """Best-effort conversion to int; return None when conversion fails."""
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def format_timestamp(ts: int | None) -> str | None:
    """Format unix timestamp as local human-readable datetime."""
    if ts is None:
        return None
    return datetime.fromtimestamp(ts).isoformat(sep=" ", timespec="seconds")


async def main() -> None:
    private_defaults = load_private_defaults()

    host = os.getenv("ENVOY_HOST", private_defaults.get("host", "envoy.local"))
    username = os.getenv("ENVOY_USERNAME", private_defaults.get("username", ""))
    password = os.getenv("ENVOY_PASSWORD", private_defaults.get("password", ""))
    token = os.getenv("ENVOY_TOKEN")

    envoy = Envoy(host)

    try:
        await envoy.setup()
        print(
            f"Connected to {envoy.host} | firmware={envoy.firmware} | sn={envoy.serial_number}"
        )

        await envoy.authenticate(username=username, password=password, token=token)
        data = await envoy.update()

        production = data.system_production
        if production is None:
            print(
                "Authenticated, but no system production data is available on this Envoy."
            )
            return

        print("Live data:")
        print(f"  Watts now: {production.watts_now}")
        print(f"  Today Wh:  {production.watt_hours_today}")
        print(f"  Total Wh:  {production.watt_hours_lifetime}")

        # Aggregate ACB data from production.json storage[type=acb]
        acb_power = data.acb_power
        if acb_power is None:
            print("\nACB aggregate: unavailable")
        else:
            print("\nACB aggregate:")
            print(f"  Batteries:   {acb_power.batteries}")
            print(f"  Power (W):   {acb_power.power}")
            print(f"  Charge (Wh): {acb_power.charge_wh}")
            print(f"  SOC (%):     {acb_power.state_of_charge}")
            print(f"  State:       {acb_power.state}")

        # Per-device ACB inventory from /ivp/ensemble/inventory (type == ACB),
        # with watts cross-referenced from /api/v1/production/inverters (devType=11).
        acb_inventory = envoy.acb_inventory or {}
        print(f"\nACB devices found: {len(acb_inventory)}")
        for serial, acb in acb_inventory.items():
            print(f"  - {serial}")
            print(f"    part_num:          {acb.part_num}")
            print(f"    charge_status:     {acb.charge_status}")
            print(f"    sleep_enabled:     {acb.sleep_enabled}")
            if acb.last_report_date is not None:
                age = max(0, int(time.time()) - acb.last_report_date)
                print(f"    last_report_date:  {acb.last_report_date}")
                print(
                    f"    last_report_at:    {format_timestamp(acb.last_report_date)}"
                )
                print(f"    report_age_sec:    {age}")
            print(f"    percent_full:      {acb.percent_full}")
            print(f"    max_cell_temp:     {acb.max_cell_temp}")
            print(f"    communicating:     {acb.communicating}")
            print(f"    operating:         {acb.operating}")
            print(f"    producing:         {acb.producing}")
            print(f"    sleep_min_soc:     {acb.sleep_min_soc}")
            print(f"    sleep_max_soc:     {acb.sleep_max_soc}")
            print(f"    last_report_watts: {acb.last_report_watts}")
            print(f"    max_report_watts:  {acb.max_report_watts}")

        # On some systems /ivp/ensemble/inventory may be empty while
        # /inventory.json?deleted=1 still contains ACB devices.
        if not acb_inventory:
            inventory_json = await read_envoy_json(envoy, "/inventory.json?deleted=1")
            acb_config_json = await read_envoy_json(envoy, "/admin/lib/acb_config")

            sleep_requests_by_serial: dict[str, dict[str, Any]] = {}
            if isinstance(acb_config_json, dict):
                for item in acb_config_json.get("acb_sleep", []):
                    serial = str(item.get("serial_num", ""))
                    if serial:
                        sleep_requests_by_serial[serial] = item

            fallback_devices: list[dict[str, Any]] = []
            if isinstance(inventory_json, list):
                for group in inventory_json:
                    if group.get("type") == "ACB":
                        fallback_devices.extend(group.get("devices", []))

            print(
                f"\nACB fallback devices from /inventory.json?deleted=1: {len(fallback_devices)}"
            )
            for device in fallback_devices:
                serial = str(device.get("serial_num", "unknown"))
                sleep_enabled = bool(device.get("sleep_enabled", False))
                device_status = [str(x) for x in device.get("device_status", [])]
                inferred_state = EnvoyACB.from_api(device).sleep_state
                configured = sleep_requests_by_serial.get(serial)
                last_rpt_date = device.get("last_rpt_date")
                last_rpt_ts = parse_int(last_rpt_date)
                report_age_sec = (
                    max(0, int(time.time()) - last_rpt_ts)
                    if last_rpt_ts is not None
                    else None
                )

                print(f"  - {serial}")
                print(f"    inferred_state:    {inferred_state}")
                print(f"    sleep_enabled:     {sleep_enabled}")
                print(f"    last_report_date:  {last_rpt_date}")
                print(f"    last_report_at:    {format_timestamp(last_rpt_ts)}")
                print(f"    report_age_sec:    {report_age_sec}")
                print(f"    device_status:     {device_status}")
                print(f"    charge_status:     {device.get('charge_status')}")
                print(f"    percent_full:      {device.get('percentFull')}")
                print(f"    max_cell_temp:     {device.get('maxCellTemp')}")
                print(f"    sleep_min_soc:     {device.get('sleep_min_soc')}")
                print(f"    sleep_max_soc:     {device.get('sleep_max_soc')}")
                if configured:
                    print(
                        "    requested_sleep:   "
                        f"{configured.get('sleep_min_soc')}..{configured.get('sleep_max_soc')}"
                    )
                else:
                    print("    requested_sleep:   none")

        # Optional write example (disabled by default to avoid accidental config writes).
        # Set ENVOY_DEMO_SET_ACB_SLEEP=true to run this call.
        if os.getenv("ENVOY_DEMO_SET_ACB_SLEEP", "").lower() in {"1", "true", "yes"}:
            if not acb_inventory:
                print("\nSkipping set_acb_sleep: no ACB devices available.")
            else:
                first_serial = next(iter(acb_inventory))
                payload = [
                    {
                        "serial_num": first_serial,
                        "sleep_min_soc": 5,
                        "sleep_max_soc": 10,
                    }
                ]
                result = await envoy.set_acb_sleep(payload)
                print("\nset_acb_sleep result:")
                print(result)
    finally:
        await envoy.close()


if __name__ == "__main__":
    asyncio.run(main())
