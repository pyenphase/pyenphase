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
        # if these don't exist they raise KeyError to not use this model but use from_v1_api
        channel = data["channels"][0]
        last_reading = channel["lastReading"]
        serial_number = data["sn"]
        last_report_date = last_reading["endDate"]
        last_report_watts = channel["watts"]["now"]
        max_report_watts = channel["watts"]["max"]

        # get data to avoid divide errors if None
        dc_voltage = last_reading.get("dcVoltageINmV")
        dc_current = last_reading.get("dcCurrentINmA")
        ac_voltage = last_reading.get("acVoltageINmV")
        ac_current = last_reading.get("acCurrentInmA")
        ac_frequency = last_reading.get("acFrequencyINmHz")
        duration = last_reading.get("duration")
        energy_produced = last_reading.get("joulesProduced")
        lifetime = channel.get("lifetime")
        joulesProduced = lifetime.get("joulesProduced") if lifetime else None
        watthours = channel.get("wattHours")
        return cls(
            serial_number=serial_number,
            last_report_date=last_report_date,
            last_report_watts=last_report_watts,
            max_report_watts=max_report_watts,
            # next ones may return none as they didn't exist before in the model
            dc_voltage=dc_voltage / 1000.0 if dc_voltage is not None else None,
            dc_current=dc_current / 1000.0 if dc_current is not None else None,
            ac_voltage=ac_voltage / 1000.0 if ac_voltage is not None else None,
            ac_current=ac_current / 1000.0 if ac_current is not None else None,
            ac_frequency=ac_frequency / 1000.0 if ac_frequency is not None else None,
            temperature=last_reading.get("channelTemp"),
            lifetime_energy=round(joulesProduced / 3600.0)
            if joulesProduced is not None
            else None,
            energy_produced=round(energy_produced / duration / 3.6, 3)
            if energy_produced is not None and duration is not None
            else None,
            energy_today=watthours.get("today") if watthours else None,
            last_report_duration=duration,
        )
