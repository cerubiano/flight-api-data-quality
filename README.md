# Flight API Data Quality Platform

A data pipeline that ingests, normalizes, and scores the quality of 
flight data returned by multiple API sources before it reaches the 
end customer.

---

## Problem

The Content Integration Team at a travel OTA is responsible for the 
health and reliability of multiple flight API integrations. Inconsistent 
or poor-quality data directly impacts customer trust and revenue.

Three core challenges:
- **Validation:** Ensuring new API integrations meet data integrity standards before going live.
- **Monitoring:** Continuous tracking of production API health to detect quality degradation.
- **Visibility:** Data-driven insights for stakeholders to make informed decisions about provider prioritization.

---

## Architecture
```
Amadeus GET /v2/shopping/flight-offers
Duffel  POST /air/offer_requests
        ↓
    Bronze → Silver → Gold
        ↓
    PostgreSQL
        ↓
    Tableau Public
```

Hexagonal Architecture (Ports & Adapters) combined with Medallion 
Architecture (Bronze → Silver → Gold) to ensure clean separation 
between business logic and infrastructure.

---

## Key Data Quality Metrics

- **Completeness:** Percentage of non-null critical fields (Fare Basis, Baggage).
- **Validity:** Adherence to IATA standards and ISO 8601 formats.
- **Consistency:** Cross-field validation (e.g., Total Amount >= Base Amount).
- **Conformity:** Structural compliance of API responses against defined schemas.

---

## Methodology

This project follows a **Shift-Left Testing** approach — quality 
assurance is defined before any code is written.

- **BDD:** Each pipeline layer is governed by a Spec written in 
Given/When/Then format.
- **Hexagonal Architecture:** Core business logic is fully decoupled 
from external APIs and databases.
- **ISTQB Standards:** Testing strategy applies Boundary Value Analysis, 
Equivalence Partitioning, and Negative Testing.

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Data processing | Pandas + PyArrow |
| Data validation | Pydantic v2 |
| Database | PostgreSQL 16 |
| Dashboard | Tableau Public |
| Version control | Git + GitHub |

---

## Project Structure
```
flight-api-data-quality/
    config/
        routes.yaml
    data/
        bronze/     ← Raw JSON from APIs
        silver/     ← Normalized Parquet
        gold/       ← QA Score Parquet
    src/
        domain/
            models/
            services/
            ports/
            exceptions.py
        adapters/
            providers/
            repositories/
        main.py
    tests/
        conftest.py
    docs/
        PRD.md
        SYSTEM_ARCHITECTURE.md
        specs/
    postman/
```

---

## Documentation

| Document | Description |
|---|---|
| [PRD](docs/PRD.md) | Problem statement, scope, and success criteria |
| [System Architecture](docs/SYSTEM_ARCHITECTURE.md) | Technical design, data flow, and data dictionary |
| [SPEC-001](docs/specs/SPEC-001-bronze-layer.md) | Bronze layer ingestion specification |
| [SPEC-002](docs/specs/SPEC-002-silver-layer.md) | Silver layer normalization specification |
| [SPEC-003](docs/specs/SPEC-003-gold-layer.md) | Gold layer validation and quality scoring specification |

---

## How to Run

### Prerequisites
- Python 3.12
- PostgreSQL 16
- Amadeus API credentials
- Duffel API credentials

### Setup
```bash
git clone https://github.com/cerubiano/flight-api-data-quality
cd flight-api-data-quality
pip install -r requirements.txt
cp .env.example .env
# Add your credentials to .env
```

### Run
```bash
python src/main.py
```

---

## Results

### Pipeline Execution Summary

5 routes validated — 396 flight offers processed across Amadeus and Duffel.

| Route | Amadeus | Duffel | Total |
|---|---|---|---|
| YUL → LAX | 5 | 6 | 11 |
| YUL → YYZ | 5 | 42 | 47 |
| YYZ → LHR | 5 | 153 | 158 |
| YVR → CDG | 5 | 120 | 125 |
| YUL → CUN | 5 | 50 | 55 |
| **Total** | **25** | **371** | **396** |

### Key Quality Findings

| Source | Avg Score | Valid | Invalid |
|---|---|---|---|
| Amadeus (GDS) | ~0.10 | 0 | 25 |
| Duffel (NDC) | ~0.55 | 206 | 165 |
| **Total** | **0.49** | **206** | **190** |

**Finding 1 — Amadeus returns no production-ready flights**
All 25 Amadeus offers scored below 0.5 across all routes. 
Primary causes: `refund_allowed` and `change_allowed` are 
structurally null in all Amadeus responses, and departure 
dates returned by the sandbox API are in the past.

**Finding 2 — Duffel has significantly more inventory**
Duffel returns up to 153 offers per route (YYZ→LHR) versus 
Amadeus which is capped at 5. NDC aggregators provide broader 
access to airline inventory than traditional GDS.

**Finding 3 — Duffel returns null flight_number on some routes**
Routes YUL→YYZ, YYZ→LHR and YVR→CDG returned offers with 
null flight_number. The pipeline captures and penalizes 
these with a blocking score of 0.0.

**Finding 4 — Timezone bug detected and resolved**
Amadeus returns timezone-aware datetimes. Python's 
datetime.now() is timezone-naive. This caused a comparison 
failure in DeparturePastRule — fixed by using 
datetime.now(timezone.utc).

### Dashboard
[Flight API Data Quality Platform — Tableau Public](https://public.tableau.com/app/profile/carlos.rubiano3854/viz/FlightAPIDataQualityPlatform/FlightAPIDataQuality?publish=yes)

---

## Author

Carlos Eduardo Rubiano Robles  
[LinkedIn](https://www.linkedin.com/in/cerubiano/) · [GitHub](https://github.com/cerubiano)