# C13: Natural Language Patient Search (MediSearch)

## What This Module Does
C13 provides natural-language patient search for the MediCare project.

Supported query examples:
- `"female patients over 40"`
- `"patients with migraine"`
- `"patients with heart disease"`
- `"patients in cardiology"`

The module includes:
- NL query parsing and synonym expansion
- PostgreSQL full-text search with `tsvector`
- Patient and admin search views (Streamlit)
- Cohort management and query history logging

---

## 1. Install PostgreSQL

### Ubuntu / Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### macOS (Homebrew)
```bash
brew install postgresql@15
brew services start postgresql@15
```

### Windows
Download and install from: https://www.postgresql.org/download/windows/

---

## 2. Create the Database

```bash
# Switch to the postgres user and open psql
sudo -u postgres psql

# Inside psql, run:
CREATE DATABASE projectdb;
\q
```

---

## 3. Configure Environment

Create a `.env` file in the project root (or `src/modules/C13/`):

**Option A — Local PostgreSQL (default):**
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=projectdb
DB_USER=postgres
DB_PASSWORD=postgres
```

**Option B — Hosted/Cloud PostgreSQL (e.g. Railway, Supabase):**
```env
DATABASE_URL=postgresql://username:password@host:port/db_name?sslmode=require
```

> Connection precedence: `DATABASE_URL` → `DATABASE_PUBLIC_URL` → individual `DB_*` vars.

---

## 4. Initialize the Schema

Load all tables, views, functions, and triggers into the database:

```bash
# Option A: Using the Python helper script
python src/modules/C13/db_init.py

# Option B: Using psql directly
psql -U postgres -d projectdb -f src/modules/C13/projectdb.sql
```

---

## 5. Insert Data into the Database

Import mock patients, search history, and cohorts:

```bash
python src/modules/C13/import_json_to_db.py
```

This will:
1. Insert **patients** from `mock_patients.json` (with symptoms, diagnoses, doctors, visits)
2. Import **search history** from `mock_history.json`
3. Create **patient cohorts** from `mock_cohorts.json`

---

## 6. Python Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 7. Run the App

**Standalone C13 UI:**
```bash
streamlit run src/modules/C13/run_c13.py --server.port 8502
```

**Full website (C13 via C1):**
```bash
streamlit run app.py --server.port 8501
```

---

## 8. Optional: Expand Dataset

Generate additional synthetic patient records:
```bash
python src/modules/C13/enhance_dataset.py --target 500
```

---

## Important Notes
- Keep `.env` out of version control (it's in `.gitignore`).
- Run `db_init.py` **before** `import_json_to_db.py` — schema must exist first.
- If searches return no results, verify DB connectivity with `verify_schema.py`.
- SSL is required for hosted PostgreSQL (`sslmode=require`).
