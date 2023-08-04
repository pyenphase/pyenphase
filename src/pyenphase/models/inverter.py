"""Model for an Enphase microinverter."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EnvoyInverter:
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

    def __repr__(self) -> str:
        """Return a representation of the inverter."""
        return (
            f"<EnvoyInverter: {self.serial_number} "
            f"last_report_data={self.last_report_date} "
            f"last_report_watts={self.last_report_watts} "
            f"max_report_watts={self.max_report_watts}"
            ">"
        )
