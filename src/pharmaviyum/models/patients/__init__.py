"""Patient domain models."""

from src.pharmaviyum.models.patients.consultation import Consultation
from src.pharmaviyum.models.patients.patient import Patient
from src.pharmaviyum.models.patients.patient_allergy import PatientAllergy
from src.pharmaviyum.models.patients.patient_condition import PatientCondition
from src.pharmaviyum.models.patients.patient_insurance import PatientInsurance

__all__ = [
    "Patient",
    "PatientAllergy",
    "PatientCondition",
    "PatientInsurance",
    "Consultation",
]
