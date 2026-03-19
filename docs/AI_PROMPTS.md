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
**promp**
Read domain.mdc and python.mdc. 
Implement src/domain/exceptions.py exactly as defined 
in domain.mdc — Exceptions section.