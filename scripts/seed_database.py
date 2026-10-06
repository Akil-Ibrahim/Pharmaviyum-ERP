"""Seed stage 1: 20 synthetic English-language pharmacy customers and inventory."""

import asyncio
import random
from datetime import date, datetime, timedelta

from sqlalchemy import delete, select

from src.pharmaviyum.core.database import AsyncSessionLocal
from src.pharmaviyum.models import Inventory, Patient, Pharmacy, Prescription, Product, ProductBatch
from src.pharmaviyum.models.patients import PatientPurchase
from src.pharmaviyum.models.patients.patient_condition import PatientCondition

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
    dict(
        name="Metformin Hydrochloride 500 mg",
        sku="DEMO-MET-500-100",
        dosage_strength="500 mg",
        dosage_form="film-coated tablet",
        units_per_pack=100,
        package_type="bottle",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Aurobindo Pharma",
        inn_name="Metformin",
        atc_code="A10BA02",
        regulatory_id="NDC 59651-854-01",
        price=8.50,
        rx=True,
    ),
    dict(
        name="Amlodipine 5 mg",
        sku="DEMO-AML-5-30",
        dosage_strength="5 mg",
        dosage_form="tablet",
        units_per_pack=30,
        package_type="blister",
        blisters_per_pack=3,
        units_per_blister=10,
        manufacturer="Demo international manufacturer",
        inn_name="Amlodipine",
        atc_code="C08CA01",
        price=6.90,
        rx=True,
    ),
    dict(
        name="Atorvastatin 20 mg",
        sku="DEMO-ATO-20-30",
        dosage_strength="20 mg",
        dosage_form="film-coated tablet",
        units_per_pack=30,
        package_type="blister",
        blisters_per_pack=3,
        units_per_blister=10,
        manufacturer="Demo international manufacturer",
        inn_name="Atorvastatin",
        atc_code="C10AA05",
        price=9.80,
        rx=True,
    ),
    dict(
        name="Ibuprofen 200 mg",
        sku="DEMO-IBU-200-100",
        dosage_strength="200 mg",
        dosage_form="film-coated tablet",
        units_per_pack=100,
        package_type="bottle",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="HyVee",
        inn_name="Ibuprofen",
        atc_code="M01AE01",
        price=5.10,
        rx=False,
    ),
    dict(
        name="Paracetamol 500 mg",
        sku="DEMO-PAR-500-100",
        dosage_strength="500 mg",
        dosage_form="tablet",
        units_per_pack=100,
        package_type="bottle",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo international manufacturer",
        inn_name="Paracetamol",
        atc_code="N02BE01",
        price=4.20,
        rx=False,
    ),
    dict(
        name="Cetirizine 10 mg",
        sku="DEMO-CET-10-30",
        dosage_strength="10 mg",
        dosage_form="tablet",
        units_per_pack=30,
        package_type="blister",
        blisters_per_pack=3,
        units_per_blister=10,
        manufacturer="Demo international manufacturer",
        inn_name="Cetirizine",
        atc_code="R06AE07",
        price=6.30,
        rx=False,
    ),
    dict(
        name="Cholecalciferol (Vitamin D3) 1000 IU",
        sku="DEMO-VITD3-1000-100",
        dosage_strength="1000 IU",
        dosage_form="tablet",
        units_per_pack=100,
        package_type="bottle",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo supplement manufacturer",
        inn_name="Cholecalciferol",
        price=11.50,
        rx=False,
    ),
    dict(
        name="Magnesium 250 mg",
        sku="DEMO-MAG-250-100",
        dosage_strength="250 mg",
        dosage_form="tablet",
        units_per_pack=100,
        package_type="bottle",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo supplement manufacturer",
        inn_name="Magnesium",
        price=12.90,
        rx=False,
    ),
    dict(
        name="Facial Moisturizer 50 ml",
        sku="DEMO-COS-MOIST-50",
        dosage_strength=None,
        dosage_form="cream",
        units_per_pack=1,
        package_type="tube",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo skincare manufacturer",
        inn_name=None,
        price=19.90,
        rx=False,
    ),
    dict(
        name="Gentle Facial Cleanser 200 ml",
        sku="DEMO-COS-CLEAN-200",
        dosage_strength=None,
        dosage_form="cleanser",
        units_per_pack=1,
        package_type="bottle",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo skincare manufacturer",
        inn_name=None,
        price=13.50,
        rx=False,
    ),
    dict(
        name="Sunscreen SPF 50 50 ml",
        sku="DEMO-COS-SPF50-50",
        dosage_strength="SPF 50",
        dosage_form="cream",
        units_per_pack=1,
        package_type="tube",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo skincare manufacturer",
        inn_name=None,
        price=22.00,
        rx=False,
    ),
    dict(
        name="Blood Pressure Monitor",
        sku="DEMO-DEVICE-BP-1",
        dosage_strength=None,
        dosage_form="electronic device",
        units_per_pack=1,
        package_type="box",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo medical device manufacturer",
        inn_name=None,
        price=39.90,
        rx=False,
    ),
    dict(
        name="Digital Thermometer",
        sku="DEMO-DEVICE-TEMP-1",
        dosage_strength=None,
        dosage_form="electronic device",
        units_per_pack=1,
        package_type="box",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo medical device manufacturer",
        inn_name=None,
        price=12.00,
        rx=False,
    ),
    dict(
        name="Elastic Support Bandage",
        sku="DEMO-SUPPLY-BANDAGE-1",
        dosage_strength=None,
        dosage_form="medical supply",
        units_per_pack=1,
        package_type="roll",
        blisters_per_pack=0,
        units_per_blister=0,
        manufacturer="Demo medical supply manufacturer",
        inn_name=None,
        price=6.50,
        rx=False,
    ),
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


PRODUCT_CATALOG.extend([
    dict(name="Norvasc 5 mg", sku="BRAND-NORVASC-5-90", dosage_strength="5 mg", dosage_form="tablet", units_per_pack=90, package_type="blister", blisters_per_pack=9, units_per_blister=10, manufacturer="Viatris", inn_name="Amlodipine", atc_code="C08CA01", price=18.90, rx=True, description="Synthetic demo reference/original product."),
    dict(name="Amlodipine 5 mg", sku="GEN-AMLOD-SANDOZ-5-30", dosage_strength="5 mg", dosage_form="tablet", units_per_pack=30, package_type="blister", blisters_per_pack=3, units_per_blister=10, manufacturer="Sandoz", inn_name="Amlodipine", atc_code="C08CA01", price=6.90, rx=True, description="Synthetic demo generic product."),
    dict(name="Lipitor 20 mg", sku="BRAND-LIPITOR-20-90", dosage_strength="20 mg", dosage_form="film-coated tablet", units_per_pack=90, package_type="blister", blisters_per_pack=9, units_per_blister=10, manufacturer="Viatris", inn_name="Atorvastatin", atc_code="C10AA05", price=22.50, rx=True, description="Synthetic demo reference/original product."),
    dict(name="Atorvastatin 20 mg", sku="GEN-ATOR-TEVA-20-30", dosage_strength="20 mg", dosage_form="film-coated tablet", units_per_pack=30, package_type="blister", blisters_per_pack=3, units_per_blister=10, manufacturer="Teva", inn_name="Atorvastatin", atc_code="C10AA05", price=9.80, rx=True, description="Synthetic demo generic product."),
    dict(name="Glucophage XR 500 mg", sku="BRAND-GLUCOPHAGE-XR-500-60", dosage_strength="500 mg", dosage_form="extended-release tablet", units_per_pack=60, package_type="blister", blisters_per_pack=6, units_per_blister=10, manufacturer="Merck", inn_name="Metformin", atc_code="A10BA02", price=16.50, rx=True, description="Synthetic demo reference/original product."),
    dict(name="Metformin 500 mg", sku="GEN-MET-TEVA-500-60", dosage_strength="500 mg", dosage_form="film-coated tablet", units_per_pack=60, package_type="blister", blisters_per_pack=6, units_per_blister=10, manufacturer="Teva", inn_name="Metformin", atc_code="A10BA02", price=7.50, rx=True, description="Synthetic demo generic product."),
    dict(name="Nexium 20 mg", sku="BRAND-NEXIUM-20-30", dosage_strength="20 mg", dosage_form="gastro-resistant tablet", units_per_pack=30, package_type="blister", blisters_per_pack=3, units_per_blister=10, manufacturer="AstraZeneca", inn_name="Esomeprazole", atc_code="A02BC05", price=24.90, rx=False, description="Synthetic demo reference/original product."),
    dict(name="Omeprazole 20 mg", sku="GEN-OME-SANDOZ-20-30", dosage_strength="20 mg", dosage_form="gastro-resistant capsule", units_per_pack=30, package_type="blister", blisters_per_pack=3, units_per_blister=10, manufacturer="Sandoz", inn_name="Omeprazole", atc_code="A02BC01", price=8.80, rx=False, description="Synthetic demo generic product."),
    dict(name="Ventolin 100 mcg/dose Inhaler", sku="BRAND-VENTOLIN-100-200", dosage_strength="100 mcg/dose", dosage_form="pressurized inhalation", units_per_pack=1, package_type="inhaler", blisters_per_pack=0, units_per_blister=0, manufacturer="GSK", inn_name="Salbutamol", atc_code="R03AC02", price=19.90, rx=True, description="Synthetic demo reference/original product."),
    dict(name="Salbutamol 100 mcg/dose Inhaler", sku="GEN-SALB-TEVA-100-200", dosage_strength="100 mcg/dose", dosage_form="pressurized inhalation", units_per_pack=1, package_type="inhaler", blisters_per_pack=0, units_per_blister=0, manufacturer="Teva", inn_name="Salbutamol", atc_code="R03AC02", price=14.90, rx=True, description="Synthetic demo generic product."),
    dict(name="Zyrtec 10 mg", sku="BRAND-ZYRTEC-10-20", dosage_strength="10 mg", dosage_form="tablet", units_per_pack=20, package_type="blister", blisters_per_pack=2, units_per_blister=10, manufacturer="UCB", inn_name="Cetirizine", atc_code="R06AE07", price=12.90, rx=False, description="Synthetic demo reference/original product."),
    dict(name="Cetirizine 10 mg", sku="GEN-CET-SANDOZ-10-20", dosage_strength="10 mg", dosage_form="tablet", units_per_pack=20, package_type="blister", blisters_per_pack=2, units_per_blister=10, manufacturer="Sandoz", inn_name="Cetirizine", atc_code="R06AE07", price=6.30, rx=False, description="Synthetic demo generic product."),
    dict(name="Voltaren Emulgel 1%", sku="BRAND-VOLTAREN-1-50", dosage_strength="1%", dosage_form="gel", units_per_pack=1, package_type="tube", blisters_per_pack=0, units_per_blister=0, manufacturer="Haleon", inn_name="Diclofenac", atc_code="M02AA15", price=14.90, rx=False, description="Synthetic demo reference/original product."),
    dict(name="Diclofenac 1% Gel", sku="GEN-DIC-TEVA-1-50", dosage_strength="1%", dosage_form="gel", units_per_pack=1, package_type="tube", blisters_per_pack=0, units_per_blister=0, manufacturer="Teva", inn_name="Diclofenac", atc_code="M02AA15", price=10.50, rx=False, description="Synthetic demo generic product."),
    dict(name="Nurofen 200 mg", sku="BRAND-NUROFEN-200-24", dosage_strength="200 mg", dosage_form="film-coated tablet", units_per_pack=24, package_type="blister", blisters_per_pack=2, units_per_blister=12, manufacturer="Reckitt", inn_name="Ibuprofen", atc_code="M01AE01", price=9.90, rx=False, description="Synthetic demo reference/original product."),
    dict(name="Ibuprofen 200 mg", sku="GEN-IBU-TEVA-200-20", dosage_strength="200 mg", dosage_form="film-coated tablet", units_per_pack=20, package_type="blister", blisters_per_pack=2, units_per_blister=10, manufacturer="Teva", inn_name="Ibuprofen", atc_code="M01AE01", price=5.10, rx=False, description="Synthetic demo generic product."),
    dict(name="Panadol 500 mg", sku="BRAND-PANADOL-500-24", dosage_strength="500 mg", dosage_form="tablet", units_per_pack=24, package_type="blister", blisters_per_pack=2, units_per_blister=12, manufacturer="Haleon", inn_name="Paracetamol", atc_code="N02BE01", price=7.90, rx=False, description="Synthetic demo reference/original product."),
    dict(name="Paracetamol 500 mg", sku="GEN-PAR-SANDOZ-500-20", dosage_strength="500 mg", dosage_form="tablet", units_per_pack=20, package_type="blister", blisters_per_pack=2, units_per_blister=10, manufacturer="Sandoz", inn_name="Paracetamol", atc_code="N02BE01", price=4.20, rx=False, description="Synthetic demo generic product."),
    dict(name="Plavix 75 mg", sku="BRAND-PLAVIX-75-28", dosage_strength="75 mg", dosage_form="film-coated tablet", units_per_pack=28, package_type="blister", blisters_per_pack=2, units_per_blister=14, manufacturer="Sanofi", inn_name="Clopidogrel", atc_code="B01AC04", price=21.90, rx=True, description="Synthetic demo reference/original product."),
    dict(name="Crestor 10 mg", sku="BRAND-CRESTOR-10-90", dosage_strength="10 mg", dosage_form="film-coated tablet", units_per_pack=90, package_type="blister", blisters_per_pack=9, units_per_blister=10, manufacturer="AstraZeneca", inn_name="Rosuvastatin", atc_code="C10AA07", price=25.90, rx=True, description="Synthetic demo reference/original product."),
    dict(name="Rosuvastatin 10 mg", sku="GEN-ROSU-SANDOZ-10-30", dosage_strength="10 mg", dosage_form="film-coated tablet", units_per_pack=30, package_type="blister", blisters_per_pack=3, units_per_blister=10, manufacturer="Sandoz", inn_name="Rosuvastatin", atc_code="C10AA07", price=10.90, rx=True, description="Synthetic demo generic product."),
])

PATIENT_PROFILES = [
("Hypertension","I10",["BRAND-NORVASC-5-90","GEN-AMLOD-SANDOZ-5-30","BRAND-LIPITOR-20-90","BRAND-NUROFEN-200-24","GEN-PAR-SANDOZ-500-20","BRAND-NEXIUM-20-30"]),
("Type 2 diabetes","E11.9",["BRAND-GLUCOPHAGE-XR-500-60","GEN-MET-TEVA-500-60","BRAND-LIPITOR-20-90","GEN-AMLOD-SANDOZ-5-30","GEN-PAR-SANDOZ-500-20","BRAND-NEXIUM-20-30"]),
("Hyperlipidemia","E78.5",["BRAND-LIPITOR-20-90","BRAND-CRESTOR-10-90","GEN-ATOR-TEVA-20-30","GEN-ROSU-SANDOZ-10-30","BRAND-NEXIUM-20-30","BRAND-PANADOL-500-24"]),
("Asthma","J45.909",["BRAND-VENTOLIN-100-200","GEN-SALB-TEVA-100-200","BRAND-ZYRTEC-10-20","GEN-CET-SANDOZ-10-20","BRAND-PANADOL-500-24","BRAND-NEXIUM-20-30"]),
("Allergic rhinitis","J30.9",["BRAND-ZYRTEC-10-20","GEN-CET-SANDOZ-10-20","BRAND-VENTOLIN-100-200","GEN-PAR-SANDOZ-500-20","BRAND-NEXIUM-20-30","BRAND-NUROFEN-200-24"]),
("GERD","K21.9",["BRAND-NEXIUM-20-30","GEN-OME-SANDOZ-20-30","BRAND-PANADOL-500-24","GEN-PAR-SANDOZ-500-20","BRAND-NUROFEN-200-24","BRAND-ZYRTEC-10-20"]),
("Osteoarthritis","M19.90",["BRAND-VOLTAREN-1-50","GEN-DIC-TEVA-1-50","BRAND-NUROFEN-200-24","GEN-IBU-TEVA-200-20","BRAND-PANADOL-500-24","GEN-PAR-SANDOZ-500-20"]),
("Atopic dermatitis","L20.9",["BRAND-VOLTAREN-1-50","GEN-DIC-TEVA-1-50","BRAND-ZYRTEC-10-20","GEN-CET-SANDOZ-10-20","BRAND-PANADOL-500-24","GEN-PAR-SANDOZ-500-20"]),
("Coronary artery disease","I25.10",["BRAND-NORVASC-5-90","GEN-AMLOD-SANDOZ-5-30","BRAND-PLAVIX-75-28","BRAND-LIPITOR-20-90","GEN-ATOR-TEVA-20-30","BRAND-NEXIUM-20-30"]),
("Chronic dyspepsia","K30",["BRAND-NEXIUM-20-30","GEN-OME-SANDOZ-20-30","BRAND-PANADOL-500-24","GEN-PAR-SANDOZ-500-20","BRAND-ZYRTEC-10-20","BRAND-NUROFEN-200-24"]),
("COPD","J44.9",["BRAND-VENTOLIN-100-200","GEN-SALB-TEVA-100-200","BRAND-ZYRTEC-10-20","GEN-CET-SANDOZ-10-20","BRAND-PANADOL-500-24","BRAND-NEXIUM-20-30"]),
("Chronic musculoskeletal pain","M79.18",["BRAND-VOLTAREN-1-50","GEN-DIC-TEVA-1-50","BRAND-NUROFEN-200-24","GEN-IBU-TEVA-200-20","BRAND-PANADOL-500-24","GEN-PAR-SANDOZ-500-20"]),
("Diabetic dyslipidemia","E11.69",["BRAND-GLUCOPHAGE-XR-500-60","GEN-MET-TEVA-500-60","BRAND-LIPITOR-20-90","GEN-ATOR-TEVA-20-30","BRAND-NORVASC-5-90","GEN-AMLOD-SANDOZ-5-30"]),
("Hypertension with hyperlipidemia","I10",["BRAND-NORVASC-5-90","GEN-AMLOD-SANDOZ-5-30","BRAND-CRESTOR-10-90","GEN-ROSU-SANDOZ-10-30","BRAND-PANADOL-500-24","BRAND-NEXIUM-20-30"]),
("Seasonal allergy","J30.2",["BRAND-ZYRTEC-10-20","GEN-CET-SANDOZ-10-20","BRAND-NEXIUM-20-30","GEN-OME-SANDOZ-20-30","BRAND-PANADOL-500-24","GEN-PAR-SANDOZ-500-20"]),
("Chronic pain","G89.29",["BRAND-NUROFEN-200-24","GEN-IBU-TEVA-200-20","BRAND-VOLTAREN-1-50","GEN-DIC-TEVA-1-50","BRAND-PANADOL-500-24","GEN-PAR-SANDOZ-500-20"]),
("Atherosclerotic cardiovascular disease","I25.10",["BRAND-PLAVIX-75-28","BRAND-LIPITOR-20-90","BRAND-NORVASC-5-90","GEN-ATOR-TEVA-20-30","GEN-AMLOD-SANDOZ-5-30","BRAND-NEXIUM-20-30"]),
("Respiratory allergy","J30.9",["BRAND-ZYRTEC-10-20","GEN-CET-SANDOZ-10-20","BRAND-VENTOLIN-100-200","GEN-SALB-TEVA-100-200","BRAND-PANADOL-500-24","GEN-PAR-SANDOZ-500-20"]),
("Chronic gastritis","K29.70",["BRAND-NEXIUM-20-30","GEN-OME-SANDOZ-20-30","BRAND-NUROFEN-200-24","GEN-IBU-TEVA-200-20","BRAND-PANADOL-500-24","GEN-PAR-SANDOZ-500-20"]),
("Mixed cardiovascular risk","I10",["BRAND-NORVASC-5-90","BRAND-LIPITOR-20-90","BRAND-PLAVIX-75-28","GEN-AMLOD-SANDOZ-5-30","GEN-ATOR-TEVA-20-30","BRAND-NEXIUM-20-30"]),
]

def synthetic_barcode(index: int) -> str:
    return f"DEMO{index:04d}{20260918}"


async def seed_inventory(
    session, pharmacy: Pharmacy
) -> dict[str, tuple[Product, ProductBatch, Inventory]]:
    inventory = {}
    for index, spec in enumerate(PRODUCT_CATALOG, 1):
        product = await session.scalar(
            select(Product).where(Product.sku == spec["sku"])
        )
        if product is None:
            product = Product(
                name=spec["name"],
                sku=spec["sku"],
                description=spec.get("description", "Synthetic pharmacy demonstration product."),
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
                "name",
                "description",
                "dosage_strength",
                "dosage_form",
                "units_per_pack",
                "package_type",
                "blisters_per_pack",
                "units_per_blister",
                "manufacturer",
                "inn_name",
                "atc_code",
                "regulatory_id",
                "price",
            ):
                setattr(product, field, spec.get(field))

        batch_number = f"DEMO-{product.sku}-L{index:02d}"
        demo_expiry_date = (
            date(2026, 9, 1)
            if index % 12 == 0
            else date(2026, 10 + (index % 3), 1)
            if index % 12 in {1, 2, 3}
            else date(2027, 1 + (index % 9), 1)
            if index % 12 in {4, 5, 6, 7, 8}
            else date(2028 + (index % 3), 6 + (index % 6), 1)
        )
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
                expiry_date=demo_expiry_date,
                received_quantity=100,
                available_quantity=100,
                barcode=synthetic_barcode(index),
            )
            session.add(batch)
            await session.flush()
        else:
            batch.expiry_date = demo_expiry_date
        inventory_record = await session.scalar(
            select(Inventory).where(
                Inventory.product_id == product.id,
                Inventory.pharmacy_id == pharmacy.id,
                Inventory.lot_number == batch.batch_number,
            )
        )
        if inventory_record is None:
            inventory_record = Inventory(
                product_id=product.id,
                pharmacy_id=pharmacy.id,
                quantity=batch.available_quantity,
                reserved_quantity=0,
                reorder_level=10,
                lot_number=batch.batch_number,
                expires_at=datetime.combine(batch.expiry_date, datetime.min.time()),
            )
            session.add(inventory_record)
            await session.flush()
        else:
            inventory_record.quantity = batch.available_quantity
            inventory_record.reserved_quantity = 0
            inventory_record.lot_number = batch.batch_number
            inventory_record.expires_at = datetime.combine(
                batch.expiry_date, datetime.min.time()
            )

        inventory[product.sku] = (product, batch, inventory_record)
    return inventory


async def seed_patients() -> None:
    async with AsyncSessionLocal() as session:
        pharmacy = await session.scalar(
            select(Pharmacy)
            .where(Pharmacy.is_active.is_(True))
            .order_by(Pharmacy.id.asc())
        )
        if pharmacy is None:
            raise RuntimeError(
                "SEED_DEMO_DATA requires at least one active pharmacy. "
                "Create a pharmacy before seeding synthetic data."
            )

        inventory = await seed_inventory(session, pharmacy)
        created = 0

        # Reset synthetic inventory before rebuilding synthetic sales history.
        # This keeps repeated SEED_DEMO_DATA runs deterministic instead of
        # decrementing the same demo batches on every run.
        for product, batch, inventory_record in inventory.values():
            batch.available_quantity = batch.received_quantity
            inventory_record.quantity = batch.received_quantity
            inventory_record.reserved_quantity = 0
            inventory_record.expires_at = datetime.combine(
                batch.expiry_date, datetime.min.time()
            )
            product.stock = batch.received_quantity

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

            # Rebuild only the demo patient's synthetic history so repeated
            # SEED_DEMO_DATA runs stay deterministic and do not double-count sales.
            await session.execute(
                delete(PatientPurchase).where(PatientPurchase.patient_id == patient.id)
            )
            await session.execute(
                delete(Prescription).where(Prescription.patient_id == patient.id)
            )
            await session.execute(
                delete(PatientCondition).where(PatientCondition.patient_id == patient.id)
            )

            condition_name, icd10_code, profile_skus = PATIENT_PROFILES[index - 1]

            existing_condition = await session.scalar(
                select(PatientCondition).where(
                    PatientCondition.patient_id == patient.id,
                    PatientCondition.condition_name == condition_name,
                )
            )
            if existing_condition is None:
                session.add(
                    PatientCondition(
                        patient_id=patient.id,
                        condition_name=condition_name,
                        icd10_code=icd10_code,
                        severity="moderate",
                        status="active",
                        diagnosis_date=date(2024 + (index % 3), 1 + (index % 12), 15),
                        is_chronic=True,
                        treatment_notes="Synthetic demonstration condition; not clinical guidance.",
                    )
                )

            # Exactly six product lines per synthetic patient.
            receipt = f"DEMO-{index:03d}-01"
            for line_number, sku in enumerate(profile_skus, 1):
                spec = next(item for item in PRODUCT_CATALOG if item["sku"] == sku)
                product, batch, inventory_record = inventory[sku]
                packs = 1 + ((index + line_number) % 2)
                session.add(
                    PatientPurchase(
                        patient_id=patient.id,
                        product_id=product.id,
                        batch_id=batch.id,
                        receipt_number=receipt,
                        category="Prescription Medicine" if spec["rx"] else "OTC / Consumer Health",
                        quantity=packs,
                        dispensed_packs=packs,
                        dispensed_blisters=product.blisters_per_pack * packs,
                        dispensed_units=product.units_per_pack * packs,
                        unit_price=spec["price"],
                        prescription_required=spec["rx"],
                        purchased_at=datetime.utcnow() - timedelta(days=index % 5),
                    )
                )
                batch.available_quantity = max(0, batch.available_quantity - packs)
                inventory_record.quantity = batch.available_quantity
                product.stock = batch.available_quantity

            # One active synthetic prescription for every second patient.
            if index % 2 == 1:
                prescription_number = f"DEMO-RX-{index:03d}"
                existing_rx = await session.scalar(
                    select(Prescription).where(
                        Prescription.prescription_number == prescription_number
                    )
                )
                if existing_rx is None:
                    rx_spec = next(
                        spec for spec in PRODUCT_CATALOG
                        if spec["sku"] == profile_skus[0] and spec["rx"]
                    )
                    rx_product, _ = inventory[rx_spec["sku"]]
                    session.add(
                        Prescription(
                            patient_id=patient.id,
                            product_id=rx_product.id,
                            prescription_number=prescription_number,
                            dosage=rx_product.dosage_strength or "follow prescriber directions",
                            instructions="Synthetic demonstration prescription. Do not use as clinical guidance.",
                            status="active",
                            issued_at=datetime.utcnow() - timedelta(days=20),
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
