"""
Migration script to import data from mock_patients.json, mock_history.json, 
and mock_cohorts.json into the projectdb PostgreSQL database.
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Fix path to allow importing from src.modules.C13
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.modules.C13.backend import get_connection

DATA_DIR = Path(__file__).resolve().parent

def import_patients(conn):
    print("Importing patients...")
    path = DATA_DIR / "mock_patients.json"
    if not path.exists():
        print(f"Skipping patients: {path} not found")
        return

    with open(path, 'r') as f:
        data = json.load(f)

    with conn.cursor() as cur:
        print("Cleaning up existing visits, patient symptoms, and doctors...")
        cur.execute("TRUNCATE TABLE patient_symptoms, visits, doctors RESTART IDENTITY CASCADE;")
        
        for p in data:
            # Map P001 -> 1
            pid_str = p.get("id", "0")
            pid = int(pid_str[1:]) if pid_str.startswith("P") else int(pid_str)
            
            fullname = p.get("name", "Unknown")
            parts = fullname.split()
            fname = parts[0]
            lname = " ".join(parts[1:]) if len(parts) > 1 else ""
            
            gender = p.get("gender", "Other").lower()
            age = p.get("age", 40)
            # Approximate DOB assuming current year is 2026
            dob = datetime(2026 - age, 1, 1).date()
            
            symptoms = ", ".join(p.get("symptoms", []))
            diagnoses = ", ".join(p.get("diagnoses", []))
            status = p.get("status", "Active")
            
            cur.execute(
                """
                INSERT INTO patients (patient_id, first_name, last_name, gender, date_of_birth, city, status, symptoms, diagnoses, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (patient_id) DO UPDATE SET
                    city = EXCLUDED.city,
                    status = EXCLUDED.status,
                    symptoms = EXCLUDED.symptoms,
                    diagnoses = EXCLUDED.diagnoses,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name
                """,
                (pid, fname, lname, gender, dob, p.get("city", "New York"), status, symptoms, diagnoses, datetime.now())
            )
            
            # Map symptoms to the symptoms table
            for s_name in p.get("symptoms", []):
                cur.execute("INSERT INTO symptoms (symptom_name) VALUES (%s) ON CONFLICT DO NOTHING", (s_name,))
                
            # Handle doctor/physician
            physician = p.get("physician", "Unknown Doctor")
            dept = p.get("department", "General Medicine")
            cur.execute(
                "INSERT INTO doctors (doctor_name, specialization) VALUES (%s, %s) ON CONFLICT (doctor_name) DO NOTHING",
                (physician, dept)
            )
            cur.execute("SELECT doctor_id FROM doctors WHERE doctor_name = %s", (physician,))
            did = cur.fetchone()[0]

            # Create a visit record
            cur.execute(
                "INSERT INTO visits (patient_id, doctor_id, visit_date, diagnosis) VALUES (%s, %s, %s, %s) RETURNING visit_id",
                (pid, did, p.get("admission_date", "2024-01-01"), diagnoses)
            )
            visit_id = cur.fetchone()[0]
            
            # Map patient to symptoms via visit
            for s_name in p.get("symptoms", []):
                cur.execute("SELECT symptom_id FROM symptoms WHERE symptom_name = %s", (s_name,))
                sid = cur.fetchone()[0]
                cur.execute("INSERT INTO patient_symptoms (visit_id, symptom_id) VALUES (%s, %s)", (visit_id, sid))
    conn.commit()
    print(f"Imported {len(data)} patients.")

def import_history(conn):
    print("Importing history...")
    path = DATA_DIR / "mock_history.json"
    if not path.exists():
        print(f"Skipping history: {path} not found")
        return

    with open(path, 'r') as f:
        data = json.load(f)

    with conn.cursor() as cur:
        for h in data:
            query = h.get("query_text")
            stype = h.get("search_type", "Mock Search")
            created_at = h.get("created_at")
            
            # Use user_id 1 (Clinician)
            cur.execute(
                "INSERT INTO search_queries (user_id, query_text, search_type, created_at) VALUES (%s, %s, %s, %s)",
                (1, query, stype, created_at)
            )
    conn.commit()
    print(f"Imported {len(data)} history items.")

def import_cohorts(conn):
    print("Importing cohorts...")
    path = DATA_DIR / "mock_cohorts.json"
    if not path.exists():
        print(f"Skipping cohorts: {path} not found")
        return

    with open(path, 'r') as f:
        data = json.load(f)

    with conn.cursor() as cur:
        for c in data:
            name = c.get("cohort_name")
            created_at = c.get("created_at")
            members = c.get("members", [])
            
            cur.execute(
                "INSERT INTO patient_cohorts (cohort_name, created_at) VALUES (%s, %s) RETURNING cohort_id",
                (name, created_at)
            )
            cohort_id = cur.fetchone()[0]
            
            for m in members:
                pid_str = m.get("id", "0")
                pid = int(pid_str[1:]) if pid_str.startswith("P") else int(pid_str)
                
                # Check if patient exists (foreign key constraint)
                cur.execute("SELECT 1 FROM patients WHERE patient_id = %s", (pid,))
                if not cur.fetchone():
                    continue
                
                cur.execute(
                    "INSERT INTO patient_cohort_members (cohort_id, patient_id, added_at) VALUES (%s, %s, %s)",
                    (cohort_id, pid, created_at)
                )
    conn.commit()
    print(f"Imported {len(data)} cohorts.")

def main():
    try:
        conn = get_connection()
        import_patients(conn)
        import_history(conn)
        import_cohorts(conn)
        conn.close()
        print("--- Migration Finished ---")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
