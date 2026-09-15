"""
Patient factory for test data generation
Best practice 2026: Factory pattern with Faker
"""

from datetime import date, timedelta

import factory
from factory import fuzzy

from src.pharmaviyum.models.patients import (
    Patient,
    PatientAllergy,
    PatientCondition,
    PatientInsurance,
)


class PatientFactory(factory.async_sqlalchemy.AsyncSQLAlchemyFactory):
    """Factory for creating test patients"""

    class Meta:
        model = Patient
        exclude = ["first_name_gen", "last_name_gen"]

    # Generate names
    first_name_gen = factory.Faker("first_name")
    last_name_gen = factory.Faker("last_name")

    # Fields
    first_name = factory.LazyAttribute(lambda o: o.first_name_gen)
    last_name = factory.LazyAttribute(lambda o: o.last_name_gen)
    full_name = factory.LazyAttribute(lambda o: f"{o.first_name} {o.last_name}")
    phone = factory.LazyAttribute(
        lambda o: f"+84{factory.Faker('numerify', text='#########').evaluate(None, None, {'locale': None})}"
    )
    email = factory.LazyAttribute(
        lambda o: f"{o.first_name.lower()}.{o.last_name.lower()}@example.com"
    )

    # Demographics
    date_of_birth = factory.LazyFunction(
        lambda: date.today()
        - timedelta(
            days=factory.Faker("random_int", min=18 * 365, max=80 * 365).evaluate(
                None, None, {"locale": None}
            )
        )
    )
    gender = fuzzy.FuzzyChoice(["male", "female", "other"])

    # Address
    address = factory.Faker("address")
    city = factory.Faker("city")
    country = fuzzy.FuzzyChoice(["VN", "TH", "MY", "ID", "PH", "SG"])
    postal_code = factory.Faker("postcode")

    # Medical
    blood_type = fuzzy.FuzzyChoice(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
    allergies_notes = factory.Faker("sentence")
    chronic_conditions = factory.Faker("sentence")

    # Preferences
    preferred_language = fuzzy.FuzzyChoice(["vi", "en", "zh", "ko", "ms", "id", "th"])
    preferred_notification_channel = fuzzy.FuzzyChoice(
        ["zalo", "line", "whatsapp", "messenger"]
    )

    # Loyalty
    loyalty_tier = fuzzy.FuzzyChoice(["Bronze", "Silver", "Gold", "Platinum"])
    loyalty_points = factory.LazyFunction(
        lambda: factory.Faker("random_int", min=0, max=10000).evaluate(
            None, None, {"locale": None}
        )
    )

    # Statistics
    total_purchases = factory.LazyFunction(
        lambda: factory.Faker("random_int", min=0, max=100000000).evaluate(
            None, None, {"locale": None}
        )
    )
    visit_count = factory.LazyFunction(
        lambda: factory.Faker("random_int", min=0, max=100).evaluate(
            None, None, {"locale": None}
        )
    )
    last_visit_date = factory.LazyFunction(
        lambda: date.today()
        - timedelta(
            days=factory.Faker("random_int", min=0, max=365).evaluate(
                None, None, {"locale": None}
            )
        )
    )

    # Metadata
    is_active = True
    notes = factory.Faker("paragraph")


class PatientAllergyFactory(factory.async_sqlalchemy.AsyncSQLAlchemyFactory):
    """Factory for creating test patient allergies"""

    class Meta:
        model = PatientAllergy

    patient = factory.SubFactory(PatientFactory)
    allergen_type = fuzzy.FuzzyChoice(["drug", "food", "environmental", "other"])
    allergen_name = fuzzy.FuzzyChoice(
        [
            "Penicillin",
            "Aspirin",
            "Ibuprofen",
            "Sulfa drugs",
            "Peanuts",
            "Shellfish",
            "Eggs",
            "Milk",
            "Pollen",
            "Dust mites",
            "Mold",
            "Pet dander",
        ]
    )
    severity = fuzzy.FuzzyChoice(["mild", "moderate", "severe", "life-threatening"])
    reaction = factory.Faker("sentence")
    is_verified = fuzzy.FuzzyChoice([True, False])


class PatientConditionFactory(factory.async_sqlalchemy.AsyncSQLAlchemyFactory):
    """Factory for creating test patient conditions"""

    class Meta:
        model = PatientCondition

    patient = factory.SubFactory(PatientFactory)
    condition_name = fuzzy.FuzzyChoice(
        [
            "Hypertension",
            "Diabetes Type 2",
            "Asthma",
            "Arthritis",
            "Depression",
            "Anxiety",
            "Migraine",
            "Epilepsy",
        ]
    )
    icd10_code = fuzzy.FuzzyChoice(
        [
            "I10",
            "E11",
            "J45",
            "M15",
            "F32",
            "F41",
            "G43",
            "G40",
        ]
    )
    severity = fuzzy.FuzzyChoice(["mild", "moderate", "severe"])
    is_chronic = True
    status = fuzzy.FuzzyChoice(["active", "chronic", "resolved"])


class PatientInsuranceFactory(factory.async_sqlalchemy.AsyncSQLAlchemyFactory):
    """Factory for creating test patient insurances"""

    class Meta:
        model = PatientInsurance

    patient = factory.SubFactory(PatientFactory)
    provider_name = fuzzy.FuzzyChoice(
        [
            "Bao Viet Insurance",
            "PVI Insurance",
            "Bao Minh Insurance",
            "Manulife",
            "Prudential",
            "AIA",
        ]
    )
    policy_number = factory.LazyAttribute(
        lambda o: f"POL{factory.Faker('numerify', text='########').evaluate(None, None, {'locale': None})}"
    )
    coverage_start = factory.LazyFunction(
        lambda: date.today()
        - timedelta(
            days=factory.Faker("random_int", min=0, max=365).evaluate(
                None, None, {"locale": None}
            )
        )
    )
    coverage_end = factory.LazyFunction(
        lambda: date.today()
        + timedelta(
            days=factory.Faker("random_int", min=30, max=365).evaluate(
                None, None, {"locale": None}
            )
        )
    )
    is_primary = True
    is_active = True
