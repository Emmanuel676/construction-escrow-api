class ServiceError(Exception):
    """Base class for domain errors raised by the service layer."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(ServiceError):
    """A referenced record does not exist."""


class ConflictError(ServiceError):
    """The record is not in a state that allows the requested change."""
