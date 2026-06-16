"""
seed_database.py
Run this ONCE to populate MongoDB with 50 synthetic patients and 20 staff.

Usage on the VM (after containers are up):
    pip install pymongo faker
    python3 seed_database.py
"""

import random
import json
from datetime import datetime, timedelta
from pymongo import MongoClient
from faker import Faker

fake = Faker()

MONGO_URI = "mongodb://admin:hospital123@localhost:27017/sunrise_hospital?authSource=admin"
client = MongoClient(MONGO_URI)
db = client["sunrise_hospital"]

DIAGNOSES = [
    "Type 2 Diabetes", "Hypertension", "Asthma",
    "Chronic Kidney Disease", "Coronary Artery Disease",
    "Appendicitis", "Pneumonia", "Fractured Femur",
    "Major Depressive Disorder", "Hypothyroidism",
    "Sepsis", "Stroke", "Pulmonary Embolism"
]

MEDICATIONS = [
    "Metformin 500mg", "Lisinopril 10mg", "Salbutamol inhaler",
    "Atorvastatin 20mg", "Aspirin 75mg", "Amoxicillin 500mg",
    "Sertraline 50mg", "Levothyroxine 50mcg", "Warfarin 5mg",
    "Insulin Glargine 10 units", "Furosemide 40mg"
]

WARDS = [
    "Ward A - Cardiology", "Ward B - General Medicine",
    "Ward C - Surgery", "Ward D - Psychiatry",
    "Ward E - Paediatrics", "ICU"
]

BLOOD_TYPES = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]

def random_sri_lankan_nic(dob):
    year_part = str(dob.year)[2:]
    day_of_year = dob.timetuple().tm_yday
    if dob.year < 2000:
        return f"{year_part}{day_of_year:03d}{random.randint(1000, 9999)}V"
    return f"{dob.year}{day_of_year:03d}{random.randint(1000, 9999)}"

def generate_patients(count=50):
    patients = []
    for i in range(count):
        dob = fake.date_of_birth(minimum_age=18, maximum_age=85)
        admission = datetime.now() - timedelta(days=random.randint(0, 30))
        diagnosis = random.choice(DIAGNOSES)
        patients.append({
            "patient_id":          f"PT{1000 + i}",
            "name":                fake.name(),
            "dob":                 dob.strftime("%Y-%m-%d"),
            "nic":                 random_sri_lankan_nic(dob),
            "phone":               f"07{random.randint(10000000, 99999999)}",
            "address":             fake.address().replace("\n", ", "),
            "blood_type":          random.choice(BLOOD_TYPES),
            "ward":                random.choice(WARDS),
            "bed_number":          random.randint(1, 20),
            "diagnosis":           diagnosis,
            "medications":         random.sample(MEDICATIONS, k=random.randint(1, 4)),
            "attending_doctor":    f"Dr. {fake.last_name()}",
            "admission_date":      admission.strftime("%Y-%m-%d"),
            "insurance_id":        f"INS{random.randint(100000, 999999)}",
            "emergency_contact":   fake.name(),
            "emergency_phone":     f"07{random.randint(10000000, 99999999)}",
            "clinical_notes":      f"Patient admitted with {diagnosis.lower()}. Stable, responding to treatment.",
            "allergies":           random.choice(["Penicillin", "Sulfa drugs", "None known", "Latex", "Aspirin"]),
            "created_at":          datetime.utcnow()
        })
    return patients

def generate_staff(count=20):
    roles = ["Doctor", "Nurse", "Senior Nurse", "Pharmacist", "Admin Staff", "Lab Technician"]
    return [{
        "staff_id":   f"ST{200 + i}",
        "name":       fake.name(),
        "role":       random.choice(roles),
        "department": random.choice(WARDS),
        "username":   fake.user_name(),
        "email":      fake.company_email(),
        "created_at": datetime.utcnow()
    } for i in range(count)]

def main():
    print("Seeding Sunrise General Hospital database...")
    db.patients.drop()
    db.staff.drop()

    patients = generate_patients(50)
    db.patients.insert_many(patients)
    print(f"  Inserted {len(patients)} patients")

    staff = generate_staff(20)
    db.staff.insert_many(staff)
    print(f"  Inserted {len(staff)} staff")

    db.patients.create_index("patient_id", unique=True)
    db.patients.create_index("ward")
    db.staff.create_index("staff_id", unique=True)

    sample = db.patients.find_one({}, {"_id": 0})
    print("\nSample patient:")
    print(json.dumps(sample, indent=2, default=str))
    print("\nDone. View at http://<vm-ip>:8081")

if __name__ == "__main__":
    main()
