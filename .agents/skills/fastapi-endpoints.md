# FastAPI Endpoints Skill

## Endpoint Pattern
```python
from fastapi import APIRouter, Depends
from app.shared.core.database import get_session

router = APIRouter(prefix="/patients", tags=["patients"])

@router.post("/", response_model=ResponseEnvelope[PatientResponse])
async def create_patient(
    data: PatientCreate,
    service: PatientService = Depends(get_service),
):
    patient = await service.create_patient(data)
    return ResponseEnvelope.success_response(data=PatientResponse.model_validate(patient))
```

## Rules
1. Use dependency injection for services
2. Return ResponseEnvelope for consistency
3. Use proper HTTP status codes
4. Add docstrings for OpenAPI
