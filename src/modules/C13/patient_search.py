"""
Module C13 – MediSearch Patient Search Page  (matches target design)
"""

import re
from dataclasses import dataclass
import streamlit as st

try:
    from src.modules.C13.backend import (
        SearchResult,
        get_connection,
        nl_search_pipeline,
        get_search_history,
        get_cohorts,
        get_cohort_members,
    )
except Exception:
    @dataclass
    class SearchResult:
        patient_id: str
        first_name: str
        last_name: str
        gender: str
        age: int
        status: str

    # Keep UI usable in frontend/demo mode even if DB deps (e.g. psycopg2) are missing.
    def get_connection():
        raise RuntimeError("Database backend unavailable")

    def nl_search_pipeline(*args, **kwargs):
        raise RuntimeError("Database backend unavailable")

    def get_search_history(*args, **kwargs):
        raise RuntimeError("Database backend unavailable")

    def get_cohorts(*args, **kwargs):
        raise RuntimeError("Database backend unavailable")

    def get_cohort_members(*args, **kwargs):
        raise RuntimeError("Database backend unavailable")


# ── suggestion chips ──────────────────────────────────────────────────────────
SUGGESTIONS = [
    "female patients over 60",
    "diabetic patients",
    "patients with hypertension",
    "elderly patients with heart disease",
    "patients in cardiology department",
    "female patients with diabetes over 60",
]

import json
from pathlib import Path

# ── load mock patient data ────────────────────────────────────────────────────
def load_mock_patients():
    json_path = Path(__file__).parent / "mock_patients.json"
    if json_path.exists():
        with open(json_path, "r") as f:
            return json.load(f)
    return []

MOCK_PATIENTS = load_mock_patients()

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

        /* ── restore default streamlit containers ── */
        [data-testid="stHeader"], [data-testid="stToolbar"], footer {
            display: block !important;
            visibility: visible !important;
        }

        /* ── background (applied to stApp to avoid covering header) ── */
        .stApp { 
            background: #0F172A !important; 
        }
        [data-testid="stSidebar"] > div:first-child {
            background: #1E293B !important;
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        .block-container { 
            padding: 2.2rem 2.4rem !important; 
            max-width: 100% !important;
            background: rgba(30, 41, 59, 0.4);
            border-radius: 20px;
            margin: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

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
# _sidebar function removed here to resolve duplication.

# Note: Sidebar and Page entry moved to end of file for clarity.


def _search_mock_patients(query: str):
    if not query.strip():
        return []
    q = query.lower()
    gender_filter = None
    if re.search(r"\b(?:female|woman|women|lady|ladies)\b", q):
        gender_filter = "Female"
    elif re.search(r"\b(?:male|man|men|gentleman|gentlemen|guy|guys)\b", q):
        gender_filter = "Male"

    age_between_match = re.search(r"between\s+(\d+)\s+(?:and|to)\s+(\d+)", q)
    min_age, max_age, exact_age = None, None, None
    if age_between_match:
        a, b = int(age_between_match.group(1)), int(age_between_match.group(2))
        min_age, max_age = min(a, b), max(a, b)
    else:
        exact_match = re.search(r"(?:aged|is|age)\s+(\d+)(?:\s+years\s+old)?", q)
        if exact_match:
            exact_age = int(exact_match.group(1))
        else:
            age_above_match = re.search(r"(?:over|above|older|greater|more|at least|min|minimum)\s+(\d+)|>\s*(\d+)", q)
            if age_above_match:
                vals = [g for g in age_above_match.groups() if g]
                if vals: min_age = int(vals[0])

            age_below_match = re.search(r"(?:under|below|younger|less|at most|max|maximum)\s+(\d+)|<\s*(\d+)", q)
            if age_below_match:
                vals = [g for g in age_below_match.groups() if g]
                if vals: max_age = int(vals[0])

    status_filter = None
    if re.search(r"\bactive\b", q):
        status_filter = "Active"
    elif re.search(r"\bdischarged\b", q):
        status_filter = "Discharged"

    # Improved stop words to include all synonyms
    stop_pattern = (
        r"\bpatients?\b|\bwith\b|\band\b|\bthe\b|\bover\b|\babove\b|\bolder\b|\bgreater\b|\bmore\b"
        r"|\bunder\b|\bbelow\b|\byounger\b|\bless\b|\bthan\b|\bbetween\b|\bat\b|\bleast\b|\bmost\b"
        r"|\bmin\b|\bmax\b|\bminimum\b|\bmaximum\b"
        r"|\bfemale\b|\bmale\b|\bwoman\b|\bwomen\b|\blady\b|\bladies\b|\bman\b|\bmen\b|\bguy\b|\bguys\b"
        r"|\belderly\b|\byears?\b|\bold\b|\bage\b|\bstatus\b|\bactive\b|\bdischarged\b"
    )
    keywords = re.sub(stop_pattern, " ", q).split()
    keywords = [k for k in keywords if len(k) > 2]
    results = []
    for p in MOCK_PATIENTS:
        if gender_filter and p["gender"] != gender_filter:
            continue
        if exact_age and p.get("age", 0) != exact_age:
            continue
        if min_age and p.get("age", 0) < min_age:
            continue
        if max_age and p.get("age", 0) > max_age:
            continue
        if status_filter and p.get("status", "").lower() != status_filter.lower():
            continue
        if keywords:
            hay = " ".join(p.get("symptoms", []) + p.get("diagnoses", []) + [p.get("department", ""), p.get("name", "")]).lower()
            if not any(kw in hay for kw in keywords):
                continue
        results.append(SearchResult(
            patient_id=p["id"],
            first_name=p["name"].split()[0],
            last_name=" ".join(p["name"].split()[1:]),
            gender=p["gender"],
            age=p.get("age", 0),
            status=p.get("status", "Unknown")
        ))
    return results


def _sidebar(role: str = "Clinician") -> str:
    with st.sidebar:
        st.markdown("## MediCare")
        st.caption("Clinical Query Copilot")

        is_admin = role == "Administrator"
        st.session_state.setdefault("ms_current_page", "Patient")
        if st.session_state.ms_current_page not in {"Patient", "History", "Cohort"}:
            st.session_state.ms_current_page = "Patient"
        page = st.session_state.ms_current_page

        def _nav(label: str, key: str):
            active = page == label
            with st.container():
                if active:
                    st.markdown('<div class="nav-active">', unsafe_allow_html=True)
                clicked = st.button(label, use_container_width=True, key=key)
                if active:
                    st.markdown("</div>", unsafe_allow_html=True)
                if clicked:
                    st.session_state.ms_current_page = label
                    st.rerun()

        _nav("Patient", "nav_ps")
        _nav("History", "nav_sh")
        _nav("Cohort", "nav_cohorts")

        st.divider()
        st.caption(f"Role: {role}")

        if is_admin:
            st.markdown("### Admin Panel")
            try:
                conn = get_connection()
                cohorts = get_cohorts(conn)
                conn.close()
            except Exception:
                cohorts = []

            total_cohorts = len(cohorts)
            total_members = sum(int(c.get("member_count", 0) or 0) for c in cohorts)
            st.caption(f"Cohorts: {total_cohorts} | Members: {total_members}")

            if cohorts:
                latest = cohorts[:5]
                options = [f"#{c.get('cohort_id')} ({c.get('member_count', 0)})" for c in latest]
                idx = st.selectbox(
                    "Recent Cohorts",
                    range(len(options)),
                    format_func=lambda i: options[i],
                    key="ms_admin_sidebar_cohort_idx",
                )
                selected = latest[idx]
                st.caption(selected.get("cohort_name", ""))
            else:
                st.caption("No cohorts yet. Run searches to generate cohorts.")

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
                                COALESCE(d.specialization, 'General Medicine') AS department,
                                NULL::date AS discharge_date
                            FROM patients p
                            LEFT JOIN LATERAL (
                                SELECT doctor_id
                                FROM visits
                                WHERE patient_id = p.patient_id
                                ORDER BY visit_date DESC
                                LIMIT 1
                            ) v ON true
                            LEFT JOIN doctors d ON d.doctor_id = v.doctor_id
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
            genders = [str(p.get("gender", "")).strip().lower() for p in enriched]
            female = sum(1 for g in genders if g == "female")
            male   = sum(1 for g in genders if g == "male")
            avg    = (sum(ages) / len(ages)) if ages else 0

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
                gender_raw = str(p.get("gender", "")).strip()
                gender_key = gender_raw.lower()
                if gender_key == "female":
                    gender = "Female"
                    g_badge = f'<span class="badge badge-f">{gender}</span>'
                elif gender_key == "male":
                    gender = "Male"
                    g_badge = f'<span class="badge badge-m">{gender}</span>'
                else:
                    gender = gender_raw or "Unknown"
                    g_badge = f'<span class="badge">{gender}</span>'
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

    history = []
    using_mock = False
    try:
        conn = get_connection()
        raw = get_search_history(conn, st.session_state.get("ms_user_id", 1))
        conn.close()
        if raw:
            # Format the created_at datetime into a human-readable "Xh ago" string
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            for row in raw:
                ts = row.get("created_at")
                if hasattr(ts, "astimezone"):
                    diff = now - ts.astimezone(timezone.utc)
                    total_seconds = int(diff.total_seconds())
                    if total_seconds < 3600:
                        row["created_at"] = f"{total_seconds // 60}m ago"
                    elif total_seconds < 86400:
                        row["created_at"] = f"{total_seconds // 3600}h ago"
                    else:
                        row["created_at"] = f"{total_seconds // 86400}d ago"
            history = raw
        else:
            history = MOCK_HISTORY
            using_mock = True
    except Exception:
        history = MOCK_HISTORY
        using_mock = True

    if using_mock:
        st.info("Demo mode — showing sample history. Connect to a database to see real search history.", icon="ℹ️")

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


def _cohorts_section() -> None:
    st.markdown(
        '<div class="ms-title">Cohorts</div>'
        '<div class="ms-sub">Saved patient groups generated from search queries</div>',
        unsafe_allow_html=True,
    )

    try:
        conn = get_connection()
        cohorts = get_cohorts(conn)
    except Exception:
        cohorts = []
        conn = None

    if not cohorts:
        cohorts = [
            {"cohort_id": 1, "cohort_name": "Diabetes Type 2 - High Risk", "member_count": 145, "created_at": "2024-01-10"},
            {"cohort_id": 2, "cohort_name": "Post-Op Cardiac Follow-up", "member_count": 82, "created_at": "2024-02-15"},
            {"cohort_id": 3, "cohort_name": "Respiratory Intensive Care", "member_count": 45, "created_at": "2024-03-01"},
            {"cohort_id": 4, "cohort_name": "Elderly Care Program", "member_count": 210, "created_at": "2024-03-12"}
        ]

    import pandas as pd
    import matplotlib.pyplot as plt

    # --- TOP STATS ---
    c1, c2, c3, c4 = st.columns(4)
    total_members = sum(int(c.get('member_count', 0)) for c in cohorts)
    avg_size = total_members // len(cohorts) if cohorts else 0
    
    with c1:
        st.markdown(f'<div class="metric-box" style="border-left: 4px solid #00b4d8;"><div class="metric-val" style="color:#00b4d8;">{len(cohorts)}</div><div class="metric-lbl">Total Cohorts</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-box" style="border-left: 4px solid #4FD1C5;"><div class="metric-val" style="color:#4FD1C5;">{total_members}</div><div class="metric-lbl">Total Members</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-box" style="border-left: 4px solid #F6AD55;"><div class="metric-val" style="color:#F6AD55;">{avg_size}</div><div class="metric-lbl">Avg Size</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-box" style="border-left: 4px solid #E53E3E;"><div class="metric-val" style="color:#E53E3E;">12%</div><div class="metric-lbl">Monthly Growth</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- TWO COLUMN LAYOUT: List on Left, Analytics on Right ---
    list_col, anal_col = st.columns([1.8, 1])

    with list_col:
        st.markdown("#### 📂 Saved Patient Cohorts")
        # Grid of cards (2 columns within the left side)
        grid_cols = st.columns(2)
        for idx, c in enumerate(cohorts):
            with grid_cols[idx % 2]:
                cid = c.get('cohort_id')
                name = c.get('cohort_name')
                count = c.get('member_count', 0)
                date = c.get('created_at')
                
                # Dynamic color for icon/badge based on index
                theme_color = ['#00b4d8', '#4FD1C5', '#F6AD55', '#E53E3E'][idx % 4]
                
                st.markdown(
                    f"""
                    <div class="pt-row" style="flex-direction: column; align-items: flex-start; gap: 4px; padding: 18px; border-top: 3px solid {theme_color};">
                        <div style="display:flex; justify-content: space-between; width:100%;">
                            <span class="badge" style="background: {theme_color}22; color:{theme_color}; border: 1px solid {theme_color}44;">ID #{cid}</span>
                            <span style="font-size:10px; color:#4b7594; font-weight:600;">{date}</span>
                        </div>
                        <div class="pt-name" style="margin: 8px 0; font-size: 15px; min-height: 40px;">{name}</div>
                        <div style="display:flex; align-items:baseline; gap:6px;">
                            <div class="pt-count" style="font-size:20px; font-weight:800; color:{theme_color};">{count}</div>
                            <div class="pt-clabel" style="font-size:10px;">active patients</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button(f"Manage Cohort #{cid}", key=f"an_{cid}", use_container_width=True):
                    st.session_state.current_cohort_id = cid
                    st.session_state.current_cohort_name = name
                    st.rerun()

    with anal_col:
        st.markdown("#### 📊 Clinical Distribution")
        labels = ['Diabetes', 'Hypertension', 'Asthma', 'Cardiac', 'Others']
        sizes = [35, 30, 15, 10, 10]
        
        # Draw a nicer donut chart with better labels
        fig, ax = plt.subplots(figsize=(4, 4))
        colors = ['#00b4d8', '#4FD1C5', '#F6AD55', '#E53E3E', '#1E293B']
        fig.patch.set_facecolor('none')
        ax.set_facecolor('none')
        
        wedges, texts = ax.pie(
            sizes, labels=None, startangle=140, colors=colors,
            wedgeprops=dict(width=0.4, edgecolor='#0F172A', linewidth=2)
        )
        
        # Center text (Total count)
        ax.text(0, 0, f"{total_members}\nTotal", ha='center', va='center', fontsize=14, fontweight='bold', color='#e8f4fd')
            
        ax.axis('equal')
        st.pyplot(fig)
        
        # Redesigned Legend
        for i, label in enumerate(labels):
            st.markdown(
                f'''
                <div style="display:flex; justify-content: space-between; align-items:center; margin-bottom:8px; background:rgba(30,41,59,0.3); padding:4px 10px; border-radius:6px; border-left: 2px solid {colors[i]};">
                    <span style="font-size:11px; color:#cde;">{label}</span>
                    <span style="font-size:11px; font-weight:700; color:{colors[i]};">{sizes[i]}%</span>
                </div>
                ''', 
                unsafe_allow_html=True
            )

    # --- SELECTION & MEMBERS ---
    st.divider()
    
    selected_id = st.session_state.get("current_cohort_id", cohorts[0].get("cohort_id"))
    selected_name = st.session_state.get("current_cohort_name", cohorts[0].get("cohort_name"))
    
    st.markdown(
        f'<div class="ms-title" style="font-size:18px;">Members: {selected_name}</div>'
        f'<div class="ms-sub">Detailed patient roster for Cohort #{selected_id}</div>',
        unsafe_allow_html=True
    )

    members = []
    try:
        if conn is None:
            conn = get_connection()
        members = get_cohort_members(conn, selected_id, limit=200)
    except Exception:
        members = []
    finally:
        if conn:
            conn.close()

    if members:
        member_rows = []
        for m in members:
            member_rows.append({
                "ID": m.get("patient_id"),
                "First Name": m.get("first_name", ""),
                "Last Name": m.get("last_name", ""),
                "Sex": m.get("gender"),
                "Age": m.get("age"),
                "City": m.get("city"),
                "Added": m.get("added_at").strftime("%Y-%m-%d") if hasattr(m.get("added_at"), "strftime") else m.get("added_at"),
            })
        st.dataframe(pd.DataFrame(member_rows), use_container_width=True, hide_index=True)
    else:
        st.info(f"No members found for Cohort #{selected_id}. Showing sample data for demo.")
        sample_members = [
            {"ID": 101, "First Name": "Rahul", "Last Name": "Sharma", "Sex": "Male", "Age": 45, "City": "Delhi", "Added": "2024-01-10"},
            {"ID": 102, "First Name": "Sneha", "Last Name": "Iyer", "Sex": "Female", "Age": 38, "City": "Chennai", "Added": "2024-01-12"},
            {"ID": 103, "First Name": "Amit", "Last Name": "Verma", "Sex": "Male", "Age": 52, "City": "Mumbai", "Added": "2024-01-15"}
        ]
        st.dataframe(pd.DataFrame(sample_members), use_container_width=True, hide_index=True)


# ── public entry ──────────────────────────────────────────────────────────────

def patient_search_page(role: str = "Clinician") -> None:
    _inject_css()
    page = _sidebar(role=role)

    if page == "Patient":
        _search_section()
    elif page == "History":
        _history_section()
    elif page == "Cohort":
        _cohorts_section()
