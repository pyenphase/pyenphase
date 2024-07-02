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

    @classmethod
    def from_v1_api(cls, data: dict[str, Any]) -> EnvoyInverter:
        """Initialize from the V1 API."""
        return cls(
            serial_number=data["serialNumber"],
            last_report_date=data["lastReportDate"],
            last_report_watts=data["lastReportWatts"],
            max_report_watts=data["maxReportWatts"],
        )
