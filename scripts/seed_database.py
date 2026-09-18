"""Seed stage 1: 20 synthetic English-language pharmacy customers."""

import asyncio
import random
from datetime import datetime, timedelta

from sqlalchemy import select

from src.pharmaviyum.core.database import AsyncSessionLocal
from src.pharmaviyum.models import Patient, Prescription
from src.pharmaviyum.models.patients import PatientPurchase

random.seed(20260918)

# Product master data follows WHO INN naming conventions; package/batch identifiers below are synthetic demo data.

CUSTOMERS = [
    ("James", "Anderson", "Chronic Care", "New York", "US"),
    ("Emily", "Carter", "Wellness", "London", "GB"),
    ("Michael", "Brown", "Cardiovascular", "Toronto", "CA"),
    ("Sophia", "Wilson", "Skincare", "Sydney", "AU"),
    ("Daniel", "Miller", "Diabetes Care", "New York", "US"),
    ("Olivia", "Taylor", "Women's Health", "London", "GB"),
    ("William", "Moore", "OTC / Self-care", "Toronto", "CA"),
    ("Ava", "Jackson", "Dermatology", "Sydney", "AU"),
    ("Benjamin", "Martin", "Elderly Care", "New York", "US"),
    ("Isabella", "Thompson", "Vitamins & Supplements", "London", "GB"),
    ("Henry", "White", "Respiratory Care", "Toronto", "CA"),
    ("Mia", "Harris", "Cosmetics", "Sydney", "AU"),
    ("Alexander", "Clark", "Family Care", "New York", "US"),
    ("Charlotte", "Lewis", "Allergy Care", "London", "GB"),
    ("Ethan", "Walker", "Sports & Wellness", "Toronto", "CA"),
    ("Amelia", "Hall", "Medical Devices", "Sydney", "AU"),
    ("Noah", "Allen", "Chronic Care", "New York", "US"),
    ("Grace", "Young", "Skincare", "London", "GB"),
    ("Lucas", "King", "OTC / Self-care", "Toronto", "CA"),
    ("Ella", "Wright", "Wellness", "Sydney", "AU"),
]

PURCHASE_CATEGORIES = [
    ("OTC Medicine", "Paracetamol 500 mg", 4.20, False),
    ("OTC Medicine", "Ibuprofen 200 mg", 5.10, False),
    ("OTC Medicine", "Cetirizine 10 mg", 6.30, False),
    ("Vitamins & Supplements", "Vitamin D3 1000 IU", 11.50, False),
    ("Vitamins & Supplements", "Magnesium 250 mg", 12.90, False),
    ("Cosmetics", "Facial Moisturizer 50 ml", 19.90, False),
    ("Cosmetics", "Gentle Facial Cleanser 200 ml", 13.50, False),
    ("Cosmetics", "Sunscreen SPF 50 50 ml", 22.00, False),
    ("Medical Devices", "Blood Pressure Monitor", 39.90, False),
    ("Medical Devices", "Digital Thermometer", 12.00, False),
    ("Medical Supplies", "Elastic Support Bandage", 6.50, False),
    ("Prescription Medicine", "Metformin 500 mg", 8.50, True),
    ("Prescription Medicine", "Amlodipine 5 mg", 6.90, True),
    ("Prescription Medicine", "Atorvastatin 20 mg", 9.80, True),
]


async def seed_patients() -> None:
    async with AsyncSessionLocal() as session:
        created = 0
        for index, (first, last, category, city, country) in enumerate(CUSTOMERS, 1):
            external_id = f"demo-patient-{index:03d}"
            patient = await session.scalar(
                select(Patient).where(Patient.external_id == external_id)
            )
            if patient is None:
                patient = Patient(
                    external_id=external_id,
                    first_name=first,
                    last_name=last,
                    full_name=f"{first} {last}",
                    phone=f"+1555010{index:04d}",
                    email=f"demo-patient-{index:03d}@example.com",
                    city=city,
                    country=country,
                    preferred_language="en",
                    preferred_notification_channel="email",
                    customer_category=category,
                    loyalty_tier=random.choice(["Bronze", "Silver", "Gold"]),
                    loyalty_points=random.randint(50, 900),
                    notes="Synthetic demonstration customer.",
                )
                session.add(patient)
                await session.flush()
                created += 1

            for visit in range(1, 3 + index % 2):
                receipt = f"DEMO-{index:03d}-{visit:02d}"
                for item_category, name, price, rx_required in random.sample(
                    PURCHASE_CATEGORIES, k=3
                ):
                    exists = await session.scalar(
                        select(PatientPurchase).where(
                            PatientPurchase.patient_id == patient.id,
                            PatientPurchase.receipt_number == receipt,
                            PatientPurchase.category == item_category,
                            PatientPurchase.product_id.is_(None),
                        )
                    )
                    if exists:
                        continue
                    session.add(
                        PatientPurchase(
                            patient_id=patient.id,
                            receipt_number=receipt,
                            category=item_category,
                            quantity=random.randint(1, 3),
                            unit_price=price,
                            prescription_required=rx_required,
                            purchased_at=datetime.utcnow()
                            - timedelta(days=random.randint(1, 120)),
                        )
                    )
            if index % 3 == 0:
                prescription_number = f"DEMO-RX-{index:03d}"
                existing_rx = await session.scalar(
                    select(Prescription).where(
                        Prescription.prescription_number == prescription_number
                    )
                )
                if existing_rx is None:
                    session.add(
                        Prescription(
                            patient_id=patient.id,
                            prescription_number=prescription_number,
                            dosage="As directed by prescriber",
                            instructions="Synthetic demonstration prescription.",
                            status="active",
                            issued_at=datetime.utcnow() - timedelta(days=30),
                            expires_at=datetime.utcnow() + timedelta(days=60),
                        )
                    )

            patient.visit_count = 2 + index % 2
            patient.last_visit_date = datetime.utcnow() - timedelta(days=index % 14)

        await session.commit()
        print(f"Stage 1 complete: {len(CUSTOMERS)} synthetic patients; newly created: {created}.")


if __name__ == "__main__":
    asyncio.run(seed_patients())
