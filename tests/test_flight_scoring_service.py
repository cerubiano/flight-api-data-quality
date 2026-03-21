from datetime import datetime, UTC
from decimal import Decimal

from src.domain.models.flight_model import FlightModel
from src.domain.services.flight_scoring_service import FlightScoringService


def _flight_with_failed_rules(flight: FlightModel, failed_rules: list[str]) -> FlightModel:
    """Create a FlightModel with pre-populated failed_rules for scoring tests."""
    flight.failed_rules = failed_rules
    return flight


def test_score_null_price_returns_zero(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _flight_with_failed_rules(valid_duffel_flight, ["PRICE_NULL"])
    service = FlightScoringService()

    # Act
    result = service.score(flight)

    # Assert
    assert result.quality_metadata.dq_score == 0.0
    assert result.quality_metadata.is_valid_flight is False
    assert "PRICE_NULL" in result.quality_metadata.failed_rules


def test_score_price_mismatch_returns_0_5(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _flight_with_failed_rules(valid_duffel_flight, ["PRICE_MISMATCH"])
    service = FlightScoringService()

    # Act
    result = service.score(flight)

    # Assert
    assert result.quality_metadata.dq_score == 0.5
    assert result.quality_metadata.is_valid_flight is True
    assert "PRICE_MISMATCH" in result.quality_metadata.failed_rules


def test_score_fare_basis_and_bags_null_returns_0_6(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _flight_with_failed_rules(
        valid_duffel_flight,
        ["FARE_BASIS_NULL", "CHECKED_BAGS_NULL"]
    )
    service = FlightScoringService()

    # Act
    result = service.score(flight)

    # Assert
    assert result.quality_metadata.dq_score == 0.6
    assert result.quality_metadata.is_valid_flight is True


def test_score_all_valid_returns_1_0(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _flight_with_failed_rules(valid_duffel_flight, [])
    service = FlightScoringService()

    # Act
    result = service.score(flight)

    # Assert
    assert result.quality_metadata.dq_score == 1.0
    assert result.quality_metadata.is_valid_flight is True
    assert result.quality_metadata.failed_rules == []


def test_score_invalid_iata_returns_0_6(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _flight_with_failed_rules(valid_duffel_flight, ["ORIGIN_INVALID"])
    service = FlightScoringService()

    # Act
    result = service.score(flight)

    # Assert
    assert result.quality_metadata.dq_score == 0.6
    assert result.quality_metadata.is_valid_flight is True
    assert "ORIGIN_INVALID" in result.quality_metadata.failed_rules


def test_score_multiple_penalties_floors_at_zero(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _flight_with_failed_rules(
        valid_duffel_flight,
        ["PRICE_NULL", "CARRIER_NULL", "PRICE_MISMATCH"]
    )
    service = FlightScoringService()

    # Act
    result = service.score(flight)

    # Assert
    assert result.quality_metadata.dq_score == 0.0
    assert result.quality_metadata.is_valid_flight is False


def test_score_populates_processed_at(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _flight_with_failed_rules(valid_duffel_flight, [])
    service = FlightScoringService()

    # Act
    result = service.score(flight)

    # Assert
    assert result.quality_metadata.processed_at is not None
    assert isinstance(result.quality_metadata.processed_at, datetime)


def test_score_unknown_rule_raises_scoring_error(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    from src.domain.exceptions import ScoringError
    flight = _flight_with_failed_rules(valid_duffel_flight, ["UNKNOWN_RULE"])
    service = FlightScoringService()

    # Act & Assert
    try:
        service.score(flight)
        assert False, "Expected ScoringError"
    except ScoringError:
        pass