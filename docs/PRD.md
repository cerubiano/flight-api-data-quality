# PRD — Flight API Data Quality Platform

## 1. Overview
A data pipeline that ingests, normalizes, and scores the quality of 
flight data returned by multiple API sources through the flight search 
endpoint. The platform ensures only validated, Gold-standard data 
reaches the end customer.

---

## 2. Problem Statement

The Content Integration Team at a travel OTA is responsible for the 
health and reliability of multiple flight API integrations. Inconsistent 
or poor-quality data directly impacts customer trust and revenue.

Three core challenges:

- **Validation:** Ensuring new API integrations meet data integrity 
standards before going live.
- **Monitoring:** Continuous tracking of production API health to detect 
quality degradation.
- **Visibility:** Data-driven insights for stakeholders to make informed 
decisions about provider prioritization.

---

## 3. Scope

### In Scope

**Flight Search Endpoint:**

| Source | Endpoint |
|---|---|
| Amadeus | GET /v2/shopping/flight-offers |
| Duffel | POST /air/offer_requests |

**Data validated per offer:**

| Dimension | Fields |
|---|---|
| Price | base_amount, tax_amount, total_amount, currency |
| Schedule | origin_iata, destination_iata, departure_at, arrival_at, duration |
| Baggage | checked_bags, carry_on_bags |
| Fare | fare_basis, fare_brand, cabin_class |
| Conditions | refund_allowed, change_allowed |

**Pipeline:**
- Data extraction from Amadeus and Duffel
- Data normalization to a standard schema
- Field-by-field data quality validation
- Quality score per dimension, per airline, and per source
- Dashboard to present results

### Out of Scope
- Flight Price endpoint
- Baggage as separate endpoint
- Seat maps
- Branded fares
- Post-booking services
- PNR management
- Hotel integrations
- Real-time validation during customer search
- Booking and ticketing

---

## 4. Users

| User | Need |
|---|---|
| QA Analyst | Validate a new integration before production |
| Integration Engineer | Monitor existing integrations health |
| Team Lead | Data-driven decisions on integration status |

---

## 5. Core Features

**F1 — Data Extraction**
Connect to Amadeus and Duffel flight search endpoints and extract raw 
responses using a defined set of test routes. Raw responses stored 
immutably in Bronze layer.

**F2 — Data Normalization**
Transform raw responses from each source into a single standard schema 
regardless of source structure. Resolves structural differences between 
GDS (Amadeus) and NDC (Duffel) responses. Output stored in Silver layer.

**F3 — Data Validation**
Apply quality rules field by field using four dimensions:
- **Completeness:** Non-null critical fields (Fare Basis, Baggage)
- **Validity:** IATA standards and ISO 8601 format compliance
- **Consistency:** Cross-field validation (e.g., Total Amount >= Base Amount)
- **Conformity:** Structural compliance against defined schemas

**F4 — Quality Scoring**
Generate a quality score per field, per dimension, per airline, and 
per integration source. Output stored in Gold layer.

**F5 — Reporting Dashboard**
Visualize quality scores and integration health in an interactive 
Tableau Public dashboard. Connected to PostgreSQL for real-time querying.

---

## 6. Success Criteria

- Platform validates data from Amadeus and Duffel
- Flight search endpoint validated per integration
- Quality score generated per Completeness, Validity, Consistency, and Conformity dimensions
- Quality score generated per airline, per dimension, and per field
- Dashboard publicly accessible via Tableau Public URL
- All quality rules covered by automated tests
- Code documented and reproducible from README