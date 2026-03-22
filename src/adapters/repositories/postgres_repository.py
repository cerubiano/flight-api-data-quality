"""PostgreSQL repository adapter.

Implements RepositoryPort for persisting validation results to PostgreSQL.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import psycopg2

from src.domain.exceptions import RepositoryError
from src.domain.models.flight_model import FlightModel
from src.domain.ports.repository_port import RepositoryPort

logger = logging.getLogger(__name__)

INSERT_DQ_RESULT = """
    INSERT INTO dq_results (
        source,
        carrier_code,
        flight_number,
        origin_iata,
        destination_iata,
        departure_at,
        total_amount,
        currency,
        checked_bags,
        carry_on_bags,
        fare_brand,
        refund_allowed,
        change_allowed,
        score_overall,
        failed_rules,
        is_valid_flight
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
"""


class PostgresRepository(RepositoryPort):
    """PostgreSQL implementation of RepositoryPort."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
    ) -> None:
        """Create a new PostgresRepository.

        Args:
            host: PostgreSQL host.
            port: PostgreSQL port.
            database: Database name.
            user: Database user.
            password: Database password.
        """
        self._host = host
        self._port = port
        self._database = database
        self._user = user
        self._password = password

    def save_bronze(self, raw_response: dict, source: str) -> Path:
        """Not implemented in PostgresRepository — handled by FileRepository."""
        raise NotImplementedError("save_bronze is handled by FileRepository")

    def save_silver(self, flights: list[FlightModel]) -> Path:
        """Not implemented in PostgresRepository — handled by FileRepository."""
        raise NotImplementedError("save_silver is handled by FileRepository")

    def save_gold(self, flights: list[FlightModel]) -> Path:
        """Not implemented in PostgresRepository — handled by FileRepository."""
        raise NotImplementedError("save_gold is handled by FileRepository")

    def save_results(self, flights: list[FlightModel]) -> None:
        """Persist quality scores to PostgreSQL dq_results table.

        Args:
            flights: Validated and scored flight offers with quality_metadata.

        Raises:
            RepositoryError: If any flight is missing quality_metadata or
                             if the database operation fails.
        """
        if not flights:
            return

        for flight in flights:
            if flight.quality_metadata is None:
                raise RepositoryError(
                    f"Flight {flight.flight_number} missing quality_metadata — "
                    "run FlightScoringService before saving results"
                )

        try:
            with psycopg2.connect(
                host=self._host,
                port=self._port,
                dbname=self._database,
                user=self._user,
                password=self._password,
            ) as conn:
                with conn.cursor() as cursor:
                    for flight in flights:
                        cursor.execute(
                            INSERT_DQ_RESULT,
                            (
                                flight.source,
                                flight.carrier_code,
                                flight.flight_number,
                                flight.origin_iata,
                                flight.destination_iata,
                                flight.departure_at,
                                float(flight.total_amount) if flight.total_amount else None,
                                flight.currency,
                                flight.checked_bags,
                                flight.carry_on_bags,
                                flight.fare_brand,
                                flight.refund_allowed,
                                flight.change_allowed,
                                flight.quality_metadata.dq_score,
                                json.dumps(flight.quality_metadata.failed_rules),
                                flight.quality_metadata.is_valid_flight,
                            ),
                        )
                conn.commit()
                logger.info("Saved %d results to dq_results", len(flights))

        except psycopg2.OperationalError as e:
            raise RepositoryError(f"PostgreSQL connection failed: {e}") from e
        except psycopg2.Error as e:
            raise RepositoryError(f"PostgreSQL operation failed: {e}") from e