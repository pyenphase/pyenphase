"""Model for the ACB Battery."""

# Data Source: URL_ENSEMBLE_SECCTRL (primary) & URL_PRODUCTION_JSON

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
