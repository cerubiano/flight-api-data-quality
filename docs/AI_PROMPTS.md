# AI-Assisted Development Log

## Methodology
This project was built using Cursor Agent in Plan mode.
Each prompt was designed to respect the architecture defined 
in .cursor/rules/ and docs/ before any code was generated.

## Prompt Log

### Phase 1 — Project Structure
**Prompt:**
Read all files in .cursor/rules/ and docs/ and summarize:
1. The architecture pattern used
2. The folder structure you will create
3. The SOLID principles that apply
Do not create anything yet.

Create the complete project folder structure with all 
necessary __init__.py files as defined in project.mdc.
Do not write any implementation code.

### step code:
1. exceptions.py          ← base de errores
2. flight_model.py        ← schema Pydantic
3. provider_port.py       ← contrato de proveedores
4. repository_port.py     ← contrato de repositorios
5. flight_validation_service.py  ← reglas de calidad
6. flight_scoring_service.py     ← scoring
7. amadeus_adapter.py     ← integración Amadeus
8. duffel_adapter.py      ← integración Duffel
9. file_repository.py     ← Bronze/Silver/Gold local
10. postgres_repository.py ← PostgreSQL
11. main.py               ← orquestador

### Phase 2 — Domain Models
**exceptions.py**
Read domain.mdc and python.mdc. 
Implement src/domain/exceptions.py exactly as defined 
in domain.mdc — Exceptions section.

**flight_model.py**
Read domain.mdc and python.mdc.
Implement src/domain/models/flight_model.py with:
- FlightModel using Pydantic v2
- QualityMetadata nested model
- All fields defined in domain.mdc — Required Fields and Optional Fields sections
- Field validators for carrier_code, origin_iata, destination_iata
- No implementation logic — only the model definition

### Lesson Learned — Be explicit about class structure
Prompt: "nested model" caused Cursor to create QualityMetadata 
as an inner class. Correct term: "separate top-level class 
in the same file".

Refactor src/domain/models/flight_model.py:
Move QualityMetadata outside of FlightModel as a separate 
top-level class in the same file. FlightModel should reference 
QualityMetadata as an external type, not define it internally.
Keep all other code exactly as is.

**provider_port.py**
Read domain.mdc and python.mdc.
Implement src/domain/ports/provider_port.py with:
- Abstract base class FlightProviderPort
- Single abstract method search_flights as defined in domain.mdc
- Google style docstring
- No implementation — only the contract

**repository_port.py**
Read domain.mdc and python.mdc.
Implement src/domain/ports/repository_port.py with:
- Abstract base class RepositoryPort
- Four abstract methods as defined in domain.mdc: 
  save_bronze, save_silver, save_gold, save_results
- Google style docstrings on each method
- Import Path from pathlib
- No implementation — only the contract