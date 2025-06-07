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
        return cls(
            serial_number=data["sn"],
            last_report_date=data["channels"][0]["lastReading"]["endDate"],
            last_report_watts=data["channels"][0]["watts"]["now"],
            max_report_watts=data["channels"][0]["watts"]["max"],
            dc_voltage=data["channels"][0]["lastReading"]["dcVoltageINmV"] / 1000.0,
            dc_current=data["channels"][0]["lastReading"]["dcCurrentINmA"] / 1000.0,
            ac_voltage=data["channels"][0]["lastReading"]["acVoltageINmV"] / 1000.0,
            ac_current=data["channels"][0]["lastReading"]["acCurrentInmA"] / 1000.0,
            ac_frequency=data["channels"][0]["lastReading"]["acFrequencyINmHz"]
            / 1000.0,
            temperature=data["channels"][0]["lastReading"]["channelTemp"],
            lifetime_energy=data["channels"][0]["lifetime"]["joulesProduced"] / 3600.0,
            energy_produced=data["channels"][0]["lastReading"]["joulesProduced"]
            / data["channels"][0]["lastReading"]["duration"]
            / 3600.0,
            energy_today=data["channels"][0]["wattHours"]["today"],
        )
