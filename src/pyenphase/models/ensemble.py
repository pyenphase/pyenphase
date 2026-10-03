"""Model for devices listed in the Ensemble status."""

# Data Source: URL_ENSEMBLE_STATUS

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class EnvoyEnsembleDevice:
    """Model for a device or submodule listed in the Ensemble status."""

    #: Device serial number
    serial_number: str
    #: Enphase device type code, for example 14 for a battery microinverter
    device_type: int
    #: Device part number
    part_number: str
    #: Running firmware version, from app_fw_version for a device and from
    #: procload.assembly_number for a submodule
    firmware_version: str
    #: Serial number of the device a submodule belongs to, None for a device
    parent_serial_number: str | None = None

    @classmethod
    def from_status(cls, status: dict[str, Any]) -> dict[str, EnvoyEnsembleDevice]:
        """
        Return the devices and submodules in an Ensemble status reply.

        Source data URL_ENSEMBLE_STATUS["inventory"]["serial_nums"]
            .. code-block:: json

                {
                    "492516006337": {
                        "device_type": 13,
                        "part_number": "836-01250-r00",
                        "app_fw_version": "4.5.35",
                        "submodules": {
                            "542517021267": {
                                "device_type": 14,
                                "part_number": "800-02041-r05",
                                "procload": {
                                    "part_number": "521-00012-r00",
                                    "assembly_number": "10.9.63-D14494"
                                }
                            }
                        }
                    }
                }

        A submodule carrying its parent's serial number is skipped, as it
        repeats the parent device. An entry with a missing field is skipped,
        and the submodules of a skipped device are still read.

        Args:
            status (dict[str, Any]): JSON returned from URL_ENSEMBLE_STATUS

        Returns:
            dict[str, EnvoyEnsembleDevice]: Devices and submodules keyed by
                serial number

        """
        devices: dict[str, EnvoyEnsembleDevice] = {}
        for serial, device in status["inventory"]["serial_nums"].items():
            try:
                devices[serial] = cls(
                    serial_number=serial,
                    device_type=device["device_type"],
                    part_number=device["part_number"],
                    firmware_version=device["app_fw_version"],
                )
            except KeyError as err:
                _LOGGER.debug(
                    "Missing data field for ensemble device %s: %r", serial, err
                )
            if not (submodules := device.get("submodules")):
                continue
            for sub_serial, submodule in submodules.items():
                if sub_serial == serial:
                    continue
                try:
                    devices[sub_serial] = cls(
                        serial_number=sub_serial,
                        device_type=submodule["device_type"],
                        part_number=submodule["part_number"],
                        firmware_version=submodule["procload"]["assembly_number"],
                        parent_serial_number=serial,
                    )
                except KeyError as err:
                    _LOGGER.debug(
                        "Missing data field for ensemble submodule %s: %r",
                        sub_serial,
                        err,
                    )
        return devices
