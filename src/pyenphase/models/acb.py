"""Model for the ACB Battery."""

# Data Source: URL_ENSEMBLE_SECCTRL (primary) & URL_PRODUCTION_JSON
# Per-device: URL_ENSEMBLE_INVENTORY (type "ACB") + URL_PRODUCTION_INVERTERS (devType=11)

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .inverter import EnvoyInverter


@dataclass(slots=True)
class EnvoyBatteryAggregate:
    """Model for combined Encharge and ACB batteries aggregate data."""

    #: Sum of Encharge aggregate and ACB aggregate current battery energy content
    #: from ENC_agg_avail_energy and ACB_agg_energy.
    available_energy: int
    #: Combined State of charge for all Encharge and ACB batteries from agg_soc.
    state_of_charge: int
    #: Combined total maximum capacity for all Encharge and ACB batteries from Max_energy.
    max_available_capacity: int

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> EnvoyBatteryAggregate:
        """
        Fill Aggregated battery data from Envoy data format.

        Source data parts of URL_ENSEMBLE_SECCTRL
            .. code-block:: json

                {

                    "agg_soc": 39,
                    "Max_energy": 7220,

                    "ENC_agg_avail_energy": 350,

                    "Enc_max_available_capacity": 3500,
                    "ACB_agg_soc": 25,
                    "ACB_agg_energy": 930,

                }

        Args:
            data (dict[str, Any]): JSON returned from URL_ENSEMBLE_SECCTRL

        Returns:
            EnvoyBatteryAggregate: Aggregated Battery data for all Encharge and ACB batteries

        """
        return cls(
            available_energy=data["ENC_agg_avail_energy"] + data["ACB_agg_energy"],
            max_available_capacity=data["Max_energy"],
            state_of_charge=data["agg_soc"],
        )


@dataclass(slots=True)
class EnvoyACBPower:
    """Model for the ACB battery power."""

    #: Current discharge/charge power for ACB batteries from wNow.
    power: int
    #: Current available capacity in Wh for ACB batteries from whNow
    charge_wh: int
    #: Current SOC in percentage for ACB batteries from percentFull
    state_of_charge: int
    #: Current state for ACB batteries (discharging/idle/charging) from state
    state: str
    #: Number of reported ACB batteries from activeCount
    batteries: int

    @classmethod
    def from_production(
        cls, data: dict[str, Any], acb_segment: int = 0
    ) -> EnvoyACBPower:
        """
        Fill ACB battery power data from Envoy data format.

        Source data URL_PRODUCTION_JSON["storage"]
            .. code-block:: json

                "storage": [{
                    "type": "acb",
                    "activeCount": 3,
                    "readingTime": 1731943992,
                    "wNow": 260,
                    "whNow": 930,
                    "state": "discharging",
                    "percentFull": 25
                }]


        Args:
            data (dict[str, Any]): JSON returned from URL_PRODUCTION_JSON
            acb_segment (int): segment to process from storage list, default is 0

        Returns:
            EnvoyACBPower: ACB battery current power out/in and energy content and status

        """
        storage_data = data["storage"][acb_segment]
        return cls(
            power=storage_data["wNow"],
            charge_wh=storage_data["whNow"],
            state_of_charge=storage_data["percentFull"],
            state=storage_data["state"],
            batteries=storage_data["activeCount"],
        )


@dataclass(slots=True)
class EnvoyACB:
    """Model for a single ACB (AC Battery) device from /ivp/ensemble/inventory."""

    #: Device serial number
    serial_num: str
    #: Device part number
    part_num: str
    #: Whether sleep mode is enabled on this device
    sleep_enabled: bool
    #: Current charge status: charging, discharging, or idle
    charge_status: str
    #: Raw device status flags from inventory (e.g. envoy.global.ok,
    #: envoy.cond_flags.pcu_ctrl.sleep-mode)
    device_status: list[str]
    #: Current state of charge as a percentage (0-100)
    percent_full: int
    #: Maximum cell temperature in degrees Celsius
    max_cell_temp: int | None
    #: Whether this device is currently communicating with the Envoy
    communicating: bool
    #: Whether this device is currently operating
    operating: bool
    #: Whether this device is currently producing power
    producing: bool
    #: Minimum SOC threshold for sleep mode activation
    sleep_min_soc: int | None
    #: Maximum SOC threshold for sleep mode deactivation
    sleep_max_soc: int | None
    #: Last report timestamp, from /api/v1/production/inverters (devType=11)
    last_report_date: int | None
    #: Current power output in watts, from /api/v1/production/inverters (devType=11)
    last_report_watts: int | None
    #: Maximum reported power in watts, from /api/v1/production/inverters (devType=11)
    max_report_watts: int | None

    @property
    def sleep_state(self) -> str:
        """
        Return human-readable sleep state based on flags and requested state.

        Values:
            - awake
            - going_to_sleep
            - asleep
            - waking
        """
        has_sleep_flag = "envoy.cond_flags.pcu_ctrl.sleep-mode" in self.device_status
        if self.sleep_enabled and has_sleep_flag:
            return "asleep"
        if self.sleep_enabled and not has_sleep_flag:
            return "going_to_sleep"
        if (not self.sleep_enabled) and has_sleep_flag:
            return "waking"
        return "awake"

    @classmethod
    def from_api(
        cls,
        data: dict[str, Any],
        inverter: EnvoyInverter | None = None,
    ) -> EnvoyACB:
        """
        Fill per-device ACB data from inventory and inverter report.

        Source data from URL_ENSEMBLE_INVENTORY type "ACB" device entry and
        (optionally) the matching entry from URL_PRODUCTION_INVERTERS.

            .. code-block:: json

                {
                    "part_num": "800-00930-r03",
                    "serial_num": "121917000087",
                    "sleep_enabled": false,
                    "percentFull": 0,
                    "maxCellTemp": 18,
                    "communicating": true,
                    "operating": true,
                    "producing": true,
                    "sleep_min_soc": 25,
                    "sleep_max_soc": 30,
                    "charge_status": "discharging"
                }

        Args:
            data (dict[str, Any]): Device entry from URL_ENSEMBLE_INVENTORY type "ACB"
            inverter (EnvoyInverter | None): Matching inverter record from
                URL_PRODUCTION_INVERTERS (devType=11), or None if not available.

        Returns:
            EnvoyACB: Per-device ACB battery data

        """
        return cls(
            serial_num=data["serial_num"],
            part_num=data.get("part_num", ""),
            sleep_enabled=data.get("sleep_enabled", False),
            charge_status=data.get("charge_status", "unknown"),
            device_status=[str(x) for x in data.get("device_status", [])],
            percent_full=data.get("percentFull", 0),
            max_cell_temp=data.get("maxCellTemp"),
            communicating=data.get("communicating", False),
            operating=data.get("operating", False),
            producing=data.get("producing", False),
            sleep_min_soc=data.get("sleep_min_soc"),
            sleep_max_soc=data.get("sleep_max_soc"),
            last_report_date=inverter.last_report_date if inverter else None,
            last_report_watts=inverter.last_report_watts if inverter else None,
            max_report_watts=inverter.max_report_watts if inverter else None,
        )
