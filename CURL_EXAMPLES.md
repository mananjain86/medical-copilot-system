# API Testing with cURL

## Quick Test Commands

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{"status": "ok"}
```

---

### 2. Patient Search

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "query": "female patients over 60"}'
```

**Expected Response:**
```json
{
  "parsed": {...},
  "sql": {...},
  "results": [
    {
      "patient_id": 123,
      "first_name": "Jane",
      "last_name": "Doe",
      "gender": "female",
      "age": 65,
      "status": "Active"
    }
  ],
  "query_id": 1,
  "cohort_id": 1
}
```

---

### 3. Search History

```bash
curl http://localhost:8000/api/v1/history/1
```

**Expected Response:**
```json
[
  {
    "query_id": 1,
    "query_text": "female patients over 60",
    "search_type": "demographic",
    "created_at": "2024-01-01T12:00:00"
  }
]
```

---

### 4. List Cohorts

```bash
curl http://localhost:8000/api/v1/cohorts
```

**Expected Response:**
```json
[
  {
    "cohort_id": 1,
    "cohort_name": "female patients over 60",
    "created_at": "2024-01-01T12:00:00",
    "member_count": 15
  }
]
```

---

### 5. Cohort Members

```bash
curl http://localhost:8000/api/v1/cohorts/1/members
```

**Expected Response:**
```json
[
  {
    "cohort_id": 1,
    "patient_id": 123,
    "first_name": "Jane",
    "last_name": "Doe",
    "gender": "female",
    "age": 65,
    "city": "Mumbai",
    "query_id": 1,
    "added_at": "2024-01-01T12:00:00"
  }
]
```

---

### 6. Patient Details

```bash
curl http://localhost:8000/api/v1/patients/123/details
```

**Expected Response:**
```json
{
  "id": 123,
  "name": "Jane Doe",
  "gender": "female",
  "age": 65,
  "city": "Mumbai",
  "visits": [...],
  "visit_count": 5,
  "doctor_visits": [...],
  "diagnoses": ["Diabetes", "Hypertension"],
  "symptoms": ["Fever", "Cough"]
}
```

---

## Testing Against Deployed API

Replace `http://localhost:8000` with your deployed URL:

```bash
# Render
curl https://your-app.onrender.com/health

# Search on deployed API
curl -X POST https://your-app.onrender.com/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "query": "diabetic patients"}'
```

---

## Using the Test Scripts

### Bash Script

```bash
# Test locally
./test_api_curl.sh

# Test deployed
./test_api_curl.sh https://your-app.onrender.com
```

### Python Script

```bash
# Test locally
python test_api.py

# Test deployed
python test_api.py https://your-app.onrender.com
```

---

## Common Issues

### Connection Refused

**Error:**
```
curl: (7) Failed to connect to localhost port 8000: Connection refused
```

**Solution:**
- Make sure API is running: `uvicorn api.main:app --host 0.0.0.0 --port 8000`

### 500 Internal Server Error

**Error:**
```json
{"detail": "Database connection failed"}
```

**Solution:**
- Check database credentials in `.env`
- Verify Supabase is running
- Test connection: `python -c "from src.modules.C13.backend import get_connection; conn = get_connection(); print('OK')"`

### Timeout

**Error:**
```
curl: (28) Operation timed out
```

**Solution:**
- Increase timeout: `curl --max-time 60 ...`
- Check if database query is slow
- Verify network connectivity

---

## Pretty Print JSON

Use `jq` for formatted output:

```bash
curl http://localhost:8000/health | jq

curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "query": "female patients"}' | jq
```

Install jq:
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq
```

---

## Save Response to File

```bash
curl http://localhost:8000/api/v1/cohorts > cohorts.json

curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "query": "diabetic patients"}' \
  -o search_results.json
```

---

## Verbose Output

See full request/response details:

```bash
curl -v http://localhost:8000/health

curl -v -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "query": "female patients"}'
```
