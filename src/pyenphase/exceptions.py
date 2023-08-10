import json

import httpx

ENDPOINT_PROBE_EXCEPTIONS = (json.JSONDecodeError, httpx.HTTPError)


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


class EnvoyProbeFailed(EnvoyError):
    """Exception raised when the Envoy probe fails."""


class EnvoyCommunicationError(EnvoyError):
    """Exception raised when the Envoy communication fails."""


class EnvoyFeatureNotAvailable(EnvoyError):
    """Exception raised when the Envoy feature is not available."""
