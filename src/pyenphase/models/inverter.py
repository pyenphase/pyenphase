"""Model for an Enphase microinverter."""

from typing import Any


class EnvoyInverter:
    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize."""
        self._data = data

    @property
    def serial_number(self) -> str:
        """Return the serial number."""
        return self._data["serialNumber"]

    @property
    def last_report_date(self) -> int:
        """Return the timestamp when the inverter last sent a report."""
        return self._data["lastReportDate"]

    @property
    def last_report_watts(self) -> int:
        """Return the production from the last report in watts."""
        return self._data["lastReportWatts"]

    @property
    def max_report_watts(self) -> int:
        """Return the maximum production of the inverter in watts."""
        return self._data["maxReportWatts"]
