"""Database seeding with realistic Vietnamese data."""
import asyncio
import random
from faker import Faker

fake = Faker('vi_VN')

MEDICATIONS = [
    {'name': 'Paracetamol 500mg', 'dosage': '1 tablet', 'frequency': '3x daily'},
    {'name': 'Amoxicillin 500mg', 'dosage': '1 tablet', 'frequency': '3x daily'},
    {'name': 'Metformin 850mg', 'dosage': '1 tablet', 'frequency': '2x daily'},
    {'name': 'Amlodipine 5mg', 'dosage': '1 tablet', 'frequency': '1x daily'},
    {'name': 'Omeprazole 20mg', 'dosage': '1 tablet', 'frequency': '1x daily'},
]

VIETNAMESE_CITIES = ['Ho Chi Minh', 'Hanoi', 'Da Nang', 'Hai Phong', 'Can Tho']


async def seed_patients(count: int = 100):
    """Generate realistic Vietnamese patients."""
    # TODO: Import your Patient model and session
    for _ in range(count):
        data = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "phone": f"+84{random.randint(100000000, 999999999)}",
            "email": fake.email(),
            "city": random.choice(VIETNAMESE_CITIES),
            "country": "VN",
            "preferred_language": "vi",
            "loyalty_tier": random.choices(
                ['Bronze', 'Silver', 'Gold', 'Platinum'],
                weights=[0.50, 0.30, 0.15, 0.05]
            )[0],
        }
        # TODO: save via your repository
    print(f"✅ Created {count} patients")


if __name__ == '__main__':
    asyncio.run(seed_patients(100))
