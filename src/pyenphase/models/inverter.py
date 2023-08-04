"""Model for an Enphase microinverter."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EnvoyInverter:
    """Model for an Enphase microinverter."""

    serial_number: str
    last_report_date: int
    last_report_watts: int
    max_report_watts: int

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize."""
        self.serial_number = data["serialNumber"]
        self.last_report_date = data["lastReportDate"]
        self.last_report_watts = data["lastReportWatts"]
        self.max_report_watts = data["maxReportWatts"]
