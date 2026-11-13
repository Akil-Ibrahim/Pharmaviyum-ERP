"""API v1 endpoints package"""

from .feature_flags import router as feature_flags_router
from .patients import router as patients_router
from .prescriptions import router as prescriptions_router

__all__ = [
    "patients_router",
    "prescriptions_router",
    "feature_flags_router",
]
