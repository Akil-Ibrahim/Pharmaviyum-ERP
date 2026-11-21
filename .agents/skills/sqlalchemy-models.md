# SQLAlchemy Models Skill

## Project Context
Modular monolith with domain-driven modules. Each module owns its data.

## Model Pattern
```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from src.pharmaviyum.database import Base

class Patient(Base):
    __tablename__ = "patients"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

## Rules
1. Use Mapped[] type hints
2. Add indexes for queried columns
3. Module-internal relationships only (no cross-module FKs)
4. Always include created_at/updated_at
