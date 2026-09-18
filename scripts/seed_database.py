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
         manufacturer="Demo skincare manufacturer", inn_name=None,
         price=19.90, rx=False),
    dict(name="Gentle Facial Cleanser 200 ml", sku="DEMO-COS-CLEAN-200",
         dosage_strength=None, dosage_form="cleanser", units_per_pack=1,
         package_type="bottle", blisters_per_pack=0, units_per_blister=0,
         manufacturer="Demo skincare manufacturer", inn_name=None,
         price=13.50, rx=False),
    dict(name="Sunscreen SPF 50 50 ml", sku="DEMO-COS-SPF50-50",
         dosage_strength="SPF 50", dosage_form="cream", units_per_pack=1,
         package_type="tube", blisters_per_pack=0, units_per_blister=0,
         manufacturer="Demo skincare manufacturer", inn_name=None,
         price=22.00, rx=False),
    dict(name="Blood Pressure Monitor", sku="DEMO-DEVICE-BP-1",
         dosage_strength=None, dosage_form="electronic device", units_per_pack=1,
         package_type="box", blisters_per_pack=0, units_per_blister=0,
         manufacturer="Demo medical device manufacturer", inn_name=None,
         price=39.90, rx=False),
    dict(name="Digital Thermometer", sku="DEMO-DEVICE-TEMP-1",
         dosage_strength=None, dosage_form="electronic device", units_per_pack=1,
         package_type="box", blisters_per_pack=0, units_per_blister=0,
         manufacturer="Demo medical device manufacturer", inn_name=None,
         price=12.00, rx=False),
    dict(name="Elastic Support Bandage", sku="DEMO-SUPPLY-BANDAGE-1",
         dosage_strength=None, dosage_form="medical supply", units_per_pack=1,
         package_type="roll", blisters_per_pack=0, units_per_blister=0,
         manufacturer="Demo medical supply manufacturer", inn_name=None,
         price=6.50, rx=False),
    dict(
        name="Amoxicillin 250 mg/5 ml Oral Suspension",
        sku="DEMO-AMOX-SUSP-100",
        dosage_strength="250 mg/5 ml",
        dosage_form="oral suspension",
        units_per_pack=1,
        package_type="bottle",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo international manufacturer",
        inn_name="Amoxicillin",
        atc_code="J01CA04",
        price=9.50,
        rx=True,
    ),
    dict(
        name="Salbutamol 100 mcg/dose Inhaler",
        sku="DEMO-SALB-INH-200",
        dosage_strength="100 mcg/dose",
        dosage_form="pressurized inhalation",
        units_per_pack=1,
        package_type="inhaler",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo international manufacturer",
        inn_name="Salbutamol",
        atc_code="R03AC02",
        price=14.90,
        rx=True,
    ),
    dict(
        name="Xylometazoline 0.1% Nasal Spray",
        sku="DEMO-XYLO-SPRAY-10",
        dosage_strength="0.1%",
        dosage_form="nasal spray",
        units_per_pack=1,
        package_type="spray bottle",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo international manufacturer",
        inn_name="Xylometazoline",
        atc_code="R01AA07",
        price=7.20,
        rx=False,
    ),
    dict(
        name="Sodium Chloride 0.9% Nasal Drops",
        sku="DEMO-NS-DROPS-10",
        dosage_strength="0.9%",
        dosage_form="nasal drops",
        units_per_pack=1,
        package_type="dropper bottle",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo international manufacturer",
        inn_name="Sodium chloride",
        atc_code="R01AX16",
        price=5.90,
        rx=False,
    ),
    dict(
        name="Chlorhexidine 0.05% Antiseptic Solution",
        sku="DEMO-CHX-SOL-200",
        dosage_strength="0.05%",
        dosage_form="topical solution",
        units_per_pack=1,
        package_type="bottle",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo international manufacturer",
        inn_name="Chlorhexidine",
        atc_code="D08AC02",
        price=6.80,
        rx=False,
    ),
    dict(
        name="Hydrocortisone 1% Cream",
        sku="DEMO-HC-CREAM-15",
        dosage_strength="1%",
        dosage_form="cream",
        units_per_pack=1,
        package_type="tube",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo dermatology manufacturer",
        inn_name="Hydrocortisone",
        atc_code="D07AA02",
        price=8.90,
        rx=False,
    ),
    dict(
        name="Clotrimazole 1% Cream",
        sku="DEMO-CLOTR-CREAM-20",
        dosage_strength="1%",
        dosage_form="cream",
        units_per_pack=1,
        package_type="tube",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo dermatology manufacturer",
        inn_name="Clotrimazole",
        atc_code="D01AC01",
        price=7.90,
        rx=False,
    ),
    dict(
        name="Mupirocin 2% Ointment",
        sku="DEMO-MUP-OINT-15",
        dosage_strength="2%",
        dosage_form="ointment",
        units_per_pack=1,
        package_type="tube",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo dermatology manufacturer",
        inn_name="Mupirocin",
        atc_code="D06AX09",
        price=11.90,
        rx=True,
    ),
    dict(
        name="Diclofenac 1% Topical Gel",
        sku="DEMO-DIC-GEL-50",
        dosage_strength="1%",
        dosage_form="gel",
        units_per_pack=1,
        package_type="tube",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo international manufacturer",
        inn_name="Diclofenac",
        atc_code="M02AA15",
        price=10.50,
        rx=False,
    ),
    dict(
        name="Calamine Topical Lotion",
        sku="DEMO-CAL-LOT-100",
        dosage_strength=None,
        dosage_form="lotion",
        units_per_pack=1,
        package_type="bottle",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo dermatology manufacturer",
        inn_name="Calamine",
        price=8.40,
        rx=False,
    ),
    dict(
        name="Benzoyl Peroxide 5% Gel",
        sku="DEMO-BPO-GEL-30",
        dosage_strength="5%",
        dosage_form="gel",
        units_per_pack=1,
        package_type="tube",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo dermatology manufacturer",
        inn_name="Benzoyl peroxide",
        atc_code="D10AE01",
        price=9.60,
        rx=False,
    ),
    dict(
        name="Zinc Oxide 10% Protective Ointment",
        sku="DEMO-ZNO-OINT-50",
        dosage_strength="10%",
        dosage_form="ointment",
        units_per_pack=1,
        package_type="tube",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo skincare manufacturer",
        inn_name="Zinc oxide",
        price=7.40,
        rx=False,
    ),
    dict(
        name="Paracetamol 120 mg/5 ml Oral Suspension",
        sku="DEMO-PAR-SUSP-100",
        dosage_strength="120 mg/5 ml",
        dosage_form="oral suspension",
        units_per_pack=1,
        package_type="bottle",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo international manufacturer",
        inn_name="Paracetamol",
        atc_code="N02BE01",
        price=6.20,
        rx=False,
    ),
    dict(
        name="Omeprazole 20 mg Capsules",
        sku="DEMO-OME-20-28",
        dosage_strength="20 mg",
        dosage_form="capsule",
        units_per_pack=28,
        package_type="blister",
        blisters_per_pack=4,
        units_per_blister=7,
        manufacturer="Demo international manufacturer",
        inn_name="Omeprazole",
        atc_code="A02BC01",
        price=8.80,
        rx=False,
    ),
    dict(
        name="Loperamide 2 mg Capsules",
        sku="DEMO-LOP-2-20",
        dosage_strength="2 mg",
        dosage_form="capsule",
        units_per_pack=20,
        package_type="blister",
        blisters_per_pack=2,
        units_per_blister=10,
        manufacturer="Demo international manufacturer",
        inn_name="Loperamide",
        atc_code="A07DA03",
        price=5.80,
        rx=False,
    ),
    dict(
        name="Glycerol 2 g Suppositories",
        sku="DEMO-GLY-SUP-12",
        dosage_strength="2 g",
        dosage_form="suppository",
        units_per_pack=12,
        package_type="blister",
        blisters_per_pack=1,
        units_per_blister=12,
        manufacturer="Demo international manufacturer",
        inn_name="Glycerol",
        atc_code="A06AX01",
        price=6.70,
        rx=False,
    ),
    dict(
        name="Clotrimazole 100 mg Vaginal Tablets",
        sku="DEMO-CLOTR-VAG-6",
        dosage_strength="100 mg",
        dosage_form="vaginal tablet",
        units_per_pack=6,
        package_type="blister",
        blisters_per_pack=1,
        units_per_blister=6,
        manufacturer="Demo women's health manufacturer",
        inn_name="Clotrimazole",
        atc_code="G01AF02",
        price=9.90,
        rx=False,
    ),
    dict(
        name="Artificial Tears Eye Drops",
        sku="DEMO-EYE-DROPS-10",
        dosage_strength=None,
        dosage_form="eye drops",
        units_per_pack=1,
        package_type="dropper bottle",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo ophthalmic manufacturer",
        inn_name=None,
        price=10.90,
        rx=False,
    ),
    dict(
        name="Antacid Oral Suspension",
        sku="DEMO-ANT-SUSP-200",
        dosage_strength=None,
        dosage_form="oral suspension",
        units_per_pack=1,
        package_type="bottle",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo international manufacturer",
        inn_name=None,
        price=7.60,
        rx=False,
    ),
    dict(
        name="Oral Rehydration Salts Sachets",
        sku="DEMO-ORS-10",
        dosage_strength=None,
        dosage_form="oral powder",
        units_per_pack=10,
        package_type="sachet box",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo international manufacturer",
        inn_name=None,
        price=8.20,
        rx=False,
    ),
    dict(
        name="Throat Lozenges",
        sku="DEMO-THROAT-LOZ-24",
        dosage_strength=None,
        dosage_form="lozenge",
        units_per_pack=24,
        package_type="blister",
        blisters_per_pack=2,
        units_per_blister=12,
        manufacturer="Demo consumer health manufacturer",
        inn_name=None,
        price=6.50,
        rx=False,
    ),
    dict(
        name="Antiseptic Wound Dressing",
        sku="DEMO-WOUND-DRESS-10",
        dosage_strength=None,
        dosage_form="wound dressing",
        units_per_pack=10,
        package_type="box",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo medical supply manufacturer",
        inn_name=None,
        price=8.90,
        rx=False,
    ),
    dict(
        name="Hydrocolloid Acne Patches",
        sku="DEMO-ACNE-PATCH-24",
        dosage_strength=None,
        dosage_form="medicated patch",
        units_per_pack=24,
        package_type="pouch",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo skincare manufacturer",
        inn_name=None,
        price=9.50,
        rx=False,
    ),
    dict(
        name="Zinc + Vitamin C Effervescent Tablets",
        sku="DEMO-ZNC-EFF-20",
        dosage_strength=None,
        dosage_form="effervescent tablet",
        units_per_pack=20,
        package_type="tube",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo supplement manufacturer",
        inn_name=None,
        price=10.50,
        rx=False,
    ),
]

def synthetic_barcode(index: int) -> str:
    return f"DEMO{index:04d}{20260918}"

async def seed_inventory(session) -> dict[str, tuple[Product, ProductBatch]]:
    inventory = {}
    for index, spec in enumerate(PRODUCT_CATALOG, 1):
        product = await session.scalar(
            select(Product).where(Product.sku == spec["sku"])
        )
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
                                if spec["dosage_form"] in {
                                    "tablet",
                                    "film-coated tablet",
                                }
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
                    rx_spec = next(spec for spec in PRODUCT_CATALOG if spec["rx"])
                    rx_product, _ = inventory[rx_spec["sku"]]
                    session.add(
                        Prescription(
                            patient_id=patient.id,
                            product_id=rx_product.id,
                            prescription_number=prescription_number,
                            dosage=(
                                (
                                    f"{rx_product.dosage_strength}; follow prescriber directions"
                                )
                            ),
                            instructions=(
                                (
                                    "Synthetic demonstration prescription. " "Do not use as clinical guidance."
                                )
                            ),
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
