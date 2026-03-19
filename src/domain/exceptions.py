class DomainError(Exception):
    """Base exception for all domain errors."""


class ValidationError(DomainError):
    """Raised when flight validation fails critically."""


class ScoringError(DomainError):
    """Raised when scoring cannot be completed."""


class AdapterError(Exception):
    """Raised when an external API call fails."""


class RepositoryError(Exception):
    """Raised when a storage operation fails."""
