Live Demo: 👉 [https://frontend-zxra8c5w4ip3f6k5gvjasp.streamlit.app/](https://frontend-zxra8c5w4ip3f6k5gvjasp.streamlit.app/)

## Local Setup

1. Create and activate virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure database environment variables in `.env`.

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=projectdb
DB_USER=gaurav
DB_PASSWORD=gaurav123
```

Optionally restrict the API CORS origins (defaults to `http://localhost:8501`):

```env
CORS_ORIGINS=http://localhost:8501,http://localhost:8502
```

3. Import C13 schema/data dump into PostgreSQL.

```bash
PGPASSWORD='gaurav123' /opt/homebrew/opt/postgresql@16/bin/psql -h localhost -U gaurav -d projectdb -f src/modules/C13/projectdb.sql
```

Note: Import into a fresh database for a clean setup. Re-importing over an existing DB can create duplicate-object errors.

## Run

Full app:

```bash
streamlit run app.py --server.port 8501
```

FastAPI backend (required for the C13 Natural Language Patient Search module):

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

C13 standalone:

```bash
streamlit run src/modules/C13/run_c13.py --server.port 8502
```

See module-specific details in src/modules/C13/README.md.
