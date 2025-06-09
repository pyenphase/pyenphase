"""Model for an Enphase microinverter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EnvoyInverter:
    """Model for an Enphase microinverter."""

    serial_number: str
    last_report_date: int
    last_report_watts: int
    max_report_watts: int
    dc_voltage: float | None = None
    dc_current: float | None = None
    ac_voltage: float | None = None
    ac_current: float | None = None
    ac_frequency: float | None = None
    temperature: float | None = None
    lifetime_energy: int | None = None
    energy_produced: float | None = None
    energy_today: int | None = None
    last_report_duration: int | None = None

    @classmethod
    def from_v1_api(cls, data: dict[str, Any]) -> EnvoyInverter:
        """Initialize from the V1 API."""
        return cls(
            serial_number=data["serialNumber"],
            last_report_date=data["lastReportDate"],
            last_report_watts=data["lastReportWatts"],
            max_report_watts=data["maxReportWatts"],
        )

    @classmethod
    def from_device_data(cls, data: dict[str, Any]) -> EnvoyInverter:
        """Initialize from device data."""

        def safe_convert_milli(value: float | None) -> float | None:
            return value / 1000.0 if value is not None else None

        # if these don't exist they raise KeyError to not use this model but use from_v1_api
        channel = data["channels"][0]
        last_reading = channel["lastReading"]

        # these four are minimal data set, if one fails keyerror will raise
        serial_number = data["sn"]
        last_report_date = last_reading["endDate"]
        last_report_watts = channel["watts"]["now"]
        max_report_watts = channel["watts"]["max"]

        # get data to avoid divide errors if None
        duration = last_reading.get("duration")
        period_joules_produced = last_reading.get("joulesProduced")
        lifetime = channel.get("lifetime")
        lifetime_joulesProduced = lifetime.get("joulesProduced") if lifetime else None
        watthours = channel.get("wattHours")

        return cls(
            serial_number=serial_number,
            last_report_date=last_report_date,
            last_report_watts=last_report_watts,
            max_report_watts=max_report_watts,
            # next ones may return none as they didn't exist before in the model
            dc_voltage=safe_convert_milli(last_reading.get("dcVoltageINmV")),
            dc_current=safe_convert_milli(last_reading.get("dcCurrentINmA")),
            ac_voltage=safe_convert_milli(last_reading.get("acVoltageINmV")),
            ac_current=safe_convert_milli(last_reading.get("acCurrentInmA")),
            ac_frequency=safe_convert_milli(last_reading.get("acFrequencyINmHz")),
            temperature=last_reading.get("channelTemp"),
            lifetime_energy=round(lifetime_joulesProduced / 3600.0)
            if lifetime_joulesProduced is not None
            else None,
            energy_produced=round(period_joules_produced / duration / 3.6, 3)
            if period_joules_produced is not None and duration is not None
            else None,
            energy_today=watthours.get("today") if watthours else None,
            last_report_duration=duration,
        )
