"""
Load C13 dataset records from mock_patients.json into PostgreSQL.

This script intentionally avoids random/synthetic generation.
It uses deterministic transforms from src/modules/C13/mock_patients.json.

Usage:
    source .venv/bin/activate
    python src/modules/C13/enhance_dataset.py --limit 200
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.modules.C13.backend import get_connection

MOCK_JSON_PATH = Path(__file__).with_name("mock_patients.json")

LAB_TEST_BY_KEYWORD = {
    "diabetes": ("glucose", 165.0),
    "cholesterol": ("cholesterol", 220.0),
    "cardiac": ("cholesterol", 230.0),
    "heart": ("cholesterol", 230.0),
    "asthma": ("hemoglobin", 12.0),
    "bronch": ("hemoglobin", 11.5),
}


def _load_mock_records() -> list[dict]:
    if not MOCK_JSON_PATH.exists():
        raise FileNotFoundError(f"Missing mock data file: {MOCK_JSON_PATH}")
    data = json.loads(MOCK_JSON_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("mock_patients.json must contain a list of patient objects")
    return data


def _safe_age(raw_age: object) -> int:
    try:
        age = int(raw_age)
    except Exception:
        return 40
    return min(95, max(1, age))


def _gender_value(raw_gender: object) -> str:
    g = str(raw_gender or "").strip().lower()
    if g in {"male", "female"}:
        return g
    return "male"


def _name_parts(full_name: object) -> tuple[str, str]:
    parts = str(full_name or "Unknown Patient").strip().split()
    if not parts:
        return "Unknown", "Patient"
    if len(parts) == 1:
        return parts[0], "Patient"
    return parts[0], " ".join(parts[1:])


def _city_from_record(item: dict) -> str:
    return str(item.get("city") or "Mumbai").strip() or "Mumbai"


def _visit_date(raw_date: object) -> date:
    text = str(raw_date or "").strip()
    if text:
        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            pass
    return date.today() - timedelta(days=30)


def _phone_from_mock_id(mock_id: object, fallback_index: int) -> str:
    text = str(mock_id or "").strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        digits = str(fallback_index)
    # Stable 10-digit number with 9000 marker prefix.
    return ("9000" + digits.zfill(6))[-10:]


def _pick_diagnosis(item: dict) -> str:
    diagnoses = item.get("diagnoses") or []
    if isinstance(diagnoses, list) and diagnoses:
        return str(diagnoses[0]).strip() or "General Checkup"
    symptoms = item.get("symptoms") or []
    if isinstance(symptoms, list) and symptoms:
        return str(symptoms[0]).strip() or "General Checkup"
    return "General Checkup"


def _lookup_specialization(department: str, diagnosis: str) -> str:
    dep = (department or "").lower()
    diag = (diagnosis or "").lower()
    if "card" in dep or "heart" in diag:
        return "Cardiology"
    if "neuro" in dep:
        return "Neurology"
    if "pulmo" in dep or "asth" in diag or "bronch" in diag:
        return "Pulmonology"
    if "endo" in dep or "diabet" in diag:
        return "Endocrinology"
    if "rheum" in dep or "arth" in diag:
        return "Rheumatology"
    if "ortho" in dep or "back" in diag:
        return "Orthopedics"
    return "General Medicine"


def _ensure_symptom(cur, symptom_name: str) -> int:
    cur.execute("SELECT symptom_id FROM symptoms WHERE LOWER(symptom_name) = LOWER(%s) LIMIT 1", (symptom_name,))
    row = cur.fetchone()
    if row:
        return int(row[0])

    cur.execute(
        "INSERT INTO symptoms(symptom_name) VALUES(%s) RETURNING symptom_id",
        (symptom_name,),
    )
    return int(cur.fetchone()[0])


def _maybe_add_lab_result(cur, visit_id: int, diagnosis: str, visit_dt: date) -> int:
    diag = diagnosis.lower()
    test_name = None
    test_value = None
    for key, (name, value) in LAB_TEST_BY_KEYWORD.items():
        if key in diag:
            test_name = name
            test_value = value
            break

    if not test_name:
        return 0

    cur.execute("SELECT test_id FROM lab_tests WHERE LOWER(test_name) = LOWER(%s) LIMIT 1", (test_name,))
    row = cur.fetchone()
    if not row:
        return 0

    test_id = int(row[0])
    cur.execute(
        """
        SELECT 1 FROM lab_results
        WHERE visit_id = %s AND test_id = %s
        LIMIT 1
        """,
        (visit_id, test_id),
    )
    if cur.fetchone():
        return 0

    cur.execute(
        """
        INSERT INTO lab_results(visit_id, test_id, result_value, result_date)
        VALUES (%s, %s, %s, %s)
        """,
        (visit_id, test_id, test_value, visit_dt),
    )
    return 1


def _sync_serial_sequence(cur, table_name: str, pk_column: str) -> None:
    cur.execute("SELECT pg_get_serial_sequence(%s, %s)", (table_name, pk_column))
    row = cur.fetchone()
    if not row or not row[0]:
        return
    seq_name = row[0]

    cur.execute(f"SELECT COALESCE(MAX({pk_column}), 0) FROM {table_name}")
    max_id = int(cur.fetchone()[0] or 0)
    cur.execute("SELECT setval(%s, %s, false)", (seq_name, max(1, max_id + 1)))


def import_mock_patients(limit: int | None = None) -> dict[str, int]:
    records = _load_mock_records()
    if limit is not None and limit > 0:
        records = records[:limit]

    conn = get_connection()
    counters = {
        "patients_upserted": 0,
        "visits_upserted": 0,
        "patient_symptoms_upserted": 0,
        "lab_results_upserted": 0,
        "records_processed": len(records),
    }

    with conn.cursor() as cur:
        _sync_serial_sequence(cur, "patients", "patient_id")
        _sync_serial_sequence(cur, "visits", "visit_id")
        _sync_serial_sequence(cur, "symptoms", "symptom_id")
        _sync_serial_sequence(cur, "lab_results", "result_id")

        cur.execute("SELECT doctor_id FROM doctors ORDER BY doctor_id LIMIT 1")
        first_doc = cur.fetchone()
        if not first_doc:
            raise RuntimeError("No doctors found in database. Seed doctors before importing mock patients.")
        fallback_doctor_id = int(first_doc[0])

        for idx, item in enumerate(records, start=1):
            first_name, last_name = _name_parts(item.get("name"))
            gender = _gender_value(item.get("gender"))
            age = _safe_age(item.get("age"))
            dob = date.today() - timedelta(days=age * 365)
            phone = _phone_from_mock_id(item.get("id"), idx)
            city = _city_from_record(item)
            department = str(item.get("department") or "").strip()
            diagnosis = _pick_diagnosis(item)
            visit_dt = _visit_date(item.get("admission_date"))

            cur.execute(
                "SELECT patient_id FROM patients WHERE phone = %s LIMIT 1",
                (phone,),
            )
            row = cur.fetchone()
            if row:
                patient_id = int(row[0])
                cur.execute(
                    """
                    UPDATE patients
                    SET first_name = %s,
                        last_name = %s,
                        gender = %s,
                        date_of_birth = %s,
                        city = %s
                    WHERE patient_id = %s
                    """,
                    (first_name, last_name, gender, dob, city, patient_id),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO patients(first_name, last_name, gender, date_of_birth, phone, city)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING patient_id
                    """,
                    (first_name, last_name, gender, dob, phone, city),
                )
                patient_id = int(cur.fetchone()[0])

            counters["patients_upserted"] += 1

            specialization = _lookup_specialization(department, diagnosis)
            cur.execute(
                "SELECT doctor_id FROM doctors WHERE LOWER(specialization) = LOWER(%s) ORDER BY doctor_id LIMIT 1",
                (specialization,),
            )
            drow = cur.fetchone()
            doctor_id = int(drow[0]) if drow else fallback_doctor_id

            cur.execute(
                """
                SELECT visit_id FROM visits
                WHERE patient_id = %s AND visit_date = %s AND LOWER(diagnosis) = LOWER(%s)
                LIMIT 1
                """,
                (patient_id, visit_dt, diagnosis),
            )
            vrow = cur.fetchone()
            if vrow:
                visit_id = int(vrow[0])
            else:
                cur.execute(
                    """
                    INSERT INTO visits(patient_id, doctor_id, visit_date, diagnosis, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING visit_id
                    """,
                    (patient_id, doctor_id, visit_dt, diagnosis, "Imported from mock_patients.json"),
                )
                visit_id = int(cur.fetchone()[0])
                counters["visits_upserted"] += 1

            symptoms = item.get("symptoms") if isinstance(item.get("symptoms"), list) else []
            for symptom in symptoms:
                symptom_name = str(symptom).strip()
                if not symptom_name:
                    continue
                symptom_id = _ensure_symptom(cur, symptom_name)
                cur.execute(
                    """
                    INSERT INTO patient_symptoms(visit_id, symptom_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (visit_id, symptom_id),
                )
                counters["patient_symptoms_upserted"] += cur.rowcount

            counters["lab_results_upserted"] += _maybe_add_lab_result(cur, visit_id, diagnosis, visit_dt)

    conn.commit()
    conn.close()
    return counters


def main() -> None:
    parser = argparse.ArgumentParser(description="Import mock_patients.json into C13 PostgreSQL")
    parser.add_argument("--limit", type=int, default=0, help="Optional number of records to import from mock_patients.json")
    args = parser.parse_args()

    limit = args.limit if args.limit and args.limit > 0 else None
    stats = import_mock_patients(limit=limit)

    print("Mock patient import complete:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
