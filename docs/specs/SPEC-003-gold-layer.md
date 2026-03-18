# SPEC-003: Gold Layer — Validation & Quality Scoring

## 1. Objective

Define the business rules and technical acceptance criteria to score 
the quality of a normalized flight offer. The output is a weighted 
Quality Score that enables comparison between providers and automated 
filtering of unreliable data.

---

## 2. Scoring Logic

The score is a decimal value between 0.0 and 1.0.

Every record starts with a perfect score of 1.0. Cumulative penalties 
are applied based on the severity of each failed rule.

### 2.1 Severity Matrix

| Dimension | Validation Rule | Severity | Penalty |
|---|---|---|---|
| Completeness | `total_amount` is null or <= 0 | Blocking | -1.0 |
| Completeness | `flight_number` or `carrier_code` is null | Blocking | -1.0 |
| Consistency | `base_amount` + `tax_amount` != `total_amount` | Critical | -0.5 |
| Validity | `arrival_at` <= `departure_at` | Critical | -0.5 |
| Completeness | `fare_basis` or `fare_brand` is null | Medium | -0.2 |
| Completeness | `checked_bags` or `carry_on_bags` is null | Medium | -0.2 |
| Validity | `origin_iata` or `destination_iata` != 3 characters | High | -0.4 |
| Conformity | `carrier_code` not in IATA airline registry | High | -0.4 |
| Conformity | `origin_iata` not in IATA airport registry | High | -0.4 |
| Conformity | `destination_iata` not in IATA airport registry | High | -0.4 |

### 2.2 Score Interpretation

| Score | Status | Meaning |
|---|---|---|
| 1.0 | ✅ Perfect | All rules passed |
| 0.8 - 0.9 | ✅ Acceptable | Minor issues — safe for production |
| 0.5 - 0.7 | ⚠️ Review | Significant issues — requires QA review |
| < 0.5 | ❌ Blocked | Critical failures — not safe for production |

---

## 3. Acceptance Criteria (BDD — Gherkin Format)

These scenarios must be covered by tests in 
`tests/test_flight_scoring_service.py`.

---

**Scenario 1: Blocking — Null Price**
```gherkin
Given a normalized flight offer from the Silver layer
When the total_amount field is null
Then is_valid_flight must be False
And dq_score must be 0.0
And failed_rules must include "PRICE_NULL"
```

---

**Scenario 2: Critical — Price Inconsistency**
```gherkin
Given a normalized flight offer from the Silver layer
When base_amount is 200.00
And tax_amount is 50.00
And total_amount reported by the API is 300.00
Then is_price_consistent must be False
And dq_score must be 0.5
And failed_rules must include "PRICE_MISMATCH"
```

---

**Scenario 3: Medium — Incomplete Flight Attributes**
```gherkin
Given a normalized flight offer with all blocking fields present
When fare_basis is null
And checked_bags is null
Then dq_score must be 0.6 (1.0 - 0.2 - 0.2)
And failed_rules must include "FARE_BASIS_NULL"
And failed_rules must include "CHECKED_BAGS_NULL"
```

---

**Scenario 4: Perfect Score**
```gherkin
Given a normalized flight offer from the Silver layer
When all fields are present, valid, and consistent
Then dq_score must be 1.0
And is_valid_flight must be True
And failed_rules must be empty
```

---

**Scenario 5: Conformity — Invalid IATA Code**
```gherkin
Given a normalized flight offer from the Silver layer
When origin_iata is "YUUL" (4 characters instead of 3)
Then dq_score must be 0.6 (1.0 - 0.4)
And failed_rules must include "ORIGIN_INVALID"
```

---

## 4. Output Structure — Gold Layer

The scoring service extends the Silver model by adding a 
`quality_metadata` object:
```json
{
  "source": "amadeus",
  "carrier_code": "AC",
  "flight_number": "775",
  "origin_iata": "YUL",
  "destination_iata": "LAX",
  "departure_at": "2026-04-15T08:35:00",
  "total_amount": 178.47,
  "currency": "EUR",
  "checked_bags": 0,
  "carry_on_bags": 0,
  "fare_basis": "GNA4A2BA",
  "refund_allowed": null,
  "change_allowed": null,
  "quality_metadata": {
    "dq_score": 0.6,
    "is_valid_flight": false,
    "failed_rules": [
      "REFUND_POLICY_MISSING",
      "CHANGE_POLICY_MISSING"
    ],
    "processed_at": "2026-03-10T15:54:10Z"
  }
}
```

---

## 5. Acceptance Criteria

- Score calculated as decimal between 0.0 and 1.0
- Penalties applied cumulatively — minimum score is 0.0
- `is_valid_flight` is False when `dq_score` < 0.5
- Every failed rule logged in `failed_rules` list
- `quality_metadata` object added to every Silver record
- Output saved as parquet to `data/gold/`
- Validation results persisted to PostgreSQL table `dq_results`
- All 5 BDD scenarios covered by automated tests
