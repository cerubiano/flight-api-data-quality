"""Tests for FileRepository."""

# 1. Standard library
import json
from datetime import datetime, UTC
from decimal import Decimal
from pathlib import Path

# 2. Third-party
import pytest

# 3. Internal
from src.adapters.repositories.file_repository import FileRepository
from src.domain.models.flight_model import FlightModel, QualityMetadata


@pytest.fixture
def repository(tmp_path: Path) -> FileRepository:
    """FileRepository using pytest tmp_path for isolation."""
    return FileRepository(base_path=tmp_path)


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


def test_save_bronze_creates_json_file(repository: FileRepository) -> None:
    # Arrange
    raw_response = {"data": [{"carrier_code": "AC"}]}

    # Act
    path = repository.save_bronze(raw_response, "amadeus")

    # Assert
    assert path.exists()
    assert path.suffix == ".json"
    assert "amadeus" in str(path)


def test_save_bronze_content_matches_input(repository: FileRepository) -> None:
    # Arrange
    raw_response = {"data": [{"carrier_code": "AC"}]}

    # Act
    path = repository.save_bronze(raw_response, "amadeus")

    # Assert
    content = json.loads(path.read_text())
    assert content == raw_response


def test_save_silver_creates_parquet_file(
    repository: FileRepository,
    valid_duffel_flight: FlightModel,
) -> None:
    # Act
    path = repository.save_silver([valid_duffel_flight])

    # Assert
    assert path.exists()
    assert path.suffix == ".parquet"


def test_save_gold_creates_parquet_file(
    repository: FileRepository,
    scored_flight: FlightModel,
) -> None:
    # Act
    path = repository.save_gold([scored_flight])

    # Assert
    assert path.exists()
    assert path.suffix == ".parquet"


def test_save_bronze_creates_source_subdirectory(repository: FileRepository) -> None:
    # Arrange
    raw_response = {"data": []}

    # Act
    path = repository.save_bronze(raw_response, "duffel")

    # Assert
    assert "duffel" in str(path)
    assert path.parent.exists()
