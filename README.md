Live Demo: 👉 [https://frontend-zxra8c5w4ip3f6k5gvjasp.streamlit.app/](https://frontend-zxra8c5w4ip3f6k5gvjasp.streamlit.app/)

## Deployment

Deploy with frontend on Streamlit Cloud and backend on Render (optional).

📖 **See [DEPLOYMENT.md](DEPLOYMENT.md) for complete instructions**

### Quick Steps

1. **Convert secrets**: `python convert_env_to_toml.py`
2. **Push to GitHub**: `git push origin main`
3. **Deploy to Streamlit Cloud**: Use TOML output from step 1
4. **Deploy to Render** (optional): For backend API

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

C13 standalone:

```bash
streamlit run src/modules/C13/run_c13.py --server.port 8502
```

See module-specific details in src/modules/C13/README.md.
