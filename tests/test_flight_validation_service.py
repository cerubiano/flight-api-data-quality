from datetime import datetime, UTC
from decimal import Decimal

from src.domain.models.flight_model import FlightModel
from src.domain.services.flight_validation_service import (
    FlightValidationService,
    VALIDATION_RULES,
)


def _construct_flight_with_overrides(flight: FlightModel, **overrides) -> FlightModel:
    """Create a FlightModel instance with overrides (bypassing Pydantic validation).

    Uses model_construct to bypass validators so tests can reach
    code paths with malformed values (wrong lengths, nulls, etc.).
    """
    data = flight.model_dump()
    data.update(overrides)
    return FlightModel.model_construct(**data)


def test_price_null_returns_price_null_error(valid_amadeus_flight: FlightModel) -> None:
    # Arrange
    flight = _construct_flight_with_overrides(valid_amadeus_flight, total_amount=None)
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert "PRICE_NULL" in result.failed_rules


def test_price_mismatch_returns_price_mismatch_error(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _construct_flight_with_overrides(
        valid_duffel_flight,
        base_amount=Decimal("200.00"),
        tax_amount=Decimal("50.00"),
        total_amount=Decimal("300.00"),
    )
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert result.failed_rules == ["PRICE_MISMATCH"]


def test_fare_basis_and_bags_null_returns_both_errors(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _construct_flight_with_overrides(
        valid_duffel_flight,
        fare_basis=None,
        checked_bags=None,
    )
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert result.failed_rules == ["FARE_BASIS_NULL", "CHECKED_BAGS_NULL"]


def test_all_valid_returns_no_errors(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(valid_duffel_flight)

    # Assert
    assert result.failed_rules == []


def test_origin_iata_four_chars_returns_origin_invalid(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _construct_flight_with_overrides(valid_duffel_flight, origin_iata="YUUL")
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert result.failed_rules == ["ORIGIN_INVALID"]


def test_carrier_code_null_returns_carrier_null(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _construct_flight_with_overrides(valid_duffel_flight, carrier_code=None)
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert result.failed_rules == ["CARRIER_NULL"]


def test_carry_on_null_returns_carry_on_null(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _construct_flight_with_overrides(valid_duffel_flight, carry_on_bags=None)
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert result.failed_rules == ["CARRY_ON_BAGS_NULL"]


def test_refund_null_returns_refund_missing(valid_amadeus_flight: FlightModel) -> None:
    # Arrange
    flight = _construct_flight_with_overrides(
        valid_amadeus_flight,
        refund_allowed=None,
        change_allowed=False,
    )
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert result.failed_rules == ["REFUND_POLICY_MISSING"]


def test_change_null_returns_change_missing(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _construct_flight_with_overrides(
        valid_duffel_flight,
        refund_allowed=True,
        change_allowed=None,
    )
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert result.failed_rules == ["CHANGE_POLICY_MISSING"]


def test_carrier_code_three_chars_returns_invalid(valid_amadeus_flight: FlightModel) -> None:
    # Arrange
    flight = _construct_flight_with_overrides(valid_amadeus_flight, carrier_code="AAA")
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert "CARRIER_CODE_INVALID" in result.failed_rules


def test_destination_iata_two_chars_returns_invalid(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _construct_flight_with_overrides(valid_duffel_flight, destination_iata="LA")
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert result.failed_rules == ["DESTINATION_INVALID"]


def test_departure_not_datetime_returns_format_error(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    class NonDatetimeDeparture:
        """Non-datetime departure value that still supports comparisons."""
        def __ge__(self, other: datetime) -> bool:
            return False
        def __lt__(self, other: datetime) -> bool:
            return False

    flight = _construct_flight_with_overrides(
        valid_duffel_flight,
        departure_at=NonDatetimeDeparture(),
    )
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert result.failed_rules == ["DEPARTURE_DATE_INVALID"]


def test_currency_four_chars_returns_invalid(valid_amadeus_flight: FlightModel) -> None:
    # Arrange
    flight = _construct_flight_with_overrides(valid_amadeus_flight, currency="USDD")
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert "CURRENCY_INVALID" in result.failed_rules


def test_zero_price_returns_price_zero(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _construct_flight_with_overrides(
        valid_duffel_flight,
        total_amount=Decimal("0"),
        base_amount=Decimal("0"),
        tax_amount=Decimal("0"),
    )
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert result.failed_rules == ["PRICE_ZERO"]


def test_arrival_equals_departure_returns_arrival_error(valid_duffel_flight: FlightModel) -> None:
    # Arrange
    flight = _construct_flight_with_overrides(
        valid_duffel_flight,
        arrival_at=valid_duffel_flight.departure_at,
    )
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert result.failed_rules == ["ARRIVAL_BEFORE_DEPARTURE"]


def test_negative_bags_returns_bags_negative(valid_amadeus_flight: FlightModel) -> None:
    # Arrange
    flight = _construct_flight_with_overrides(
        valid_amadeus_flight,
        checked_bags=-1,
        carry_on_bags=0,
    )
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert "BAGS_NEGATIVE" in result.failed_rules


def test_departure_in_past_returns_departure_error(valid_amadeus_flight: FlightModel) -> None:
    # Arrange
    flight = _construct_flight_with_overrides(
        valid_amadeus_flight,
        departure_at=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
        arrival_at=datetime(2026, 1, 2, 0, 0, tzinfo=UTC),
    )
    service = FlightValidationService(VALIDATION_RULES)

    # Act
    result = service.validate(flight)

    # Assert
    assert "DEPARTURE_IN_PAST" in result.failed_rules