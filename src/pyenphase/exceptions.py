class EnvoyFirmwareCheckError(Exception):
    """Exception raised when unable to query the Envoy firmware version."""

    def __init__(self, status_code: int, status: str) -> None:
        self.status_code = status_code
        self.status = status


class EnvoyFirmwareFatalCheckError(Exception):
    """Exception raised when we should not retry the Envoy firmware version."""

    def __init__(self, status_code: int, status: str) -> None:
        self.status_code = status_code
        self.status = status


class EnvoyAuthenticationError(Exception):
    """Exception raised when unable to query the Envoy firmware version."""

    def __init__(self, status: str) -> None:
        self.status = status


class EnvoyAuthenticationRequired(Exception):
    """Exception raised when authentication hasn't been setup."""

    def __init__(self, status: str) -> None:
        self.status = status
