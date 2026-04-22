import sys
from pathlib import Path

# Add project root to path so src modules can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.modules.C13.backend import (
    get_connection,
    nl_search_pipeline,
    get_search_history,
    get_saved_queries,
    save_query,
    get_cohorts,
    get_cohort_members
)

app = FastAPI(
    title="Medical Copilot API",
    description="API for the Medical Copilot System and Natural Language Patient Search",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB connection
def get_db():
    try:
        conn = get_connection()
        try:
            yield conn
        finally:
            conn.close()
    except Exception as e:
        # If DB fails, yield None so endpoints can handle fallback
        yield None

# Request Models
class SearchRequest(BaseModel):
    user_id: int
    query: str

class SaveQueryRequest(BaseModel):
    user_id: int
    query_text: str

# Endpoints
from fastapi.encoders import jsonable_encoder

@app.post("/api/v1/search")
def search_patients(req: SearchRequest, db=Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection failed (None yielded from get_db)")
    
    try:
        result = nl_search_pipeline(db, req.user_id, req.query)
        return jsonable_encoder(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search pipeline failed: {str(e)}")

@app.get("/api/v1/history/{user_id}")
def get_history(user_id: int, db=Depends(get_db)):
    try:
        return get_search_history(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/saved-queries/{user_id}")
def get_saved(user_id: int, db=Depends(get_db)):
    try:
        return get_saved_queries(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/saved-queries")
def save_user_query(req: SaveQueryRequest, db=Depends(get_db)):
    try:
        save_query(db, req.user_id, req.query_text)
        return {"status": "success", "message": "Query saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/cohorts")
def list_cohorts(db=Depends(get_db)):
    try:
        return get_cohorts(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/cohorts/{cohort_id}/members")
def get_members(cohort_id: int, limit: int = 200, db=Depends(get_db)):
    try:
        return get_cohort_members(db, cohort_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/patients/{patient_id}/details")
def get_patient_details(patient_id: int, db=Depends(get_db)):
    try:
        with db.cursor() as cur:
            cur.execute(
                """
                SELECT
                    p.patient_id,
                    p.first_name,
                    p.last_name,
                    p.gender,
                    DATE_PART('year', AGE(p.date_of_birth))::int AS age,
                    p.city
                FROM patients p
                WHERE p.patient_id = %s
                """,
                (patient_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Patient not found")

            cur.execute(
                """
                SELECT
                    v.visit_date,
                    v.diagnosis,
                    COALESCE(d.specialization, 'General Medicine') AS department,
                    COALESCE(d.doctor_name, 'Unknown Doctor') AS doctor_name
                FROM visits v
                LEFT JOIN doctors d ON d.doctor_id = v.doctor_id
                WHERE v.patient_id = %s
                ORDER BY v.visit_date DESC
                LIMIT 20
                """,
                (patient_id,),
            )
            visits = [
                {
                    "visit_date": str(v[0]),
                    "diagnosis": v[1],
                    "department": v[2],
                    "doctor_name": v[3],
                }
                for v in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT DISTINCT s.symptom_name
                FROM visits v
                JOIN patient_symptoms ps ON ps.visit_id = v.visit_id
                JOIN symptoms s ON s.symptom_id = ps.symptom_id
                WHERE v.patient_id = %s
                ORDER BY s.symptom_name
                LIMIT 12
                """,
                (patient_id,),
            )
            symptoms = [r[0] for r in cur.fetchall()]

            cur.execute(
                """
                SELECT
                    COALESCE(d.doctor_name, 'Unknown Doctor') AS doctor_name,
                    COUNT(*)::int AS visit_count
                FROM visits v
                LEFT JOIN doctors d ON d.doctor_id = v.doctor_id
                WHERE v.patient_id = %s
                GROUP BY COALESCE(d.doctor_name, 'Unknown Doctor')
                ORDER BY visit_count DESC, doctor_name
                """,
                (patient_id,),
            )
            doctor_visits = [
                {"doctor_name": r[0], "visit_count": r[1]}
                for r in cur.fetchall()
            ]

            diagnoses = sorted({(v.get("diagnosis") or "").strip() for v in visits if v.get("diagnosis")})

        return {
            "id": row[0],
            "name": f"{row[1]} {row[2]}".strip(),
            "gender": row[3],
            "age": row[4],
            "city": row[5],
            "visits": visits,
            "visit_count": len(visits),
            "doctor_visits": doctor_visits,
            "diagnoses": diagnoses,
            "symptoms": symptoms,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
