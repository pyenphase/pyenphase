import json

import httpx


class EnvoyError(Exception):
    """Base class for Envoy exceptions."""


class EnvoyFirmwareCheckError(EnvoyError):
    """Exception raised when unable to query the Envoy firmware version."""

    def __init__(self, status_code: int, status: str) -> None:
        self.status_code = status_code
        self.status = status


class EnvoyFirmwareFatalCheckError(EnvoyError):
    """Exception raised when we should not retry the Envoy firmware version."""

    def __init__(self, status_code: int, status: str) -> None:
        self.status_code = status_code
        self.status = status


class EnvoyAuthenticationError(EnvoyError):
    """Exception raised when unable to query the Envoy firmware version."""

    def __init__(self, status: str) -> None:
        self.status = status


class EnvoyAuthenticationRequired(EnvoyError):
    """Exception raised when authentication hasn't been setup."""

    def __init__(self, status: str) -> None:
        self.status = status


class EnvoyHTTPStatusError(EnvoyError):
    """Exception raised when unable to query the Envoy status."""

    def __init__(self, status_code: int, url: str) -> None:
        self.status_code = status_code
        self.url = url
        super().__init__(f"HTTP status error {url} {status_code}")


class EnvoyProbeFailed(EnvoyError):
    """Exception raised when the Envoy probe fails."""


class EnvoyCommunicationError(EnvoyError):
    """Exception raised when the Envoy communication fails."""


class EnvoyFeatureNotAvailable(EnvoyError):
    """Exception raised when the Envoy feature is not available."""


class EnvoyPoorDataQuality(EnvoyError):
    """Exception raised when data identifies known issues."""

    def __init__(self, status: str) -> None:
        self.status = status


ENDPOINT_PROBE_EXCEPTIONS = (
    json.JSONDecodeError,
    httpx.HTTPError,
    EnvoyHTTPStatusError,
)
