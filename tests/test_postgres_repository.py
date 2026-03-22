"""Tests for PostgresRepository."""

# 1. Standard library
from datetime import datetime, UTC
from decimal import Decimal
from unittest.mock import MagicMock, patch, call
import json

# 2. Third-party
import pytest

# 3. Internal
from src.adapters.repositories.postgres_repository import PostgresRepository
from src.domain.exceptions import RepositoryError
from src.domain.models.flight_model import FlightModel, QualityMetadata


@pytest.fixture
def repository() -> PostgresRepository:
    """PostgresRepository with fake connection string."""
    return PostgresRepository(
        host="localhost",
        port=5432,
        database="flight_dq",
        user="crubiano",
        password="",
    )


@pytest.fixture
def scored_flight(valid_duffel_flight: FlightModel) -> FlightModel:
    """Valid flight with quality_metadata populated."""
    valid_duffel_flight.failed_rules = ["REFUND_POLICY_MISSING"]
    valid_duffel_flight.quality_metadata = QualityMetadata(
        dq_score=0.8,
        is_valid_flight=True,
        failed_rules=["REFUND_POLICY_MISSING"],
        processed_at=datetime(2026, 3, 22, 12, 0, 0, tzinfo=UTC),
    )
    return valid_duffel_flight


def test_save_results_executes_insert(
    repository: PostgresRepository,
    scored_flight: FlightModel,
) -> None:
    # Arrange
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("src.adapters.repositories.postgres_repository.psycopg2.connect") as mock_connect:
        mock_connect.return_value = mock_conn

        # Act
        repository.save_results([scored_flight])

    # Assert
    assert mock_cursor.execute.called


def test_save_results_empty_list_does_not_execute(
    repository: PostgresRepository,
) -> None:
    # Arrange
    mock_conn = MagicMock()
    with patch("src.adapters.repositories.postgres_repository.psycopg2.connect") as mock_connect:
        mock_connect.return_value = mock_conn

        # Act
        repository.save_results([])

    # Assert
    mock_conn.cursor.assert_not_called()


def test_save_results_flight_without_metadata_raises_repository_error(
    repository: PostgresRepository,
    valid_duffel_flight: FlightModel,
) -> None:
    # Arrange — flight has no quality_metadata
    mock_conn = MagicMock()
    with patch("src.adapters.repositories.postgres_repository.psycopg2.connect") as mock_connect:
        mock_connect.return_value = mock_conn

        # Act & Assert
        with pytest.raises(RepositoryError):
            repository.save_results([valid_duffel_flight])


def test_save_results_connection_error_raises_repository_error(
    repository: PostgresRepository,
    scored_flight: FlightModel,
) -> None:
    # Arrange
    import psycopg2
    with patch("src.adapters.repositories.postgres_repository.psycopg2.connect") as mock_connect:
        mock_connect.side_effect = psycopg2.OperationalError("connection refused")

        # Act & Assert
        with pytest.raises(RepositoryError):
            repository.save_results([scored_flight])