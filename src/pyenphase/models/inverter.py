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
    lifetime_energy: float | None = None
    energy_produced: float | None = None
    energy_today: float | None = None

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
        channel = data["channels"][0]
        last_reading = channel["lastReading"]
        return cls(
            serial_number=data["sn"],
            last_report_date=last_reading["endDate"],
            last_report_watts=channel["watts"]["now"],
            max_report_watts=channel["watts"]["max"],
            dc_voltage=last_reading["dcVoltageINmV"] / 1000.0,
            dc_current=last_reading["dcCurrentINmA"] / 1000.0,
            ac_voltage=last_reading["acVoltageINmV"] / 1000.0,
            ac_current=last_reading["acCurrentInmA"] / 1000.0,
            ac_frequency=last_reading["acFrequencyINmHz"] / 1000.0,
            temperature=last_reading["channelTemp"],
            lifetime_energy=channel["lifetime"]["joulesProduced"] / 3600.0,
            energy_produced=last_reading["joulesProduced"]
            / last_reading["duration"]
            / 3600.0,
            energy_today=channel["wattHours"]["today"],
        )
