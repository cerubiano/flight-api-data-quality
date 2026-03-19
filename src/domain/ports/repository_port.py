"""Port definitions for storage repositories.

This module declares the RepositoryPort interface used by file and database
adapters for Bronze, Silver, Gold, and results persistence.
"""

# 1. Standard library
from abc import ABC, abstractmethod
from pathlib import Path

# 3. Internal — absolute imports only
from src.domain.models.flight_model import FlightModel


class RepositoryPort(ABC):
    """Contract for persistence of flight pipeline artifacts.

    Implementations handle external I/O (filesystem, PostgreSQL, etc.) while the
    domain remains infrastructure-agnostic.
    """

    @abstractmethod
    def save_bronze(self, raw_response: dict, source: str) -> Path:
        """Save raw API response to Bronze layer.

        Args:
            raw_response: Provider response payload as received (no transforms).
            source: Provider identifier (e.g., amadeus, duffel).

        Returns:
            Path to the written Bronze JSON file.
        """

    @abstractmethod
    def save_silver(self, flights: list[FlightModel]) -> Path:
        """Save normalized flights to Silver layer as Parquet.

        Args:
            flights: Normalized flight offers (Silver schema).

        Returns:
            Path to the written Silver Parquet file.
        """

    @abstractmethod
    def save_gold(self, flights: list[FlightModel]) -> Path:
        """Save validated and scored flights to Gold layer as Parquet.

        Args:
            flights: Validated and scored flight offers (Gold schema).

        Returns:
            Path to the written Gold Parquet file.
        """

    @abstractmethod
    def save_results(self, flights: list[FlightModel]) -> None:
        """Persist quality scores to PostgreSQL dq_results table.

        Args:
            flights: Validated and scored flight offers containing quality metadata.
        """
