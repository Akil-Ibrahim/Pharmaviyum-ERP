"""
Database seeding with realistic Vietnamese data.
Uses Faker with Vietnamese locale.
Medication names in English (international standard).
"""
import asyncio
import random
from faker import Faker

fake = Faker('vi_VN')

MEDICATIONS = [
    {'name': 'Paracetamol 500mg', 'dosage': '1 tablet', 'frequency': '3 times daily'},
    {'name': 'Amoxicillin 500mg', 'dosage': '1 tablet', 'frequency': '3 times daily'},
    {'name': 'Metformin 850mg', 'dosage': '1 tablet', 'frequency': '2 times daily'},
    {'name': 'Amlodipine 5mg', 'dosage': '1 tablet', 'frequency': '1 time daily'},
    {'name': 'Omeprazole 20mg', 'dosage': '1 tablet', 'frequency': '1 time daily'},
]

VIETNAMESE_CITIES = [
    'Ho Chi Minh', 'Hanoi', 'Da Nang', 'Hai Phong', 'Can Tho', 'Nha Trang',
]


async def seed_patients(count: int = 100):
    """Generate realistic Vietnamese patients."""
    from backend.app.shared.core.database import async_session_factory
    from backend.app.modules.patients.models import Patient
    
    async with async_session_factory() as session:
        for _ in range(count):
            patient = Patient(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                full_name=None,
                phone=f"+84{random.randint(100000000, 999999999)}",
                email=fake.email(),
                city=random.choice(VIETNAMESE_CITIES),
                country='VN',
                preferred_language='vi',
                loyalty_tier=random.choices(
                    ['Bronze', 'Silver', 'Gold', 'Platinum'],
                    weights=[0.50, 0.30, 0.15, 0.05]
                )[0],
                loyalty_points=random.randint(0, 15000),
                total_purchases=random.randint(0, 100000000),
                visit_count=random.randint(0, 60),
                is_active=True,
            )
            patient.full_name = f"{patient.last_name} {patient.first_name}"
            session.add(patient)
        
        await session.commit()
        print(f"Created {count} patients")


if __name__ == '__main__':
    asyncio.run(seed_patients(100))
