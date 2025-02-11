"""Enphase Envoy exceptions."""

import json

import httpx


class EnvoyError(Exception):
    """Base class for Envoy exceptions."""


class EnvoyFirmwareCheckError(EnvoyError):
    """
    Exception raised when unable to query the Envoy firmware version.

    - http error when sending request to Envoy
    - Any http status code other then 200 received

    :param status_code: http status code
    :param status: Error status description
    """

    def __init__(self, status_code: int, status: str) -> None:
        self.status_code = status_code
        self.status = status


class EnvoyFirmwareFatalCheckError(EnvoyError):
    """
    Exception raised when we should not retry getting the Envoy firmware version.

    - httpx timeout or connection error when sending request to Envoy

    :param status_code: http status code
    :param status: Error status description
    """

    def __init__(self, status_code: int, status: str) -> None:
        self.status_code = status_code
        self.status = status


class EnvoyAuthenticationError(EnvoyError):
    """
    Exception raised when Envoy Authentication fails.

    - When a jwt token authentication failure occurs with the local Envoy.
    - When using token authentication and no cloud credentials or envoy serial are specified
    - When a failure occurs during obtaining a token from the Enlighten cloud

    :param status: Error status description
    """

    def __init__(self, status: str) -> None:
        self.status = status


class EnvoyAuthenticationRequired(EnvoyError):
    """
    Exception raised when authentication hasn't been setup.

    - When communication with Envoy was attempted without setting up authentication.
    - When neither token nor username and/or password are specified during authentication.

    :param status: Error status description
    """

    def __init__(self, status: str) -> None:
        self.status = status


class EnvoyHTTPStatusError(EnvoyError):
    """
    Exception raised when unable to query the Envoy.

    - HTTP Status of request not in 200 range.

    :param status_code: http status code
    :param status: Error status description
    :param url: failing url
    """

    def __init__(self, status_code: int, url: str) -> None:
        self.status_code = status_code
        self.url = url
        super().__init__(f"HTTP status error {url} {status_code}")


class EnvoyProbeFailed(EnvoyError):
    """Exception raised when the Envoy probe fails."""


class EnvoyCommunicationError(EnvoyError):
    """
    Exception raised when the Envoy communication fails.

    - EndOfStream is reported during communication.
    - httpx.NetworkError error occurs.
    - httpx.TimeoutException error occurs
    """


class EnvoyFeatureNotAvailable(EnvoyError):
    """
    Exception raised when the Envoy feature is not available.

    - When using go on/off grid and ENPOWER feature is not available in Envoy

    """


class EnvoyPoorDataQuality(EnvoyError):
    """
    Exception raised when data identifies known issues.

    - FW 3.x production values all zero at startup

    :param status: Error status description
    """

    def __init__(self, status: str) -> None:
        self.status = status


ENDPOINT_PROBE_EXCEPTIONS = (
    json.JSONDecodeError,
    httpx.HTTPError,
    EnvoyHTTPStatusError,
)
