"""
Pharmaviyum CRM Models Package
All database models for the CRM system
"""
from src.pharmaviyum.models.patients.patient import Patient
from src.pharmaviyum.models.patients.patient_allergy import PatientAllergy
from src.pharmaviyum.models.patients.patient_condition import PatientCondition
from src.pharmaviyum.models.patients.patient_insurance import PatientInsurance
from src.pharmaviyum.models.patients.consultation import Consultation

__all__ = [
    "Patient",
    "PatientAllergy",
    "PatientCondition",
    "PatientInsurance",
    "Consultation",
]
