# SPEC-001: Bronze Layer — Raw Data Ingestion

## Overview
Store raw API responses exactly as received from each source.
No transformations. No modifications.

## Acceptance Criteria

**Given:** A flight search request YUL→LAX 2026-04-15 1 adult economy
**When:** Amadeus and Duffel APIs are called
**Then:**
- Raw JSON from Amadeus is saved to `/data/bronze/amadeus/`
- Raw JSON from Duffel is saved to `/data/bronze/duffel/`
- Files are named with timestamp: `YYYYMMDD_HHMMSS_source.json`
- No field is modified, added, or removed
- Ingestion timestamp is logged

## File Naming Convention
```
bronze/
    amadeus/
        20260310_154410_amadeus.json
    duffel/
        20260310_154410_duffel.json
```

## Failure Criteria
- API returns error → log error, do not save empty file
- API timeout → log timeout, retry once