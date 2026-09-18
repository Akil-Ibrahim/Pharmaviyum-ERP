"""Seed stage 1: 20 synthetic English-language pharmacy customers and inventory."""

import asyncio
import random
from datetime import date, datetime, timedelta

from sqlalchemy import select

from src.pharmaviyum.core.database import AsyncSessionLocal
from src.pharmaviyum.models import Patient, Prescription, Product, ProductBatch
from src.pharmaviyum.models.patients import PatientPurchase

random.seed(20260918)

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

# Real medicine/product names and package characteristics are based on public
# international/US labeling examples. Batch numbers and barcodes are synthetic.
PRODUCT_CATALOG = [
    dict(name="Metformin Hydrochloride 500 mg", sku="DEMO-MET-500-100",
         dosage_strength="500 mg", dosage_form="film-coated tablet", units_per_pack=100,
         package_type="bottle", blisters_per_pack=0, units_per_blister=0,
         manufacturer="Aurobindo Pharma", inn_name="Metformin", atc_code="A10BA02",
         regulatory_id="NDC 59651-854-01", price=8.50, rx=True),
    dict(name="Amlodipine 5 mg", sku="DEMO-AML-5-30",
         dosage_strength="5 mg", dosage_form="tablet", units_per_pack=30,
         package_type="blister", blisters_per_pack=3, units_per_blister=10,
         manufacturer="Demo international manufacturer", inn_name="Amlodipine",
         atc_code="C08CA01", price=6.90, rx=True),
    dict(name="Atorvastatin 20 mg", sku="DEMO-ATO-20-30",
         dosage_strength="20 mg", dosage_form="film-coated tablet", units_per_pack=30,
         package_type="blister", blisters_per_pack=3, units_per_blister=10,
         manufacturer="Demo international manufacturer", inn_name="Atorvastatin",
         atc_code="C10AA05", price=9.80, rx=True),
    dict(name="Ibuprofen 200 mg", sku="DEMO-IBU-200-100",
         dosage_strength="200 mg", dosage_form="film-coated tablet", units_per_pack=100,
         package_type="bottle", blisters_per_pack=0, units_per_blister=0,
         manufacturer="HyVee", inn_name="Ibuprofen", atc_code="M01AE01",
         price=5.10, rx=False),
    dict(name="Paracetamol 500 mg", sku="DEMO-PAR-500-100",
         dosage_strength="500 mg", dosage_form="tablet", units_per_pack=100,
         package_type="bottle", blisters_per_pack=0, units_per_blister=0,
         manufacturer="Demo international manufacturer", inn_name="Paracetamol",
         atc_code="N02BE01", price=4.20, rx=False),
    dict(name="Cetirizine 10 mg", sku="DEMO-CET-10-30",
         dosage_strength="10 mg", dosage_form="tablet", units_per_pack=30,
         package_type="blister", blisters_per_pack=3, units_per_blister=10,
         manufacturer="Demo international manufacturer", inn_name="Cetirizine",
         atc_code="R06AE07", price=6.30, rx=False),
    dict(name="Cholecalciferol (Vitamin D3) 1000 IU", sku="DEMO-VITD3-1000-100",
         dosage_strength="1000 IU", dosage_form="tablet", units_per_pack=100,
         package_type="bottle", blisters_per_pack=0, units_per_blister=0,
         manufacturer="Demo supplement manufacturer", inn_name="Cholecalciferol",
         price=11.50, rx=False),
    dict(name="Magnesium 250 mg", sku="DEMO-MAG-250-100",
         dosage_strength="250 mg", dosage_form="tablet", units_per_pack=100,
         package_type="bottle", blisters_per_pack=0, units_per_blister=0,
         manufacturer="Demo supplement manufacturer", inn_name="Magnesium",
         price=12.90, rx=False),
    dict(name="Facial Moisturizer 50 ml", sku="DEMO-COS-MOIST-50",
         dosage_strength=None, dosage_form="cream", units_per_pack=1,
         package_type="tube", blisters_per_pack=0, units_per_blister=0,
         manufacturer="Demo skincare manufacturer", inn_name=None, price=19.90, rx=False),
    dict(name="Gentle Facial Cleanser 200 ml", sku="DEMO-COS-CLEAN-200",
         dosage_strength=None, dosage_form="cleanser", units_per_pack=1,
         package_type="bottle", blisters_per_pack=0, units_per_blister=0,
         manufacturer="Demo skincare manufacturer", inn_name=None, price=13.50, rx=False),
    dict(name="Sunscreen SPF 50 50 ml", sku="DEMO-COS-SPF50-50",
         dosage_strength="SPF 50", dosage_form="cream", units_per_pack=1,
         package_type="tube", blisters_per_pack=0, units_per_blister=0,
         manufacturer="Demo skincare manufacturer", inn_name=None, price=22.00, rx=False),
    dict(name="Blood Pressure Monitor", sku="DEMO-DEVICE-BP-1",
         dosage_strength=None, dosage_form="electronic device", units_per_pack=1,
         package_type="box", blisters_per_pack=0, units_per_blister=0,
         manufacturer="Demo medical device manufacturer", inn_name=None, price=39.90, rx=False),
    dict(name="Digital Thermometer", sku="DEMO-DEVICE-TEMP-1",
         dosage_strength=None, dosage_form="electronic device", units_per_pack=1,
         package_type="box", blisters_per_pack=0, units_per_blister=0,
         manufacturer="Demo medical device manufacturer", inn_name=None, price=12.00, rx=False),
    dict(name="Elastic Support Bandage", sku="DEMO-SUPPLY-BANDAGE-1",
         dosage_strength=None, dosage_form="medical supply", units_per_pack=1,
         package_type="roll", blisters_per_pack=0, units_per_blister=0,
         manufacturer="Demo medical supply manufacturer", inn_name=None, price=6.50, rx=False),
]


def synthetic_barcode(index: int) -> str:
    return f"DEMO{index:04d}{20260918}"


async def seed_inventory(session) -> dict[str, tuple[Product, ProductBatch]]:
    inventory = {}
    for index, spec in enumerate(PRODUCT_CATALOG, 1):
        product = await session.scalar(select(Product).where(Product.sku == spec["sku"]))
        if product is None:
            product = Product(
                name=spec["name"],
                sku=spec["sku"],
                description="Synthetic pharmacy demonstration product.",
                dosage_strength=spec["dosage_strength"],
                dosage_form=spec["dosage_form"],
                units_per_pack=spec["units_per_pack"],
                package_type=spec["package_type"],
                blisters_per_pack=spec["blisters_per_pack"],
                units_per_blister=spec["units_per_blister"],
                manufacturer=spec["manufacturer"],
                inn_name=spec["inn_name"],
                atc_code=spec.get("atc_code"),
                regulatory_id=spec.get("regulatory_id"),
                price=spec["price"],
                stock=0,
                is_active=True,
            )
            session.add(product)
            await session.flush()
        else:
            for field in (
                "name", "dosage_strength", "dosage_form", "units_per_pack",
                "package_type", "blisters_per_pack", "units_per_blister",
                "manufacturer", "inn_name", "atc_code", "regulatory_id", "price",
            ):
                setattr(product, field, spec.get(field))

        batch_number = f"DEMO-{product.sku}-L{index:02d}"
        batch = await session.scalar(
            select(ProductBatch).where(
                ProductBatch.product_id == product.id,
                ProductBatch.batch_number == batch_number,
            )
        )
        if batch is None:
            batch = ProductBatch(
                product_id=product.id,
                batch_number=batch_number,
                expiry_date=date(2029 + (index % 3), 6 + (index % 6), 1),
                received_quantity=100,
                available_quantity=100,
                barcode=synthetic_barcode(index),
            )
            session.add(batch)
            await session.flush()
        inventory[product.sku] = (product, batch)
    return inventory


async def seed_patients() -> None:
    async with AsyncSessionLocal() as session:
        inventory = await seed_inventory(session)
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

            # Give every patient a varied pharmacy history. Product choice is
            # intentionally not derived from a real patient's medical record.
            for visit in range(1, 3 + index % 2):
                receipt = f"DEMO-{index:03d}-{visit:02d}"
                products = random.sample(PRODUCT_CATALOG, k=3)
                for spec in products:
                    product, batch = inventory[spec["sku"]]
                    exists = await session.scalar(
                        select(PatientPurchase).where(
                            PatientPurchase.patient_id == patient.id,
                            PatientPurchase.receipt_number == receipt,
                            PatientPurchase.product_id == product.id,
                        )
                    )
                    if exists:
                        continue

                    packs = random.randint(1, 2)
                    if product.units_per_pack > 1 and product.blisters_per_pack:
                        blisters = random.randint(1, product.blisters_per_pack * packs)
                        units = min(
                            product.units_per_pack * packs,
                            blisters * product.units_per_blister,
                        )
                    else:
                        blisters = 0
                        units = product.units_per_pack * packs

                    session.add(
                        PatientPurchase(
                            patient_id=patient.id,
                            product_id=product.id,
                            batch_id=batch.id,
                            receipt_number=receipt,
                            category=(
                                "Prescription Medicine" if spec["rx"]
                                else "OTC / Consumer Health"
                                if spec["dosage_form"] in {"tablet", "film-coated tablet"}
                                else "Consumer / Medical"
                            ),
                            quantity=packs,
                            dispensed_packs=packs,
                            dispensed_blisters=blisters,
                            dispensed_units=units,
                            unit_price=spec["price"],
                            prescription_required=spec["rx"],
                            purchased_at=datetime.utcnow()
                            - timedelta(days=random.randint(1, 120)),
                        )
                    )
                    batch.available_quantity = max(
                        0, batch.available_quantity - packs
                    )
                    product.stock = batch.available_quantity

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
        print(
            f"Stage 1 complete: {len(CUSTOMERS)} synthetic patients; "
            f"newly created: {created}; products: {len(PRODUCT_CATALOG)}."
        )


if __name__ == "__main__":
    asyncio.run(seed_patients())
