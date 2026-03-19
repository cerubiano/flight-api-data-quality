"""Service for applying flight data validation rules.

This module will host the FlightValidationService responsible for running
field-level quality rules and populating failed rules on flight models.
"""

# 1. Standard library
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from decimal import Decimal

# 3. Internal — absolute imports only
from src.domain.exceptions import ValidationError
from src.domain.models.flight_model import FlightModel

MIN_CARRIER_CODE_LENGTH = 2
MIN_IATA_CODE_LENGTH = 3

PENALTY_BLOCKING = 1.0
PENALTY_CRITICAL = 0.5
PENALTY_HIGH = 0.4
PENALTY_MEDIUM = 0.2

DIMENSION_COMPLETENESS = "completeness"
DIMENSION_VALIDITY = "validity"
DIMENSION_CONSISTENCY = "consistency"
DIMENSION_CONFORMITY = "conformity"

SEVERITY_BLOCKING = "blocking"
SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"


class ValidationRule(ABC):
    """Abstract validation rule contract."""

    rule_id: str
    dimension: str
    severity: str
    penalty: float

    @abstractmethod
    def validate(self, flight: FlightModel) -> str | None:
        """Validate a single flight against this rule.

        Args:
            flight: Normalized flight offer to validate.

        Returns:
            Error code (rule_id) if the rule fails, otherwise None.
        """


class PriceNullRule(ValidationRule):
    """CM-001 — blocking — total_amount is null."""

    rule_id = "PRICE_NULL"
    dimension = DIMENSION_COMPLETENESS
    severity = SEVERITY_BLOCKING
    penalty = PENALTY_BLOCKING

    def validate(self, flight: FlightModel) -> str | None:
        if flight.total_amount is None:
            return self.rule_id
        return None


class CarrierNullRule(ValidationRule):
    """CM-002 — blocking — flight_number or carrier_code is null."""

    rule_id = "CARRIER_NULL"
    dimension = DIMENSION_COMPLETENESS
    severity = SEVERITY_BLOCKING
    penalty = PENALTY_BLOCKING

    def validate(self, flight: FlightModel) -> str | None:
        if flight.flight_number is None or flight.carrier_code is None:
            return self.rule_id
        return None


class FareBasisNullRule(ValidationRule):
    """CM-003 — medium — fare_basis is null."""

    rule_id = "FARE_BASIS_NULL"
    dimension = DIMENSION_COMPLETENESS
    severity = SEVERITY_MEDIUM
    penalty = PENALTY_MEDIUM

    def validate(self, flight: FlightModel) -> str | None:
        if flight.fare_basis is None:
            return self.rule_id
        return None


class CheckedBagsNullRule(ValidationRule):
    """CM-004 — medium — checked_bags is null."""

    rule_id = "CHECKED_BAGS_NULL"
    dimension = DIMENSION_COMPLETENESS
    severity = SEVERITY_MEDIUM
    penalty = PENALTY_MEDIUM

    def validate(self, flight: FlightModel) -> str | None:
        if flight.checked_bags is None:
            return self.rule_id
        return None


class CarryOnNullRule(ValidationRule):
    """CM-005 — medium — carry_on_bags is null."""

    rule_id = "CARRY_ON_BAGS_NULL"
    dimension = DIMENSION_COMPLETENESS
    severity = SEVERITY_MEDIUM
    penalty = PENALTY_MEDIUM

    def validate(self, flight: FlightModel) -> str | None:
        if flight.carry_on_bags is None:
            return self.rule_id
        return None


class RefundPolicyNullRule(ValidationRule):
    """CM-006 — medium — refund_allowed is null."""

    rule_id = "REFUND_POLICY_MISSING"
    dimension = DIMENSION_COMPLETENESS
    severity = SEVERITY_MEDIUM
    penalty = PENALTY_MEDIUM

    def validate(self, flight: FlightModel) -> str | None:
        if flight.refund_allowed is None:
            return self.rule_id
        return None


class ChangePolicyNullRule(ValidationRule):
    """CM-007 — medium — change_allowed is null."""

    rule_id = "CHANGE_POLICY_MISSING"
    dimension = DIMENSION_COMPLETENESS
    severity = SEVERITY_MEDIUM
    penalty = PENALTY_MEDIUM

    def validate(self, flight: FlightModel) -> str | None:
        if flight.change_allowed is None:
            return self.rule_id
        return None


class CarrierCodeLengthRule(ValidationRule):
    """VL-001 — high — carrier_code must be exactly 2 characters."""

    rule_id = "CARRIER_CODE_INVALID"
    dimension = DIMENSION_VALIDITY
    severity = SEVERITY_HIGH
    penalty = PENALTY_HIGH

    def validate(self, flight: FlightModel) -> str | None:
        if flight.carrier_code is None:
            return None
        if len(flight.carrier_code) != MIN_CARRIER_CODE_LENGTH:
            return self.rule_id
        return None


class OriginIATALengthRule(ValidationRule):
    """VL-002 — high — origin_iata must be exactly 3 characters."""

    rule_id = "ORIGIN_INVALID"
    dimension = DIMENSION_VALIDITY
    severity = SEVERITY_HIGH
    penalty = PENALTY_HIGH

    def validate(self, flight: FlightModel) -> str | None:
        if flight.origin_iata is None:
            return None
        if len(flight.origin_iata) != MIN_IATA_CODE_LENGTH:
            return self.rule_id
        return None


class DestIATALengthRule(ValidationRule):
    """VL-003 — high — destination_iata must be exactly 3 characters."""

    rule_id = "DESTINATION_INVALID"
    dimension = DIMENSION_VALIDITY
    severity = SEVERITY_HIGH
    penalty = PENALTY_HIGH

    def validate(self, flight: FlightModel) -> str | None:
        if flight.destination_iata is None:
            return None
        if len(flight.destination_iata) != MIN_IATA_CODE_LENGTH:
            return self.rule_id
        return None


class DepartureDateFormatRule(ValidationRule):
    """VL-004 — high — departure_at must be a datetime."""

    rule_id = "DEPARTURE_DATE_INVALID"
    dimension = DIMENSION_VALIDITY
    severity = SEVERITY_HIGH
    penalty = PENALTY_HIGH

    def validate(self, flight: FlightModel) -> str | None:
        if not isinstance(flight.departure_at, datetime):
            return self.rule_id
        return None


class CurrencyFormatRule(ValidationRule):
    """VL-005 — high — currency must be exactly 3 characters."""

    rule_id = "CURRENCY_INVALID"
    dimension = DIMENSION_VALIDITY
    severity = SEVERITY_HIGH
    penalty = PENALTY_HIGH

    def validate(self, flight: FlightModel) -> str | None:
        if flight.currency is None:
            return self.rule_id
        if len(flight.currency) != 3:
            return self.rule_id
        return None


class PriceZeroRule(ValidationRule):
    """CS-001 — blocking — total_amount is zero or negative."""

    rule_id = "PRICE_ZERO"
    dimension = DIMENSION_CONSISTENCY
    severity = SEVERITY_BLOCKING
    penalty = PENALTY_BLOCKING

    def validate(self, flight: FlightModel) -> str | None:
        if flight.total_amount is None:
            return None
        if flight.total_amount <= Decimal("0"):
            return self.rule_id
        return None


class PriceMismatchRule(ValidationRule):
    """CS-002 — critical — base_amount + tax_amount must equal total_amount."""

    rule_id = "PRICE_MISMATCH"
    dimension = DIMENSION_CONSISTENCY
    severity = SEVERITY_CRITICAL
    penalty = PENALTY_CRITICAL

    def validate(self, flight: FlightModel) -> str | None:
        if flight.base_amount is None or flight.tax_amount is None or flight.total_amount is None:
            return None
        if (flight.base_amount + flight.tax_amount) != flight.total_amount:
            return self.rule_id
        return None


class ArrivalBeforeDeptRule(ValidationRule):
    """CS-003 — critical — arrival_at must be after departure_at."""

    rule_id = "ARRIVAL_BEFORE_DEPARTURE"
    dimension = DIMENSION_VALIDITY
    severity = SEVERITY_CRITICAL
    penalty = PENALTY_CRITICAL

    def validate(self, flight: FlightModel) -> str | None:
        if flight.arrival_at <= flight.departure_at:
            return self.rule_id
        return None


class BagsNegativeRule(ValidationRule):
    """CS-004 — medium — baggage counts must not be negative."""

    rule_id = "BAGS_NEGATIVE"
    dimension = DIMENSION_CONSISTENCY
    severity = SEVERITY_MEDIUM
    penalty = PENALTY_MEDIUM

    def validate(self, flight: FlightModel) -> str | None:
        if flight.checked_bags is not None and flight.checked_bags < 0:
            return self.rule_id
        if flight.carry_on_bags is not None and flight.carry_on_bags < 0:
            return self.rule_id
        return None


class DeparturePastRule(ValidationRule):
    """CF-001 — critical — departure_at must not be in the past."""

    rule_id = "DEPARTURE_IN_PAST"
    dimension = DIMENSION_CONFORMITY
    severity = SEVERITY_CRITICAL
    penalty = PENALTY_CRITICAL

    def validate(self, flight: FlightModel) -> str | None:
        if flight.departure_at < datetime.now(UTC):
            return self.rule_id
        return None


VALIDATION_RULES: list[ValidationRule] = [
    # Completeness
    PriceNullRule(),
    CarrierNullRule(),
    FareBasisNullRule(),
    CheckedBagsNullRule(),
    CarryOnNullRule(),
    RefundPolicyNullRule(),
    ChangePolicyNullRule(),
    # Validity
    CarrierCodeLengthRule(),
    OriginIATALengthRule(),
    DestIATALengthRule(),
    DepartureDateFormatRule(),
    CurrencyFormatRule(),
    # Consistency
    PriceZeroRule(),
    PriceMismatchRule(),
    ArrivalBeforeDeptRule(),
    BagsNegativeRule(),
    # Conformity
    DeparturePastRule(),
]


class FlightValidationService:
    """Validates flight data against quality rules."""

    def __init__(self, rules: list[ValidationRule]) -> None:
        """Create a validation service.

        Args:
            rules: List of validation rules to apply to each flight.
        """

        self._rules = rules

    def validate(self, flight: FlightModel) -> FlightModel:
        """Validate a flight offer against all configured rules.

        Args:
            flight: Normalized flight offer to validate.

        Returns:
            The same `FlightModel` instance with a `failed_rules` attribute
            populated as a list of error codes.

        Raises:
            ValidationError: If the flight is None or rules are misconfigured.
        """

        if flight is None:
            raise ValidationError("flight must not be None")
        if not self._rules:
            raise ValidationError("no validation rules configured")

        failed_rules: list[str] = []
        for rule in self._rules:
            error_code = rule.validate(flight)
            if error_code is not None:
                failed_rules.append(error_code)

        flight.failed_rules = failed_rules
        return flight
