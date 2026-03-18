"""
Expand the C13 PostgreSQL dataset with realistic synthetic records.

This script is idempotent by phone-prefix marker and target count:
- It creates synthetic patients with phone numbers starting with "9000".
- Re-running only tops up to the requested synthetic target size.

Usage:
    source .venv/bin/activate
    python src/modules/C13/enhance_dataset.py --target 400
"""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.modules.C13.backend import get_connection


FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna", "Ishaan", "Rohan",
    "Aanya", "Diya", "Saanvi", "Myra", "Ananya", "Ira", "Meera", "Riya", "Kavya", "Siya",
    "Rahul", "Amit", "Nikhil", "Suresh", "Karan", "Manish", "Deepak", "Ravi", "Ajay", "Vikram",
    "Priya", "Pooja", "Neha", "Sneha", "Anita", "Shreya", "Nisha", "Komal", "Preeti", "Tanya",
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Mehta", "Singh", "Gupta", "Reddy", "Nair", "Iyer", "Khan",
    "Malhotra", "Joshi", "Kapoor", "Bansal", "Chopra", "Mishra", "Yadav", "Jain", "Das", "Kulkarni",
]

CITIES = ["Mumbai", "Delhi", "Kolkata", "Chennai", "Hyderabad", "Ahmedabad", "Kochi"]

DIAGNOSES = [
    "asthma",
    "bronchitis",
    "chest pain",
    "diabetes",
    "fatigue",
    "flu",
    "headache",
    "migraine",
    "nausea",
    "viral fever",
]

DIAGNOSIS_TO_SYMPTOMS = {
    "asthma": ["shortness of breath", "cough"],
    "bronchitis": ["cough", "fatigue"],
    "chest pain": ["chest pain", "shortness of breath"],
    "diabetes": ["fatigue"],
    "fatigue": ["fatigue"],
    "flu": ["fever", "cough", "fatigue"],
    "headache": ["headache"],
    "migraine": ["headache", "nausea"],
    "nausea": ["nausea"],
    "viral fever": ["fever", "fatigue"],
}

DIAGNOSIS_TO_SPECIALIZATION = {
    "asthma": "Pulmonology",
    "bronchitis": "Pulmonology",
    "chest pain": "Cardiology",
    "diabetes": "Endocrinology",
    "fatigue": "General Medicine",
    "flu": "General Medicine",
    "headache": "Neurology",
    "migraine": "Neurology",
    "nausea": "General Medicine",
    "viral fever": "General Medicine",
}

LAB_TEST_BY_DIAGNOSIS = {
    "diabetes": "glucose",
    "chest pain": "cholesterol",
    "asthma": "hemoglobin",
    "bronchitis": "hemoglobin",
    "fatigue": "hemoglobin",
    "flu": "hemoglobin",
    "headache": "hemoglobin",
    "migraine": "hemoglobin",
    "nausea": "glucose",
    "viral fever": "glucose",
}


def random_dob(min_age: int = 18, max_age: int = 85) -> date:
    today = date.today()
    start = today - timedelta(days=max_age * 365)
    end = today - timedelta(days=min_age * 365)
    return start + timedelta(days=random.randint(0, (end - start).days))


def random_visit_date() -> date:
    today = date.today()
    return today - timedelta(days=random.randint(0, 730))


def random_lab_value(test_name: str) -> float:
    if test_name == "glucose":
        return float(random.randint(80, 260))
    if test_name == "cholesterol":
        return float(random.randint(140, 300))
    return float(random.randint(9, 18))


def enhance_dataset(target_synthetic_patients: int, seed: int = 42) -> dict[str, int]:
    random.seed(seed)

    conn = get_connection()
    counters = {"patients": 0, "visits": 0, "patient_symptoms": 0, "lab_results": 0}

    with conn.cursor() as cur:
        # Lookup maps
        cur.execute("SELECT symptom_id, symptom_name FROM symptoms")
        symptom_id_by_name = {name: sid for sid, name in cur.fetchall()}

        cur.execute("SELECT test_id, test_name FROM lab_tests")
        test_id_by_name = {name: tid for tid, name in cur.fetchall()}

        cur.execute("SELECT doctor_id, specialization FROM doctors")
        doctors_by_spec: dict[str, list[int]] = {}
        for doc_id, spec in cur.fetchall():
            doctors_by_spec.setdefault(spec, []).append(doc_id)

        cur.execute("SELECT doctor_id FROM doctors ORDER BY doctor_id")
        all_doctors = [row[0] for row in cur.fetchall()]

        cur.execute("SELECT COUNT(*) FROM patients WHERE phone LIKE '9000%'")
        existing_synthetic = cur.fetchone()[0]
        to_add = max(0, target_synthetic_patients - existing_synthetic)

        # Build deterministic unique phone numbers for marker-prefixed synthetic rows.
        cur.execute("SELECT COALESCE(MAX(patient_id), 0) FROM patients")
        max_patient_id = cur.fetchone()[0]

        for i in range(to_add):
            gender = random.choice(["male", "female"])
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            dob = random_dob()
            city = random.choice(CITIES)

            # 10-digit marker phone, guaranteed distinct by sequence offset.
            phone = f"9000{max_patient_id + i + 1:06d}"[-10:]

            cur.execute(
                """
                INSERT INTO patients (first_name, last_name, gender, date_of_birth, phone, city)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING patient_id
                """,
                (first_name, last_name, gender, dob, phone, city),
            )
            patient_id = cur.fetchone()[0]
            counters["patients"] += 1

            visit_count = random.randint(1, 3)
            for _ in range(visit_count):
                diagnosis = random.choice(DIAGNOSES)
                specialization = DIAGNOSIS_TO_SPECIALIZATION.get(diagnosis, "General Medicine")
                doctor_choices = doctors_by_spec.get(specialization) or all_doctors
                doctor_id = random.choice(doctor_choices)

                cur.execute(
                    """
                    INSERT INTO visits (patient_id, doctor_id, visit_date, diagnosis, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING visit_id
                    """,
                    (patient_id, doctor_id, random_visit_date(), diagnosis, "Synthetic expanded dataset record"),
                )
                visit_id = cur.fetchone()[0]
                counters["visits"] += 1

                # Attach 1-2 symptoms relevant to diagnosis.
                symptom_names = DIAGNOSIS_TO_SYMPTOMS.get(diagnosis, ["fatigue"])
                sample_size = 1 if len(symptom_names) == 1 else random.randint(1, 2)
                for symptom_name in random.sample(symptom_names, k=sample_size):
                    symptom_id = symptom_id_by_name.get(symptom_name)
                    if symptom_id is None:
                        continue
                    cur.execute(
                        "INSERT INTO patient_symptoms (visit_id, symptom_id) VALUES (%s, %s)",
                        (visit_id, symptom_id),
                    )
                    counters["patient_symptoms"] += 1

                # Add a lab result for most visits.
                if random.random() < 0.8:
                    test_name = LAB_TEST_BY_DIAGNOSIS.get(diagnosis, "hemoglobin")
                    test_id = test_id_by_name.get(test_name)
                    if test_id is not None:
                        cur.execute(
                            """
                            INSERT INTO lab_results (visit_id, test_id, result_value, result_date)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (visit_id, test_id, random_lab_value(test_name), random_visit_date()),
                        )
                        counters["lab_results"] += 1

    conn.commit()
    conn.close()

    counters["synthetic_target"] = target_synthetic_patients
    counters["added_patients"] = to_add
    return counters


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand C13 dataset with synthetic records")
    parser.add_argument("--target", type=int, default=400, help="Target synthetic patient count (phone prefix 9000)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    stats = enhance_dataset(target_synthetic_patients=args.target, seed=args.seed)
    print("Dataset enhancement complete:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
