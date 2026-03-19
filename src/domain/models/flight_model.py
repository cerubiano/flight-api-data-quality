"""Domain flight model and related quality metadata.

This module defines the core Pydantic models for the normalized flight schema
and its associated quality metadata used across the pipeline.
"""

# 1. Standard library
from datetime import datetime
from decimal import Decimal

# 2. Third-party
from pydantic import BaseModel, ConfigDict, Field, field_validator

MIN_CARRIER_CODE_LENGTH = 2
MAX_CARRIER_CODE_LENGTH = 2
MIN_IATA_CODE_LENGTH = 3
MAX_IATA_CODE_LENGTH = 3


class QualityMetadata(BaseModel):
    """Quality scoring metadata for a single flight offer."""

    model_config = ConfigDict(str_strip_whitespace=True)

    dq_score: float = Field(..., ge=0.0, le=1.0)
    is_valid_flight: bool
    failed_rules: list[str]
    processed_at: datetime


class FlightModel(BaseModel):
    """Normalized flight offer model (domain)."""

    model_config = ConfigDict(str_strip_whitespace=True, frozen=False)

    # Required Fields — Blocking if null
    source: str
    carrier_code: str = Field(..., min_length=MIN_CARRIER_CODE_LENGTH, max_length=MAX_CARRIER_CODE_LENGTH)
    flight_number: str
    origin_iata: str = Field(..., min_length=MIN_IATA_CODE_LENGTH, max_length=MAX_IATA_CODE_LENGTH)
    destination_iata: str = Field(..., min_length=MIN_IATA_CODE_LENGTH, max_length=MAX_IATA_CODE_LENGTH)
    departure_at: datetime
    arrival_at: datetime
    total_amount: Decimal = Field(..., gt=Decimal("0"))
    currency: str

    # Optional Fields — Penalized if null
    base_amount: Decimal | None = None
    tax_amount: Decimal | None = None
    duration: str | None = None
    cabin_class: str | None = None
    fare_basis: str | None = None
    fare_brand: str | None = None
    checked_bags: int | None = None
    carry_on_bags: int | None = None
    refund_allowed: bool | None = None
    change_allowed: bool | None = None

    # Quality Metadata — populated by FlightScoringService
    quality_metadata: QualityMetadata | None = None
    failed_rules: list[str] = Field(default_factory=list)

    @field_validator("carrier_code")
    @classmethod
    def carrier_code_must_be_iata_length(cls, v: str) -> str:
        if len(v) != MIN_CARRIER_CODE_LENGTH:
            raise ValueError("carrier_code must be exactly 2 characters")
        return v

    @field_validator("origin_iata", "destination_iata")
    @classmethod
    def iata_codes_must_be_airport_length(cls, v: str) -> str:
        if len(v) != MIN_IATA_CODE_LENGTH:
            raise ValueError("IATA code must be exactly 3 characters")
        return v
