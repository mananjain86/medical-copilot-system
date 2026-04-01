# C13: Natural Language Patient Search

## What This Module Does
C13 provides a natural-language patient search flow for the MediCare project.
It supports queries like:
- "female patients over 40"
- "patients with migraine"
- "patients with heart disease"
- "patients in cardiology"

The module includes:
- NL query parsing and mapping logic
- PostgreSQL-backed patient search
- Patient and admin search views
- Optional synthetic dataset expansion script

## Quick Setup
From project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r src/modules/C13/requirements.txt
```

## Database Setup (PostgreSQL)
Prerequisite: Install PostgreSQL server and ensure the `psql` client is available in your shell `PATH`.

1. Ensure PostgreSQL is running.
2. Create `.env` in `src/modules/C13/`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=projectdb
DB_USER=gaurav
DB_PASSWORD=gaurav123
```

3. Import schema/data dump:

```bash
PGPASSWORD='gaurav123' /opt/homebrew/opt/postgresql@16/bin/psql -h localhost -U gaurav -d projectdb -f src/modules/C13/projectdb.sql
```

## Run Options
Standalone C13 UI:

```bash
streamlit run src/modules/C13/run_c13.py --server.port 8502
```

Full website (C13 is opened through C1):

```bash
streamlit run app.py --server.port 8501
```

## Optional: Expand Dataset
To add synthetic records for richer search results:

```bash
python src/modules/C13/enhance_dataset.py --target 500
```
