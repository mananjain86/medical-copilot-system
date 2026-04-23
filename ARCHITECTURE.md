# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         End Users                                │
│                    (Doctors, Patients, Admins)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
        │                                         │
        ▼                                         ▼
┌──────────────────┐                    ┌──────────────────┐
│  Streamlit Cloud │                    │      Render      │
│   (Frontend)     │                    │   (Backend API)  │
│                  │                    │                  │
│  Port: 8501      │◄──────────────────►│  Port: 8000      │
│                  │    Optional API    │                  │
│  Components:     │      Calls         │  Components:     │
│  • app.py        │                    │  • api/main.py   │
│  • auth/         │                    │  • FastAPI       │
│  • dashboards/   │                    │  • Uvicorn       │
│  • components/   │                    │  • Endpoints:    │
│  • views/        │                    │    - /search     │
│                  │                    │    - /history    │
│                  │                    │    - /cohorts    │
└────────┬─────────┘                    └────────┬─────────┘
         │                                       │
         │                                       │
         │         ┌─────────────────────────────┘
         │         │
         │         │ PostgreSQL Protocol
         │         │ (SSL/TLS)
         │         │
         └─────────┼─────────────────┐
                   │                 │
                   ▼                 ▼
         ┌──────────────────────────────────┐
         │         Supabase                 │
         │    (PostgreSQL Database)         │
         │                                  │
         │  Connection Pooler               │
         │  Port: 5432                      │
         │                                  │
         │  Tables:                         │
         │  • patients                      │
         │  • visits                        │
         │  • symptoms                      │
         │  • doctors                       │
         │  • users                         │
         │  • search_queries                │
         │  • search_results                │
         │  • patient_cohorts               │
         │  • saved_queries                 │
         │                                  │
         └──────────────────────────────────┘
```

---

## Deployment Architecture

### Option 1: Direct Database Access (Current)

```
┌──────────────┐         ┌──────────────┐
│  Streamlit   │────────►│   Supabase   │
│   Frontend   │         │   Database   │
└──────────────┘         └──────────────┘
                                ▲
                                │
┌──────────────┐                │
│    Render    │────────────────┘
│   Backend    │
└──────────────┘
```

**Pros**: Simple, fast, fewer moving parts
**Cons**: Database credentials in multiple places

### Option 2: API-Based (Recommended for Production)

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  Streamlit   │────────►│    Render    │────────►│   Supabase   │
│   Frontend   │   API   │   Backend    │   SQL   │   Database   │
└──────────────┘         └──────────────┘         └──────────────┘
```

**Pros**: Better security, centralized logic, easier to scale
**Cons**: Additional latency, more complex setup

---

## Data Flow

### Patient Search Flow

```
1. User enters query
   │
   ▼
2. Frontend (Streamlit)
   │
   ├─→ Option A: Direct DB query
   │   └─→ backend.py → nl_search_pipeline()
   │
   └─→ Option B: API call
       └─→ POST /api/v1/search
           └─→ backend.py → nl_search_pipeline()
   │
   ▼
3. Query Processing
   │
   ├─→ parse_query() - Extract filters
   ├─→ expand_terms() - Synonym expansion
   ├─→ generate_sql() - Build dynamic SQL
   └─→ run_search() - Execute query
   │
   ▼
4. Database (Supabase)
   │
   ├─→ Query patients table
   ├─→ Join with visits, symptoms
   ├─→ Apply filters
   └─→ Return results
   │
   ▼
5. Results Processing
   │
   ├─→ Log search query
   ├─→ Create cohort
   └─→ Return to frontend
   │
   ▼
6. Display Results
   └─→ Show patient cards
```

---

## Component Breakdown

### Frontend (Streamlit)

```
app.py (Main Entry)
│
├─→ auth/
│   ├─→ login.py
│   └─→ signup.py
│
├─→ dashboards/
│   ├─→ patient_dashboard.py
│   ├─→ doctor_dashboard.py
│   └─→ admin_dashboard.py
│
├─→ components/
│   ├─→ cards.py
│   ├─→ charts.py
│   ├─→ sidebar.py
│   └─→ tabs.py
│
└─→ views/
    ├─→ category_modules.py
    ├─→ cohort_patients.py
    ├─→ module_detail.py
    └─→ patient_modules.py
```

### Backend (FastAPI)

```
api/main.py (API Entry)
│
├─→ Endpoints:
│   ├─→ POST /api/v1/search
│   ├─→ GET  /api/v1/history/{user_id}
│   ├─→ GET  /api/v1/saved-queries/{user_id}
│   ├─→ POST /api/v1/saved-queries
│   ├─→ GET  /api/v1/cohorts
│   ├─→ GET  /api/v1/cohorts/{id}/members
│   ├─→ GET  /api/v1/patients/{id}/details
│   └─→ GET  /health
│
└─→ src/modules/C13/backend.py
    ├─→ parse_query()
    ├─→ expand_terms()
    ├─→ generate_sql()
    ├─→ run_search()
    ├─→ nl_search_pipeline()
    └─→ Database helpers
```

### Database (Supabase)

```
PostgreSQL Schema
│
├─→ Core Tables:
│   ├─→ patients
│   ├─→ visits
│   ├─→ symptoms
│   ├─→ doctors
│   └─→ users
│
├─→ Search Tables:
│   ├─→ search_queries
│   ├─→ search_results
│   ├─→ saved_queries
│   └─→ query_templates
│
├─→ Cohort Tables:
│   ├─→ patient_cohorts
│   └─→ patient_cohort_members
│
└─→ Reference Tables:
    ├─→ synonyms
    ├─→ symptom_hierarchy
    ├─→ lab_tests
    └─→ lab_results
```

---

## Technology Stack

### Frontend
- **Framework**: Streamlit 1.x
- **UI Components**: streamlit-option-menu
- **Charts**: Matplotlib
- **HTTP Client**: Requests (optional)

### Backend
- **Framework**: FastAPI
- **Server**: Uvicorn
- **Validation**: Pydantic
- **Database Driver**: psycopg2-binary

### Database
- **DBMS**: PostgreSQL 15+
- **Hosting**: Supabase
- **Connection**: Connection Pooler
- **SSL**: Required

### Deployment
- **Frontend Host**: Streamlit Cloud
- **Backend Host**: Render
- **Database Host**: Supabase
- **CI/CD**: GitHub Actions

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Security Layers                       │
└─────────────────────────────────────────────────────────┘

1. Transport Layer
   ├─→ HTTPS/TLS for all connections
   ├─→ SSL for database connections
   └─→ Certificate validation

2. Authentication Layer
   ├─→ User login (auth/login.py)
   ├─→ Session management
   └─→ Role-based access (Patient/Doctor/Admin)

3. Application Layer
   ├─→ Input validation (Pydantic)
   ├─→ SQL injection prevention (parameterized queries)
   ├─→ CORS configuration
   └─→ Environment variable secrets

4. Database Layer
   ├─→ Connection pooling
   ├─→ SSL mode required
   ├─→ Prepared statements
   └─→ Row-level security (Supabase)

5. Infrastructure Layer
   ├─→ Secrets management (env vars)
   ├─→ .gitignore for sensitive files
   ├─→ GitHub Actions security checks
   └─→ Platform security (Render/Streamlit/Supabase)
```

---

## Scalability Considerations

### Current Limits (Free Tier)

| Component | Limit | Impact |
|-----------|-------|--------|
| Streamlit Cloud | 1 app | Single deployment |
| Render | 750 hrs/month | Sleeps after 15min idle |
| Supabase | 500MB DB | ~50K patient records |
| Supabase | 2GB bandwidth | ~20K API calls/month |

### Scaling Path

```
Phase 1: Free Tier (Current)
├─→ Good for: Demos, testing, small teams
└─→ Users: <100 concurrent

Phase 2: Paid Tier ($50/month)
├─→ Streamlit: $20/month (private, more apps)
├─→ Render: $7/month (always-on)
├─→ Supabase: $25/month (8GB, 100GB bandwidth)
└─→ Users: <1000 concurrent

Phase 3: Production ($200+/month)
├─→ Streamlit: Custom plan
├─→ Render: Multiple instances + load balancer
├─→ Supabase: Pro plan with read replicas
└─→ Users: 10K+ concurrent
```

---

## Monitoring & Observability

```
┌──────────────────────────────────────────────────────┐
│                  Monitoring Stack                     │
└──────────────────────────────────────────────────────┘

Frontend (Streamlit Cloud)
├─→ App analytics
├─→ Error logs
├─→ Usage metrics
└─→ Performance data

Backend (Render)
├─→ Application logs
├─→ Request metrics
├─→ CPU/Memory usage
└─→ Deployment history

Database (Supabase)
├─→ Query performance
├─→ Connection pool stats
├─→ Storage usage
└─→ API analytics

External (Optional)
├─→ Uptime monitoring (UptimeRobot)
├─→ Error tracking (Sentry)
└─→ Analytics (Google Analytics)
```

---

## Development Workflow

```
Local Development
│
├─→ 1. Code changes
│   └─→ Edit files locally
│
├─→ 2. Test locally
│   ├─→ ./test_local.sh
│   └─→ python verify_deployment.py
│
├─→ 3. Commit & Push
│   ├─→ git add .
│   ├─→ git commit -m "..."
│   └─→ git push origin main
│
├─→ 4. GitHub Actions
│   ├─→ Run checks
│   └─→ Verify deployment readiness
│
├─→ 5. Auto-Deploy
│   ├─→ Render: Auto-deploy on push
│   └─→ Streamlit: Auto-deploy on push
│
└─→ 6. Monitor
    ├─→ Check logs
    └─→ Verify functionality
```

---

## File Structure

```
medical-copilot-system/
│
├─→ Frontend Files
│   ├─→ app.py (main entry)
│   ├─→ streamlit_app.py (cloud entry)
│   ├─→ auth/ (authentication)
│   ├─→ dashboards/ (role-based views)
│   ├─→ components/ (UI components)
│   └─→ views/ (feature views)
│
├─→ Backend Files
│   ├─→ api/main.py (FastAPI app)
│   └─→ src/modules/C13/backend.py (business logic)
│
├─→ Deployment Files
│   ├─→ Procfile (Render config)
│   ├─→ runtime.txt (Python version)
│   ├─→ render.yaml (service config)
│   ├─→ .streamlit/config.toml (Streamlit config)
│   └─→ requirements.txt (dependencies)
│
├─→ Documentation
│   ├─→ README.md (overview)
│   ├─→ DEPLOYMENT.md (full guide)
│   ├─→ QUICK_START.md (15-min guide)
│   ├─→ DEPLOYMENT_CHECKLIST.md (step-by-step)
│   ├─→ DEPLOYMENT_SUMMARY.md (summary)
│   └─→ ARCHITECTURE.md (this file)
│
├─→ Utilities
│   ├─→ verify_deployment.py (pre-deploy check)
│   ├─→ test_local.sh (local testing)
│   └─→ .github/workflows/deploy.yml (CI/CD)
│
└─→ Configuration
    ├─→ .env (secrets - not in git)
    ├─→ .env.example (template)
    └─→ .gitignore (excluded files)
```

---

## API Endpoints Reference

### Search Endpoints

```
POST /api/v1/search
├─→ Body: {"user_id": int, "query": string}
└─→ Returns: {parsed, sql, results, query_id, cohort_id}

GET /api/v1/history/{user_id}
└─→ Returns: [list of past queries]

GET /api/v1/saved-queries/{user_id}
└─→ Returns: [list of saved queries]

POST /api/v1/saved-queries
├─→ Body: {"user_id": int, "query_text": string}
└─→ Returns: {status, message}
```

### Cohort Endpoints

```
GET /api/v1/cohorts
└─→ Returns: [list of cohorts with member counts]

GET /api/v1/cohorts/{cohort_id}/members
├─→ Query: ?limit=200
└─→ Returns: [list of patients in cohort]
```

### Patient Endpoints

```
GET /api/v1/patients/{patient_id}/details
└─→ Returns: {id, name, gender, age, visits, symptoms, diagnoses}
```

### Health Check

```
GET /health
└─→ Returns: {"status": "ok"}
```

---

## Environment Variables

### Required for Both Services

```bash
DATABASE_URL="postgresql://..."
DATABASE_PUBLIC_URL="postgresql://..."
DB_HOST="host.supabase.com"
DB_PORT="5432"
DB_NAME="postgres"
DB_USER="postgres.project"
DB_PASSWORD="password"
DB_SSLMODE="require"
```

### Optional

```bash
# For API-based architecture
BACKEND_API_URL="https://your-app.onrender.com"

# Connection pooling
DB_POOL_MIN="1"
DB_POOL_MAX="10"
```

---

## Performance Optimization

### Database Queries
- ✅ Indexed columns: patient_id, visit_id, symptom_id
- ✅ Connection pooling enabled
- ✅ Prepared statements used
- ✅ Query result caching (Streamlit)

### Frontend
- ✅ Streamlit caching (@st.cache_data)
- ✅ Lazy loading of components
- ✅ Efficient state management
- ✅ Minimal re-renders

### Backend
- ✅ Async endpoints (FastAPI)
- ✅ Connection pooling
- ✅ Response compression
- ✅ CORS optimization

---

**Last Updated**: April 24, 2026
**Version**: 1.0.0
