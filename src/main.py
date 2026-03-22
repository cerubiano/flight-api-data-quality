"""Flight API Data Quality Platform — Pipeline Orchestrator.

Runs the complete pipeline:
1. Extract flights from Amadeus and Duffel
2. Save raw responses to Bronze layer
3. Validate flights against quality rules
4. Score flights and populate quality metadata
5. Save normalized flights to Silver layer
6. Save scored flights to Gold layer
7. Persist results to PostgreSQL
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from src.adapters.providers.amadeus_adapter import AmadeusAdapter
from src.adapters.providers.duffel_adapter import DuffelAdapter
from src.adapters.repositories.file_repository import FileRepository
from src.adapters.repositories.postgres_repository import PostgresRepository
from src.domain.services.flight_scoring_service import FlightScoringService
from src.domain.services.flight_validation_service import (
    FlightValidationService,
    VALIDATION_RULES,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

ORIGIN = os.getenv("ORIGIN", "YUL")
DESTINATION = os.getenv("DESTINATION", "LAX")
DEPARTURE_DATE = os.getenv("DEPARTURE_DATE", "2026-04-15")
ADULTS = int(os.getenv("ADULTS", "1"))
DATA_PATH = Path("data")


def main() -> None:
    """Run the Flight API Data Quality pipeline."""

    logger.info("Starting Flight API Data Quality Pipeline")
    logger.info("Route: %s → %s on %s", ORIGIN, DESTINATION, DEPARTURE_DATE)

    # --- Initialize adapters ---
    amadeus = AmadeusAdapter(
        amadeus_api_key=os.getenv("AMADEUS_API_KEY", ""),
        amadeus_api_secret=os.getenv("AMADEUS_API_SECRET", ""),
    )
    duffel = DuffelAdapter(
        access_token=os.getenv("DUFFEL_ACCESS_TOKEN", ""),
    )
    file_repo = FileRepository(base_path=DATA_PATH)
    postgres_repo = PostgresRepository(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "flight_dq"),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", ""),
    )
    validator = FlightValidationService(rules=VALIDATION_RULES)
    scorer = FlightScoringService()

    all_flights = []

    # --- Step 1: Extract from Amadeus ---
    logger.info("Extracting flights from Amadeus...")
    try:
        amadeus_raw = amadeus._get_token()
        import requests
        response = requests.get(
            "https://test.api.amadeus.com/v2/shopping/flight-offers",
            headers={"Authorization": f"Bearer {amadeus_raw}"},
            params={
                "originLocationCode": ORIGIN,
                "destinationLocationCode": DESTINATION,
                "departureDate": DEPARTURE_DATE,
                "adults": ADULTS,
                "max": 5,
            },
            timeout=30,
        )
        response.raise_for_status()
        amadeus_raw_response = response.json()
        file_repo.save_bronze(amadeus_raw_response, "amadeus")
        amadeus_flights = amadeus.search_flights(ORIGIN, DESTINATION, DEPARTURE_DATE, ADULTS)
        logger.info("Amadeus: %d flights found", len(amadeus_flights))
        all_flights.extend(amadeus_flights)
    except Exception as e:
        logger.error("Amadeus extraction failed: %s", e)

    # --- Step 2: Extract from Duffel ---
    logger.info("Extracting flights from Duffel...")
    try:
        import requests
        response = requests.post(
            "https://api.duffel.com/air/offer_requests",
            headers={
                "Authorization": f"Bearer {os.getenv('DUFFEL_ACCESS_TOKEN', '')}",
                "Content-Type": "application/json",
                "Duffel-Version": "v2",
            },
            json={
                "data": {
                    "slices": [{"origin": ORIGIN, "destination": DESTINATION, "departure_date": DEPARTURE_DATE}],
                    "passengers": [{"type": "adult"} for _ in range(ADULTS)],
                    "cabin_class": "economy",
                }
            },
            timeout=30,
        )
        response.raise_for_status()
        duffel_raw_response = response.json()
        file_repo.save_bronze(duffel_raw_response, "duffel")
        duffel_flights = duffel.search_flights(ORIGIN, DESTINATION, DEPARTURE_DATE, ADULTS)
        logger.info("Duffel: %d flights found", len(duffel_flights))
        all_flights.extend(duffel_flights)
    except Exception as e:
        logger.error("Duffel extraction failed: %s", e)

    if not all_flights:
        logger.error("No flights found — pipeline aborted")
        return

    # --- Step 3: Validate ---
    logger.info("Validating %d flights...", len(all_flights))
    validated = [validator.validate(flight) for flight in all_flights]

    # --- Step 4: Score ---
    logger.info("Scoring flights...")
    scored = [scorer.score(flight) for flight in validated]

    # --- Step 5: Save Silver ---
    silver_path = file_repo.save_silver(scored)
    logger.info("Silver saved: %s", silver_path)

    # --- Step 6: Save Gold ---
    gold_path = file_repo.save_gold(scored)
    logger.info("Gold saved: %s", gold_path)

    # --- Step 7: Save to PostgreSQL ---
    postgres_repo.save_results(scored)
    logger.info("Results saved to PostgreSQL")

    # --- Summary ---
    valid = sum(1 for f in scored if f.quality_metadata and f.quality_metadata.is_valid_flight)
    invalid = len(scored) - valid
    avg_score = sum(f.quality_metadata.dq_score for f in scored if f.quality_metadata) / len(scored)

    logger.info("Pipeline complete — %d flights processed", len(scored))
    logger.info("Valid: %d | Invalid: %d | Avg score: %.2f", valid, invalid, avg_score)


if __name__ == "__main__":
    main()