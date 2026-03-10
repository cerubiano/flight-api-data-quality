# SPEC-003: Gold Layer — Data Quality Validation

## Overview
Apply quality rules field by field to normalized Silver data.
Generate a quality score per field, per airline, and per source.

## Quality Rules

### Price Rules
| Rule ID | Field | Condition | Error Code |
|---|---|---|---|
| PR-001 | `total_amount` | > 0 | PRICE_ZERO |
| PR-002 | `currency` | Valid ISO 4217 code | CURRENCY_INVALID |
| PR-003 | `total_amount` | = `base_amount` + `tax_amount` | PRICE_MISMATCH |

### Schedule Rules
| Rule ID | Field | Condition | Error Code |
|---|---|---|---|
| SC-001 | `carrier_code` | Exactly 2 characters | CARRIER_INVALID |
| SC-002 | `departure_at` | Is future datetime | DEPARTURE_PAST |
| SC-003 | `arrival_at` | > `departure_at` | ARRIVAL_BEFORE_DEPARTURE |
| SC-004 | `origin_iata` | Exactly 3 characters | ORIGIN_INVALID |
| SC-005 | `destination_iata` | Exactly 3 characters | DESTINATION_INVALID |

### Baggage Rules
| Rule ID | Field | Condition | Error Code |
|---|---|---|---|
| BG-001 | `checked_bags` | Not null | CHECKED_BAGS_NULL |
| BG-002 | `carry_on_bags` | Not null | CARRY_ON_NULL |
| BG-003 | `checked_bags` | >= 0 | CHECKED_BAGS_NEGATIVE |

### Conditions Rules
| Rule ID | Field | Condition | Error Code |
|---|---|---|---|
| CD-001 | `refund_allowed` | Not null | REFUND_POLICY_MISSING |
| CD-002 | `change_allowed` | Not null | CHANGE_POLICY_MISSING |

## Quality Score Calculation
```
field_score = passed_rules / total_rules * 100
source_score = passed_fields / total_fields * 100
```

## Output per Source
```json
{
  "source": "amadeus",
  "carrier_code": "AC",
  "validation_timestamp": "2026-03-10T15:54:10Z",
  "scores": {
    "price": 100,
    "schedule": 100,
    "baggage": 50,
    "conditions": 0,
    "overall": 75
  },
  "errors": [
    {"rule_id": "BG-001", "field": "checked_bags", "error_code": "CHECKED_BAGS_NULL"},
    {"rule_id": "CD-001", "field": "refund_allowed", "error_code": "REFUND_POLICY_MISSING"},
    {"rule_id": "CD-002", "field": "change_allowed", "error_code": "CHANGE_POLICY_MISSING"}
  ]
}
```

## Acceptance Criteria
- Score calculated per field group and overall
- Every failed rule logged with rule_id and error_code
- Output saved to MySQL table `dq_results`
- Output saved as parquet to `/data/gold/`