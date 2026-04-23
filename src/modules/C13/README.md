# C13: Natural Language Patient Search (MediSearch)

## What This Module Does

C13 provides natural-language patient search for the MediCare project.

Supported query examples:
- `"female patients over 40"`
- `"patients with fatigue"`
- `"patients with heart disease"`
- `"patients in cardiology department"`

The module includes:
- NL query parsing and synonym expansion
- Dynamic SQL generation from natural language
- Patient and admin search views (Streamlit)
- Cohort management and query history logging

---

## Prerequisites

- Python 3.10+
- A PostgreSQL database — either **local** or **Supabase (recommended)**

---

## 1. Clone the Repository

```bash
git clone https://github.com/mananjain86/medical-copilot-system.git
cd medical-copilot-system
```

---

## 2. Set Up Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 3. Configure the Database (.env)

Create a `.env` file in the **project root** (`medical-copilot-system/.env`).

### Option A — Supabase (Recommended)

```env
# Supabase Configuration
DATABASE_URL="postgresql://<user>:<password>@<host>:5432/postgres?sslmode=require"
DATABASE_PUBLIC_URL="postgresql://<user>:<password>@<host>:5432/postgres?sslmode=require"

DB_HOST=<your-supabase-pooler-host>
DB_PORT=5432
DB_NAME=postgres
DB_USER=<your-supabase-user>
DB_PASSWORD=<your-supabase-password>
DB_SSLMODE=require
```

> Get these values from your Supabase project → **Settings → Database → Connection string (URI)**.

### Option B — Local PostgreSQL

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=projectdb
DB_USER=postgres
DB_PASSWORD=yourpassword
```

> Connection precedence: `DATABASE_URL` → `DATABASE_PUBLIC_URL` → individual `DB_*` vars.

---

## 4. Initialize the Database Schema

Load all tables, views, functions, and triggers:

```bash
# Run from the project root
python src/modules/C13/db_init.py
```

Or directly with psql (local only):

```bash
psql -U postgres -d projectdb -f src/modules/C13/projectdb.sql
```

---

## 5. Import Patient Data

```bash
python src/modules/C13/import_json_to_db.py
```

This inserts 400 patients with visits, symptoms, diagnoses, and doctors into the database.

> **Order matters:** Run `db_init.py` first (schema), then `import_json_to_db.py` (data).

---

## 6. Run Locally

The app needs **two processes** running at the same time.

### Terminal 1 — Start the FastAPI Backend

```bash
# From the project root
venv/bin/uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2 — Start the Streamlit UI

```bash
# Standalone C13 UI
streamlit run src/modules/C13/run_c13.py --server.port 8502

# OR full app
streamlit run app.py --server.port 8501
```

Open your browser at: **http://localhost:8502** (or 8501 for full app)

---

## 7. How the Search Works

```
User types a query (e.g. "female patients over 60 with diabetes")
    ↓
Streamlit → POST /api/v1/search
    ↓
FastAPI → backend.py pipeline:
  1. parse_query()        Extract gender / age / symptom from text
  2. expand_terms()       Synonym expansion via DB synonyms table
  3. resolve_symptom()    Match to canonical symptom name in DB
  4. resolve_diagnosis()  Match to diagnosis values in visits table
  5. generate_sql()       Build dynamic SQL
  6. run_search()         Execute SQL on DB, log to search_queries table
  7. create_cohort()      Save matching patients as a cohort
    ↓
Returns: patient results + generated SQL + cohort ID
```

The **"🔍 Generated SQL Query"** panel appears automatically after every search showing the exact SQL executed.

> **If the API is not running:** The app falls back to mock/demo data for results, but still generates and shows SQL directly from the database.

---

## 8. Verify Connection

```bash
python3 -c "
from src.modules.C13.backend import get_connection, _DB_HOST
conn = get_connection()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM patients')
print(f'Connected to: {_DB_HOST}')
print(f'Patients in DB: {cur.fetchone()[0]}')
conn.close()
"
```

---

## Important Notes

- Keep `.env` out of version control — it is already in `.gitignore`
- The API server (`uvicorn`) and Streamlit must both be running for full functionality
- SSL (`sslmode=require`) is mandatory for Supabase connections
- First search may take 10–15 seconds due to Supabase network latency (multiple DB round trips)
- `db_init.py` must be run **before** `import_json_to_db.py`
