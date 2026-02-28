from dataclasses import dataclass


class IngestV2Error(Exception):
    """Base error: messages must be stable and deterministic."""
    exit_code = 2


@dataclass
class ValidationError(IngestV2Error):
    message: str
    exit_code: int = 3

    def __str__(self) -> str:
        return self.message


@dataclass
class DbError(IngestV2Error):
    message: str
    exit_code: int = 4

    def __str__(self) -> str:
        return self.message


@dataclass
class ConflictError(IngestV2Error):
    message: str
    exit_code: int = 5

    def __str__(self) -> str:
        return self.message