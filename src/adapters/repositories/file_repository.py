"""File system repository adapter.

Implements RepositoryPort for Bronze, Silver, and Gold layer persistence.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, UTC
from pathlib import Path

import pandas as pd

from src.domain.exceptions import RepositoryError
from src.domain.models.flight_model import FlightModel
from src.domain.ports.repository_port import RepositoryPort

logger = logging.getLogger(__name__)

BRONZE_DIR = "bronze"
SILVER_DIR = "silver"
GOLD_DIR = "gold"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


class FileRepository(RepositoryPort):
    """Local filesystem implementation of RepositoryPort."""

    def __init__(self, base_path: Path) -> None:
        """Create a new FileRepository.

        Args:
            base_path: Root path for all data layers.
        """
        self._base_path = Path(base_path)

    def save_bronze(self, raw_response: dict, source: str) -> Path:
        """Save raw API response to Bronze layer.

        Args:
            raw_response: Provider response payload as received.
            source: Provider identifier (amadeus, duffel).

        Returns:
            Path to the written Bronze JSON file.

        Raises:
            RepositoryError: If the file cannot be written.
        """
        timestamp = datetime.now(UTC).strftime(TIMESTAMP_FORMAT)
        bronze_path = self._base_path / BRONZE_DIR / source
        bronze_path.mkdir(parents=True, exist_ok=True)

        file_path = bronze_path / f"{timestamp}_{source}.json"

        try:
            file_path.write_text(json.dumps(raw_response, indent=2))
            logger.info("Saved bronze: %s", file_path)
            return file_path
        except OSError as e:
            raise RepositoryError(f"Failed to save bronze file: {e}") from e

    def save_silver(self, flights: list[FlightModel]) -> Path:
        """Save normalized flights to Silver layer as Parquet.

        Args:
            flights: Normalized flight offers.

        Returns:
            Path to the written Silver Parquet file.

        Raises:
            RepositoryError: If the file cannot be written.
        """
        timestamp = datetime.now(UTC).strftime(TIMESTAMP_FORMAT)
        silver_path = self._base_path / SILVER_DIR
        silver_path.mkdir(parents=True, exist_ok=True)

        file_path = silver_path / f"{timestamp}_normalized.parquet"

        try:
            records = [
                flight.model_dump(exclude={"quality_metadata", "failed_rules"})
                for flight in flights
            ]
            df = pd.DataFrame(records)
            df.to_parquet(file_path, compression="snappy", index=False)
            logger.info("Saved silver: %s (%d records)", file_path, len(flights))
            return file_path
        except Exception as e:
            raise RepositoryError(f"Failed to save silver file: {e}") from e

    def save_gold(self, flights: list[FlightModel]) -> Path:
        """Save validated and scored flights to Gold layer as Parquet.

        Args:
            flights: Validated and scored flight offers.

        Returns:
            Path to the written Gold Parquet file.

        Raises:
            RepositoryError: If the file cannot be written.
        """
        timestamp = datetime.now(UTC).strftime(TIMESTAMP_FORMAT)
        gold_path = self._base_path / GOLD_DIR
        gold_path.mkdir(parents=True, exist_ok=True)

        file_path = gold_path / f"{timestamp}_validated.parquet"

        try:
            records = []
            for flight in flights:
                record = flight.model_dump(exclude={"quality_metadata"})
                if flight.quality_metadata:
                    record["dq_score"] = flight.quality_metadata.dq_score
                    record["is_valid_flight"] = flight.quality_metadata.is_valid_flight
                    record["processed_at"] = flight.quality_metadata.processed_at
                records.append(record)

            df = pd.DataFrame(records)
            df.to_parquet(file_path, compression="snappy", index=False)
            logger.info("Saved gold: %s (%d records)", file_path, len(flights))
            return file_path
        except Exception as e:
            raise RepositoryError(f"Failed to save gold file: {e}") from e

    def save_results(self, flights: list[FlightModel]) -> None:
        """Not implemented in FileRepository — handled by PostgresRepository."""
        raise NotImplementedError("save_results is handled by PostgresRepository")