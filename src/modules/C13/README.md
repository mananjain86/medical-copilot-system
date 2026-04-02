# C13: Natural Language Patient Search

## What This Module Does
C13 provides natural-language patient search for the MediCare project.

Supported query examples:
- "female patients over 40"
- "patients with migraine"
- "patients with heart disease"
- "patients in cardiology"

The module includes:
- NL query parsing and mapping
- PostgreSQL-backed patient search
- Patient and admin search views
- Optional synthetic dataset expansion

## Quick Setup
From project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Database Setup (PostgreSQL)
C13 supports DSN-based connection for hosted PostgreSQL and does not require local psql CLI at runtime.

1. Create `src/modules/C13/.env`.

2. Use one of the following connection styles.

Preferred (hosted DB):

```env
# Primary DSN (used first)
DATABASE_URL=postgresql://<username>:<password>@<host>:<port>/<db_name>?sslmode=require

# Optional fallback DSN (used only if DATABASE_URL is missing)
DATABASE_PUBLIC_URL=postgresql://<username>:<password>@<public_host>:<port>/<db_name>?sslmode=require
```

Fallback (used when DSN is not set):

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=projectdb
DB_USER=postgres
DB_PASSWORD=1234
DB_SSLMODE=require
```

Connection precedence in backend:
1. `DATABASE_URL`
2. `DATABASE_PUBLIC_URL`
3. `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (and optional `DB_SSLMODE`)

3. Optional one-time schema/data import (only if DB is empty):

```bash
python -c "from src.modules.C13.backend import initialize_projectdb; print(initialize_projectdb())"
```

## Run Options
Standalone C13 UI:

```bash
streamlit run src/modules/C13/run_c13.py --server.port 8502
```

Full website (C13 opened via C1):

```bash
streamlit run app.py --server.port 8501
```

## Optional: Expand Dataset
Generate synthetic records for richer results:

```bash
python src/modules/C13/enhance_dataset.py --target 500
```

## Important Notes
- Keep `.env` out of version control.
- If using hosted PostgreSQL, keep SSL enabled (`sslmode=require` or `DB_SSLMODE=require`).
- If searches return no results, verify DB connectivity and that schema/data were initialized.
