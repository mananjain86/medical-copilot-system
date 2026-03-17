"""
Module C13 – MediSearch Patient Search Page  (matches target design)
"""

import re
import streamlit as st
import numpy as np
from src.modules.C13.backend import get_connection, nl_search_pipeline, get_search_history


# ── suggestion chips ──────────────────────────────────────────────────────────
SUGGESTIONS = [
    "female patients over 60",
    "diabetic patients",
    "patients with hypertension",
    "elderly patients with heart disease",
    "patients in cardiology department",
    "female patients with diabetes over 60",
]

# ── mock patient data ─────────────────────────────────────────────────────────
MOCK_PATIENTS = [
    {"id": "P001", "name": "Mary Johnson",      "age": 65, "gender": "Female", "symptoms": ["Diabetes", "Hypertension"],    "diagnoses": ["Type 2 Diabetes", "Stage 1 Hypertension"],      "department": "Endocrinology", "admission_date": "2024-01-15", "physician": "Dr. Sarah Chen",     "status": "Active"},
    {"id": "P002", "name": "Linda Martinez",    "age": 68, "gender": "Female", "symptoms": ["Diabetes"],                   "diagnoses": ["Type 2 Diabetes"],                              "department": "Endocrinology", "admission_date": "2024-02-10", "physician": "Dr. Sarah Chen",     "status": "Active"},
    {"id": "P003", "name": "Patricia Lee",      "age": 62, "gender": "Female", "symptoms": ["Diabetic Neuropathy"],        "diagnoses": ["Diabetic Peripheral Neuropathy"],               "department": "Neurology",     "admission_date": "2024-01-28", "physician": "Dr. James Park",     "status": "Discharged"},
    {"id": "P004", "name": "Robert Williams",   "age": 72, "gender": "Male",   "symptoms": ["Hypertension", "Chest Pain"], "diagnoses": ["Essential Hypertension", "Angina"],             "department": "Cardiology",    "admission_date": "2024-03-01", "physician": "Dr. Michael Torres", "status": "Active"},
    {"id": "P005", "name": "James Brown",       "age": 58, "gender": "Male",   "symptoms": ["Asthma", "Allergies"],        "diagnoses": ["Bronchial Asthma", "Allergic Rhinitis"],        "department": "Pulmonology",   "admission_date": "2024-02-20", "physician": "Dr. Emily Watson",   "status": "Active"},
    {"id": "P006", "name": "Dorothy Wilson",    "age": 70, "gender": "Female", "symptoms": ["Arthritis", "Hypertension"],  "diagnoses": ["Rheumatoid Arthritis", "Hypertension"],        "department": "Rheumatology",  "admission_date": "2024-01-05", "physician": "Dr. Linda Patel",    "status": "Active"},
    {"id": "P007", "name": "Charles Anderson",  "age": 55, "gender": "Male",   "symptoms": ["Back Pain", "Sciatica"],      "diagnoses": ["Lumbar Disc Herniation"],                      "department": "Orthopedics",   "admission_date": "2024-03-10", "physician": "Dr. Kevin Nguyen",   "status": "Active"},
    {"id": "P008", "name": "Barbara Taylor",    "age": 67, "gender": "Female", "symptoms": ["Osteoporosis"],               "diagnoses": ["Osteoporosis"],                                "department": "Orthopedics",   "admission_date": "2024-02-15", "physician": "Dr. Kevin Nguyen",   "status": "Discharged"},
    {"id": "P009", "name": "Thomas Moore",      "age": 63, "gender": "Male",   "symptoms": ["Diabetes", "Kidney Disease"], "diagnoses": ["Type 2 Diabetes", "CKD"],                     "department": "Nephrology",    "admission_date": "2024-01-20", "physician": "Dr. Rachel Kim",     "status": "Active"},
    {"id": "P010", "name": "Nancy Jackson",     "age": 71, "gender": "Female", "symptoms": ["Alzheimers"],                 "diagnoses": ["Alzheimer's Disease"],                         "department": "Neurology",     "admission_date": "2024-02-28", "physician": "Dr. James Park",     "status": "Active"},
    {"id": "P011", "name": "Richard Harris",    "age": 48, "gender": "Male",   "symptoms": ["Depression", "Anxiety"],      "diagnoses": ["Major Depressive Disorder"],                   "department": "Psychiatry",    "admission_date": "2024-03-05", "physician": "Dr. Olivia Stone",   "status": "Active"},
    {"id": "P012", "name": "Susan White",       "age": 54, "gender": "Female", "symptoms": ["Breast Cancer"],              "diagnoses": ["Breast Cancer Stage 2"],                       "department": "Oncology",      "admission_date": "2024-01-12", "physician": "Dr. Mark Sullivan",  "status": "Active"},
    {"id": "P013", "name": "David Thompson",    "age": 66, "gender": "Male",   "symptoms": ["Prostate Issues"],            "diagnoses": ["Benign Prostate Hyperplasia"],                 "department": "Urology",       "admission_date": "2024-02-08", "physician": "Dr. Paul Zhang",     "status": "Discharged"},
    {"id": "P014", "name": "Margaret Garcia",   "age": 60, "gender": "Female", "symptoms": ["Thyroid", "Fatigue"],         "diagnoses": ["Hypothyroidism"],                              "department": "Endocrinology", "admission_date": "2024-03-12", "physician": "Dr. Sarah Chen",     "status": "Active"},
    {"id": "P015", "name": "Joseph Rodriguez",  "age": 76, "gender": "Male",   "symptoms": ["COPD"],                       "diagnoses": ["COPD"],                                        "department": "Pulmonology",   "admission_date": "2024-01-30", "physician": "Dr. Emily Watson",   "status": "Active"},
    {"id": "P016", "name": "Elizabeth Lewis",   "age": 59, "gender": "Female", "symptoms": ["Migraine"],                   "diagnoses": ["Chronic Migraine"],                            "department": "Neurology",     "admission_date": "2024-02-22", "physician": "Dr. James Park",     "status": "Discharged"},
    {"id": "P017", "name": "Christopher Hill",  "age": 44, "gender": "Male",   "symptoms": ["Hypertension"],               "diagnoses": ["Essential Hypertension"],                      "department": "Cardiology",    "admission_date": "2024-03-08", "physician": "Dr. Michael Torres", "status": "Active"},
    {"id": "P018", "name": "Betty Scott",       "age": 73, "gender": "Female", "symptoms": ["Heart Failure", "Edema"],     "diagnoses": ["Congestive Heart Failure"],                    "department": "Cardiology",    "admission_date": "2024-01-18", "physician": "Dr. Michael Torres", "status": "Active"},
    {"id": "P019", "name": "William Adams",     "age": 50, "gender": "Male",   "symptoms": ["Diabetes", "Obesity"],        "diagnoses": ["Type 2 Diabetes", "Morbid Obesity"],           "department": "Endocrinology", "admission_date": "2024-02-05", "physician": "Dr. Sarah Chen",     "status": "Active"},
    {"id": "P020", "name": "Helen Nelson",      "age": 64, "gender": "Female", "symptoms": ["Lupus", "Joint Pain"],        "diagnoses": ["Systemic Lupus Erythematosus"],               "department": "Rheumatology",  "admission_date": "2024-03-15", "physician": "Dr. Linda Patel",    "status": "Active"},
]

# ── mock history entries ───────────────────────────────────────────────────────
MOCK_HISTORY = [
    {"query_text": "female patients over 60 with diabetes",   "search_type": "Demographic · Clinical Combo", "created_at": "3h ago",  "results": 3},
    {"query_text": "patients with hypertension in cardiology", "search_type": "Symptom-Based Search",        "created_at": "4h ago",  "results": 5},
    {"query_text": "elderly patients with heart disease",      "search_type": "Age Range Search",             "created_at": "5h ago",  "results": 4},
    {"query_text": "diabetic patients",                        "search_type": "Symptom-Based Search",        "created_at": "1d ago",  "results": 6},
    {"query_text": "male patients with asthma",                "search_type": "Demographic · Clinical Combo", "created_at": "4d ago",  "results": 2},
    {"query_text": "patients in neurology over 60",            "search_type": "Department Search",           "created_at": "6d ago",  "results": 3},
]


# ── shared CSS ────────────────────────────────────────────────────────────────
def _inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
        #MainMenu, footer,
        [data-testid="stHeader"], [data-testid="stToolbar"],
        [data-testid="stDecoration"] { display: none !important; visibility: hidden !important; }

        /* ── background + sidebar ── */
        [data-testid="stAppViewContainer"] { background: #080f1a !important; }
        [data-testid="stSidebar"] > div:first-child {
            background: #0d1520 !important;
            border-right: 1px solid #132030 !important;
        }
        [data-testid="stSidebar"] { min-width: 210px !important; max-width: 215px !important; }
        .block-container { padding: 2.2rem 2.4rem !important; max-width: 100% !important; }

        /* scrollbar */
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: #1f3050; border-radius: 99px; }

        /* ── logo ── */
        .ms-logo {
            display: flex; align-items: center; gap: 10px;
            padding: 18px 14px 12px;
        }
        .ms-logo-icon {
            width: 34px; height: 34px;
            background: linear-gradient(135deg, #00b4d8, #0070f3);
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 18px;
        }
        .ms-logo-name { color: #f0f6ff; font-weight: 800; font-size: 15px; line-height: 1; }
        .ms-logo-sub  { color: #3d6880; font-size: 10px; margin-top: 2px; font-weight: 500; }

        /* ── nav button reset ── */
        div[data-testid="stSidebar"] div[data-testid="stButton"] button {
            width: 100% !important;
            background: transparent !important;
            color: #4b7594 !important;
            border: none !important;
            border-radius: 8px !important;
            text-align: left !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            padding: 9px 12px !important;
            justify-content: flex-start !important;
            transition: all .15s !important;
            box-shadow: none !important;
        }
        div[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
            background: rgba(0,180,216,.08) !important;
            color: #8cccdf !important;
        }
        /* active nav item */
        div[data-testid="stSidebar"] div[data-testid="stButton"][key$="_active"] button,
        .nav-active button {
            background: rgba(0,180,216,.12) !important;
            color: #00b4d8 !important;
        }

        /* ── user card ── */
        .ms-user-card {
            margin: 8px 10px; padding: 10px 12px;
            background: #111f30; border: 1px solid #1a2e44;
            border-radius: 10px;
            display: flex; align-items: center; gap: 10px;
        }
        .ms-ava {
            width: 32px; height: 32px; border-radius: 50%;
            background: linear-gradient(135deg, #00b4d8, #0070f3);
            display: flex; align-items: center; justify-content: center;
            font-size: 12px; font-weight: 800; color: #fff; flex-shrink: 0;
        }
        .ms-ava-admin { background: linear-gradient(135deg, #9b59b6, #6c3483) !important; }
        .ms-ava-name  { color: #cde; font-size: 12px; font-weight: 600; line-height: 1.1; }
        .ms-ava-role  { color: #00b4d8; font-size: 10px; font-weight: 500; }
        .ms-ava-role-admin { color: #9b59b6 !important; }

        /* ── main headings ── */
        .ms-title { font-size: 22px; font-weight: 800; color: #e8f4fd; letter-spacing: -.3px; }
        .ms-sub   { color: #3d5869; font-size: 13px; margin-top: 2px; margin-bottom: 20px; }

        /* ── search bar ── */
        [data-testid="stTextInput"] input {
            background: #111f30 !important;
            border: 1px solid #1f3248 !important;
            border-radius: 10px !important;
            color: #cde !important;
            font-size: 13px !important;
            font-family: 'Inter', sans-serif !important;
            padding: 11px 14px !important;
        }
        [data-testid="stTextInput"] input:focus {
            border-color: #00b4d8 !important;
            box-shadow: 0 0 0 2px rgba(0,180,216,.12) !important;
        }
        [data-testid="stTextInput"] input::placeholder { color: #2a3f52 !important; }
        [data-testid="stTextInput"] > label { display: none !important; }

        /* ── search button (main area only) ── */
        div[data-testid="stMain"] > div > div > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
            background: linear-gradient(135deg, #00b4d8, #0070f3) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 700 !important; font-size: 13px !important;
            padding: 11px 18px !important;
            box-shadow: 0 2px 12px rgba(0,176,216,.3) !important;
            transition: opacity .18s !important;
        }
        div[data-testid="stMain"] > div > div > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button:hover {
            opacity: .85 !important;
        }

        /* ── chip label ── */
        .chip-row-label { color: #2a3f52; font-size: 10px; font-weight: 700;
                          text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }

        /* ── chips ── */
        div[data-testid="stColumn"] div[data-testid="stButton"] button {
            background: transparent !important;
            color: #4b7594 !important;
            border: 1px solid #1f3248 !important;
            border-radius: 99px !important;
            font-size: 11px !important;
            font-weight: 400 !important;
            padding: 4px 10px !important;
            transition: all .15s !important;
            box-shadow: none !important;
        }
        div[data-testid="stColumn"] div[data-testid="stButton"] button:hover {
            border-color: #00b4d8 !important;
            color: #00b4d8 !important;
            background: rgba(0,180,216,.05) !important;
        }

        /* ── metric strip ── */
        .metric-strip {
            display: grid; grid-template-columns: repeat(3,1fr);
            gap: 12px; margin: 20px 0 16px;
        }
        .metric-box {
            background: #111f30; border: 1px solid #1a2e44;
            border-radius: 10px; padding: 16px 18px;
        }
        .metric-val { font-size: 28px; font-weight: 800; color: #e8f4fd; line-height: 1; }
        .metric-lbl { font-size: 10px; color: #2e4a60; font-weight: 600;
                      text-transform: uppercase; letter-spacing: .8px; margin-top: 4px; }

        /* ── result row ── */
        .pt-row {
            display: flex; align-items: center;
            background: #111f30; border: 1px solid #1a2e44;
            border-radius: 10px; padding: 14px 16px; margin-bottom: 6px;
            transition: background .15s;
        }
        .pt-row:hover { background: #132030; }
        .pt-avatar {
            width: 36px; height: 36px; border-radius: 50%;
            background: #0e2035;
            display: flex; align-items: center; justify-content: center;
            font-size: 14px; flex-shrink: 0; margin-right: 12px;
        }
        .pt-body     { flex: 1; min-width: 0; }
        .pt-name     { font-weight: 700; color: #d4eaf8; font-size: 14px; }
        .pt-meta     { color: #2e4a60; font-size: 11px; margin-top: 2px; }
        .pt-meta span { color: #3a6278; }
        .pt-right    { text-align: right; flex-shrink: 0; margin-left: 16px; }
        .pt-count    { font-size: 20px; font-weight: 800; color: #e8f4fd; line-height: 1; }
        .pt-clabel   { font-size: 10px; color: #2e4a60; font-weight: 600;
                       text-transform: uppercase; letter-spacing: .7px; margin-top: 2px; }

        /* badge */
        .badge { display:inline-block; padding:2px 8px; border-radius:99px;
                 font-size:10px; font-weight:600; margin-right:4px; }
        .badge-f { background:rgba(255,150,200,.12); color:#f9a8d4; }
        .badge-m { background:rgba(100,200,230,.10); color:#7dd3fc; }
        .badge-a { background:rgba(0,230,118,.10); color:#4ade80; }
        .badge-d { background:rgba(250,170,60,.10); color:#fbbf24; }

        /* ── empty state ── */
        .empty { display:flex; flex-direction:column; align-items:center;
                 justify-content:center; padding:70px 0; text-align:center; }
        .empty-ico { font-size:52px; opacity:.3; margin-bottom:16px; }
        .empty-ttl { color:#cde; font-size:18px; font-weight:700; margin-bottom:6px; }
        .empty-sub { color:#2e4a60; font-size:13px; line-height:1.6; }
        .empty-sub em { color:#00b4d8; font-style:normal; }

        /* ── history rows ── */
        .hist-row {
            display: flex; align-items: center;
            background: #111f30; border: 1px solid #1a2e44;
            border-radius: 10px; padding: 14px 16px; margin-bottom: 6px;
            gap: 12px;
        }
        .hist-row:hover { background: #132030; }
        .hist-ico {
            width: 32px; height: 32px; border-radius: 50%;
            background: #0e2035; border: 1px solid #1a2e44;
            display:flex; align-items:center; justify-content:center;
            font-size:13px; flex-shrink:0;
        }
        .hist-body { flex:1; min-width:0; }
        .hist-q    { color: #d4eaf8; font-size: 13px; font-weight: 600; }
        .hist-q b  { color: #00b4d8; font-weight: 700; }
        .hist-meta { color: #2e4a60; font-size: 11px; margin-top: 3px; }
        .hist-meta span { color: #1f6688; }
        .hist-right { text-align:right; flex-shrink:0; }
        .hist-num   { font-size:20px; font-weight:800; color:#e8f4fd; }
        .hist-nlbl  { font-size:10px; color:#2e4a60; font-weight:600;
                      text-transform:uppercase; letter-spacing:.6px; }

        /* filter input */
        .filter-wrap { margin-bottom: 16px; }

        /* ── history stat strip ── */
        .hist-stats {
            display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:20px;
        }

        /* dataframe */
        [data-testid="stDataFrame"] { border-radius: 10px !important; overflow: hidden !important; }
        hr { border-color: #1a2e44 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _search_mock_patients(query: str):
    from src.modules.C13.backend import SearchResult
    if not query.strip():
        return []
    q = query.lower()
    gender_filter = "Female" if "female" in q else ("Male" if "male" in q else None)
    age_match  = re.search(r"over\s+(\d+)|above\s+(\d+)|>\s*(\d+)", q)
    min_age = int(next(g for g in age_match.groups() if g)) if age_match else None
    keywords = re.sub(
        r"\bpatients?\b|\bwith\b|\band\b|\bthe\b|\bover\b|\bfemale\b|\bmale\b"
        r"|\belderly\b|\byears?\b|\bold\b",
        " ", q
    ).split()
    keywords = [k for k in keywords if len(k) > 2]
    results = []
    for p in MOCK_PATIENTS:
        if gender_filter and p["gender"] != gender_filter:
            continue
        if min_age and p["age"] <= min_age:
            continue
        if keywords:
            hay = " ".join(p["symptoms"] + p["diagnoses"] + [p["department"], p["name"]]).lower()
            if not any(kw in hay for kw in keywords):
                continue
        results.append(SearchResult(
            patient_id=p["id"],
            first_name=p["name"].split()[0],
            last_name=" ".join(p["name"].split()[1:]),
            gender=p["gender"],
        ))
    return results


def _sidebar(role: str = "Clinician") -> str:
    with st.sidebar:
        is_admin = role == "Administrator"

        st.markdown(
            """
            <div class="ms-logo">
                <div class="ms-logo-icon">🫀</div>
                <div>
                    <div class="ms-logo-name">MediSearch</div>
                    <div class="ms-logo-sub">Patient Finder</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.session_state.setdefault("ms_current_page", "Patient Search")
        page = st.session_state.ms_current_page

        def _nav(label: str, icon: str, key: str):
            active = page == label
            with st.container():
                if active:
                    st.markdown('<div class="nav-active">', unsafe_allow_html=True)
                clicked = st.button(f"{icon}  {label}", use_container_width=True, key=key)
                if active:
                    st.markdown("</div>", unsafe_allow_html=True)
                if clicked:
                    st.session_state.ms_current_page = label
                    st.rerun()

        _nav("Patient Search", "🔍", "nav_ps")
        _nav("Search History", "🕐", "nav_sh")
        _nav("Admin Panel",    "⚙️",  "nav_ap")

        # spacer then user card
        st.markdown("<br>" * 4, unsafe_allow_html=True)
        ava_cls  = "ms-ava ms-ava-admin" if is_admin else "ms-ava"
        role_cls = "ms-ava-role ms-ava-role-admin" if is_admin else "ms-ava-role"
        initials = "SA" if is_admin else "JD"
        name     = "System Admin" if is_admin else "Dr. Jane Doe"
        st.markdown(
            f"""
            <div class="ms-user-card">
                <div class="{ava_cls}">{initials}</div>
                <div>
                    <div class="ms-ava-name">{name}</div>
                    <div class="{role_cls}">● {role}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return st.session_state.ms_current_page


# ── Search section ────────────────────────────────────────────────────────────

def _search_section() -> None:
    st.markdown(
        '<div class="ms-title">Patient Search</div>'
        '<div class="ms-sub">Use natural language to find patient cohorts</div>',
        unsafe_allow_html=True,
    )

    col_in, col_btn = st.columns([6, 1], gap="small")
    with col_in:
        query = st.text_input(
            "q", placeholder='e.g. "female patients over 60 with diabetes"',
            label_visibility="collapsed", key="ms_query",
        )
    with col_btn:
        searched = st.button("🔍 Search", use_container_width=True, key="ms_search_btn")

    run = searched or st.session_state.pop("_ms_run", False)

    if run and (query or "").strip():
        use_mock = False
        try:
            conn = get_connection()
            result = nl_search_pipeline(conn, st.session_state.get("ms_user_id", 1), query)

            # Fetch extra patient details (age, dept, status) from DB
            raw_results = result.get("results", [])
            enriched = []
            if raw_results:
                ids = [getattr(p, "patient_id", None) for p in raw_results]
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            SELECT
                                p.patient_id,
                                DATE_PART('year', AGE(p.date_of_birth))::int AS age,
                                v.department,
                                v.discharge_date
                            FROM patients p
                            LEFT JOIN LATERAL (
                                SELECT department, discharge_date
                                FROM visits
                                WHERE patient_id = p.patient_id
                                ORDER BY visit_date DESC
                                LIMIT 1
                            ) v ON true
                            WHERE p.patient_id = ANY(%s)
                            """,
                            (ids,),
                        )
                        extra = {row[0]: row for row in cur.fetchall()}
                except Exception:
                    extra = {}

                for p in raw_results:
                    pid = getattr(p, "patient_id", None)
                    ex  = extra.get(pid, ())
                    enriched.append({
                        "id":   pid,
                        "name": f"{getattr(p,'first_name','')} {getattr(p,'last_name','')}".strip(),
                        "age":  ex[1] if len(ex) > 1 else "—",
                        "gender": getattr(p, "gender", ""),
                        "department": ex[2] if len(ex) > 2 else "—",
                        "status": "Discharged" if (len(ex) > 3 and ex[3]) else "Active",
                        "symptoms": [], "diagnoses": [],
                    })
            conn.close()
        except Exception:
            use_mock = True
            patients_raw = _search_mock_patients(query)
            enriched = []
            for p in patients_raw:
                pid  = getattr(p, "patient_id", None)
                mock = next((m for m in MOCK_PATIENTS if m["id"] == pid), None)
                enriched.append(mock if mock else {
                    "id": pid,
                    "name": f"{getattr(p,'first_name','')} {getattr(p,'last_name','')}".strip(),
                    "age": "—", "gender": getattr(p, "gender", ""),
                    "department": "—", "symptoms": [], "diagnoses": [], "status": "Active",
                })
            st.info("Demo mode — database unavailable.", icon="ℹ️")

        if enriched:
            ages   = [p["age"] for p in enriched if isinstance(p.get("age"), (int, float))]
            female = sum(1 for p in enriched if p.get("gender") == "Female")
            male   = len(enriched) - female
            avg    = np.mean(ages) if ages else 0

            st.markdown(
                f"""
                <div class="metric-strip">
                    <div class="metric-box">
                        <div class="metric-val">{len(enriched)}</div>
                        <div class="metric-lbl">Total Patients</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-val">{avg:.0f}</div>
                        <div class="metric-lbl">Avg Age</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-val">{female}F / {male}M</div>
                        <div class="metric-lbl">Gender Split</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            for p in enriched:
                gender = p.get("gender", "")
                g_badge = f'<span class="badge badge-f">{gender}</span>' if gender == "Female" \
                          else f'<span class="badge badge-m">{gender}</span>'
                status = p.get("status", "Active")
                s_badge = f'<span class="badge badge-a">{status}</span>' if status == "Active" \
                          else f'<span class="badge badge-d">{status}</span>'
                dept = p.get("department", "")
                age  = p.get("age", "—")
                st.markdown(
                    f"""
                    <div class="pt-row">
                        <div class="pt-avatar">👤</div>
                        <div class="pt-body">
                            <div class="pt-name">{p['name']} &nbsp;{g_badge}{s_badge}</div>
                            <div class="pt-meta">
                                {p['id']} &nbsp;·&nbsp; Age {age}
                                &nbsp;·&nbsp; <span>{dept}</span>
                            </div>
                        </div>
                        <div class="pt-right">
                            <div class="pt-count">{age}</div>
                            <div class="pt-clabel">yrs old</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """
                <div class="empty">
                    <div class="empty-ico">🔍</div>
                    <div class="empty-ttl">No patients found</div>
                    <div class="empty-sub">Try adjusting your query</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div class="empty">
                <div class="empty-ico">🏥</div>
                <div class="empty-ttl">Start with a natural language query</div>
                <div class="empty-sub">
                    Type something like<br>
                    <em>"female patients over 60 with diabetes"</em><br>
                    to search patient records.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── History section ───────────────────────────────────────────────────────────

def _history_section() -> None:
    st.markdown(
        '<div class="ms-title">Search History</div>'
        '<div class="ms-sub">Your past natural language queries and results</div>',
        unsafe_allow_html=True,
    )

    history = MOCK_HISTORY
    try:
        conn = get_connection()
        raw = get_search_history(conn, st.session_state.get("ms_user_id", 1))
        conn.close()
        if raw:
            history = raw
    except Exception:
        pass

    # Filter input
    filt = st.text_input(
        "filter", placeholder="Filter history...",
        label_visibility="collapsed", key="ms_hist_filter",
    )

    total = len(history)
    avg_r = "4.0"
    st.markdown(
        f"""
        <div class="hist-stats">
            <div class="metric-box">
                <div class="metric-val">{total}</div>
                <div class="metric-lbl">Total Queries</div>
            </div>
            <div class="metric-box">
                <div class="metric-val">{avg_r}</div>
                <div class="metric-lbl">Avg Results</div>
            </div>
            <div class="metric-box">
                <div class="metric-val">90%</div>
                <div class="metric-lbl">Avg Success</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for h in history:
        q      = h.get("query_text", "")
        typ    = h.get("search_type", h.get("Search Type", ""))
        ts     = h.get("created_at",  h.get("Timestamp", ""))
        count  = h.get("results", "—")

        # highlight matching words
        if filt and filt.lower() in q.lower():
            parts = q.split(filt, 1)
            q_html = f"{parts[0]}<b>{filt}</b>{parts[1]}"
        else:
            q_html = q

        if filt and filt.lower() not in q.lower():
            continue

        st.markdown(
            f"""
            <div class="hist-row">
                <div class="hist-ico">🔍</div>
                <div class="hist-body">
                    <div class="hist-q">{q_html}</div>
                    <div class="hist-meta">
                        {ts} &nbsp;·&nbsp; Template: <span>{typ}</span>
                    </div>
                </div>
                <div class="hist-right">
                    <div class="hist-num">{count}</div>
                    <div class="hist-nlbl">patients</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── public entry ──────────────────────────────────────────────────────────────

def patient_search_page(role: str = "Clinician") -> None:
    _inject_css()
    page = _sidebar(role=role)

    if page == "Patient Search":
        _search_section()
    elif page == "Search History":
        _history_section()
    elif page == "Admin Panel":
        st.markdown(
            '<div class="ms-title">Admin Panel</div>'
            '<div class="ms-sub">Administrator access required</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="empty">
                <div class="empty-ico">🔒</div>
                <div class="empty-ttl">Admin Access Required</div>
                <div class="empty-sub">
                    Please sign out and log in as an Administrator.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
