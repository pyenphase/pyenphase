"""Model for the Envoy's production data."""

# Data Source: URL_PRODUCTION
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

_LOGGER = logging.getLogger(__name__)


def find_dict_by_key(
    all_production: list[dict[str, Any]], key: str, required: bool = True
) -> dict[str, Any]:
    """
    Find a dict by key presence in list of dicts.

    :param all_production: production segment of /production json
    :param key: key to find in production segment list of dicts
    :param required: if True key must be present
    :raises valueError: if key is required to be present and not found
    :returns: dict with key if found, empty dict if not found and not required, raises otherwise
    """
    for production in all_production:
        if production.get("type") == key:
            return production

    # as of 8.3.5422 on Envoy non-metered, /api/v1/production returns all zeros
    # and we need to fallback to type=inverters of production section in /production.
    # The non metered Envoy /production has no type=eim in the production section
    # and this test would raise. If not metered return empty dict by setting
    # required to False
    if not required:
        return {}

    raise ValueError(f"{key} is missing")


@dataclass(slots=True)
class EnvoySystemProduction:
    """Model for the Envoy's production data."""

    watt_hours_lifetime: int  #: Lifetime Energy produced
    watt_hours_last_7_days: (
        int  #: Energy produced in previous 7 days (not including today)
    )
    watt_hours_today: int  #: Energy produced since start of day
    watts_now: int  #: Current Power production

    @classmethod
    def from_v1_api(cls, data: dict[str, Any]) -> EnvoySystemProduction:
        """
        Initialize from the V1 API.

        :param data:  JSON reply from api/v1/production endpoint
        :return: Lifetime, last seven days, todays energy and current power for solar production
        """
        return cls(
            watt_hours_lifetime=data["wattHoursLifetime"],
            watt_hours_last_7_days=data["wattHoursSevenDays"],
            watt_hours_today=data["wattHoursToday"],
            watts_now=data["wattsNow"],
        )

    @classmethod
    def from_production(
        cls, data: dict[str, Any], has_production_ct: bool = True
    ) -> EnvoySystemProduction | None:
        """
        Initialize from the production API.

        :param data: JSON reply from /production endpoint
        :param has_production_ct: signal Envoy has an enabled PRODUCTION CT;
            when True do not fall back to the inverter data section and
            return None if activeCount is zero
        :return: Lifetime, last seven days, todays energy and current power for solar production or None if the Envoy has an enabled production CT and activeCount is zero
        """
        all_production = data["production"]

        # if metered envoy with production CT active, eim key must be present
        # for non-metered envoy not
        eim = find_dict_by_key(all_production, "eim", has_production_ct)
        # inverters key must be present for both metered and not metered
        inverters = find_dict_by_key(all_production, "inverters", True)

        # As of fw 5.3.5528 (and maybe earlier) metered envoy with CT intermittently
        # report bogus data in /production type=eim, recognizable by activeCount: 0.
        # A silent fallback from production to inverters data of /production happens
        # because activecount (and potentially other values as well) being 0. The
        # inverter segment data for this and others firmwares has different values
        # as the eim segment and would result in step changes in the value.
        #
        # Don't fallback to the inverters section for metered with production ct.
        # Return None instead so HA data will keep last value or show as unavailable.
        # Caller can tell through has_production_ct param if envoy is metered with
        # active production CT or not.
        if has_production_ct and not eim["activeCount"]:
            _LOGGER.debug(
                "Envoy with Production CT but activeCount is zero, returning None for production data"
            )
            return None

        # This is backwards compatible with envoy_reader
        # envoy metered without configured CT has whLifetime and wNow in inverters
        # whLastSevenDays and whToday are incorrect for both so either can be used
        #
        # 8.3.5422 on Envoy non-metered /api/v1/production returns all zeros and
        # needs to use inverters section while type=eim is not present in its
        # /production endpoint. fallback to inverters if no eim present at all
        now_source = eim if eim and eim["activeCount"] else inverters

        return cls(
            watt_hours_lifetime=round(now_source["whLifetime"]),
            watt_hours_last_7_days=round(
                eim.get("whLastSevenDays") or inverters.get("whLastSevenDays") or 0
            ),
            watt_hours_today=round(eim.get("whToday") or inverters.get("whToday") or 0),
            watts_now=round(now_source["wNow"]),
        )

    @classmethod
    def from_production_phase(
        cls, data: dict[str, Any], phase: int, has_production_ct: bool = True
    ) -> EnvoySystemProduction | None:
        """
        Initialize from the production API phase data.

        :param data: JSON reply from /production endpoint
        :param phase: Index (0-2) in [lines] segment for which to return data
        :param has_production_ct: signal Envoy has an enabled PRODUCTION CT;
            when True do not fall back to the inverter data section and
            return None if activeCount is zero
        :return: Lifetime, last seven days, todays energy and current power for production phase
            or None if activeCount is zero, lines or phases are missing
        """
        all_production = data["production"]
        eim = find_dict_by_key(all_production, "eim", has_production_ct)

        # if {production[type=eim]{Lines[]} or phase is missing return None
        # 8.3.5422 on Envoy non-metered /api/v1/production returns all zeros and
        # needs to use inverters section while type=eim is not present in its
        # /production endpoint. return none if no eim present at all
        if (
            not eim
            or (has_production_ct and not eim["activeCount"])
            or not (phases := eim.get("lines"))
            or phase >= len(phases)
        ):
            return None

        phase_data = phases[phase]
        return cls(
            watt_hours_lifetime=round(phase_data.get("whLifetime") or 0),
            watt_hours_last_7_days=round(phase_data.get("whLastSevenDays") or 0),
            watt_hours_today=round(phase_data.get("whToday") or 0),
            watts_now=round(phase_data.get("wNow") or 0),
        )
