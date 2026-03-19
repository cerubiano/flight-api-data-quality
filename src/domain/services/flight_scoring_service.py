"""Service for computing data quality scores.

This module will host the FlightScoringService responsible for turning
validation results into overall data quality scores and flags.
"""

# 1. Standard library
from datetime import UTC, datetime

# 3. Internal — absolute imports only
from src.domain.exceptions import ScoringError
from src.domain.models.flight_model import FlightModel, QualityMetadata

BASE_DQ_SCORE = 1.0
MIN_DQ_SCORE = 0.0
VALID_FLIGHT_THRESHOLD = 0.5
DQ_SCORE_DECIMALS = 2

PENALTY_BLOCKING = 1.0
PENALTY_CRITICAL = 0.5
PENALTY_HIGH = 0.4
PENALTY_MEDIUM = 0.2

PENALTY_MAP: dict[str, float] = {
    # Completeness
    "PRICE_NULL": PENALTY_BLOCKING,
    "CARRIER_NULL": PENALTY_BLOCKING,
    "FARE_BASIS_NULL": PENALTY_MEDIUM,
    "CHECKED_BAGS_NULL": PENALTY_MEDIUM,
    "CARRY_ON_BAGS_NULL": PENALTY_MEDIUM,
    "REFUND_POLICY_MISSING": PENALTY_MEDIUM,
    "CHANGE_POLICY_MISSING": PENALTY_MEDIUM,
    # Validity
    "CARRIER_CODE_INVALID": PENALTY_HIGH,
    "ORIGIN_INVALID": PENALTY_HIGH,
    "DESTINATION_INVALID": PENALTY_HIGH,
    "DEPARTURE_DATE_INVALID": PENALTY_HIGH,
    "CURRENCY_INVALID": PENALTY_HIGH,
    # Consistency
    "PRICE_ZERO": PENALTY_BLOCKING,
    "PRICE_MISMATCH": PENALTY_CRITICAL,
    "ARRIVAL_BEFORE_DEPARTURE": PENALTY_CRITICAL,
    "BAGS_NEGATIVE": PENALTY_MEDIUM,
    # Conformity
    "DEPARTURE_IN_PAST": PENALTY_CRITICAL,
}


class FlightScoringService:
    """Calculates data quality scores for flight offers."""

    def score(self, flight: FlightModel) -> FlightModel:
        """Calculate dq_score from failed rules and populate quality metadata.

        Args:
            flight: Normalized flight offer with `failed_rules` populated.

        Returns:
            The same `FlightModel` instance with `quality_metadata` populated.

        Raises:
            ScoringError: If the flight is None or contains unknown rule IDs.
        """

        if flight is None:
            raise ScoringError("flight must not be None")

        score = BASE_DQ_SCORE
        for rule_id in flight.failed_rules:
            if rule_id not in PENALTY_MAP:
                raise ScoringError(f"Unknown rule_id: {rule_id}")
            score -= PENALTY_MAP[rule_id]

        score = max(MIN_DQ_SCORE, score)

        flight.quality_metadata = QualityMetadata(
            dq_score=round(score, DQ_SCORE_DECIMALS),
            is_valid_flight=score >= VALID_FLIGHT_THRESHOLD,
            failed_rules=flight.failed_rules,
            processed_at=datetime.now(UTC),
        )
        return flight
