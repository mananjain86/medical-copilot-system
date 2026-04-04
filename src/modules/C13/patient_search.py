"""
Module C13 – MediSearch Patient Search Page  (matches target design)
"""

import re
from html import escape
from dataclasses import dataclass
import streamlit as st

_BACKEND_IMPORT_ERROR: Exception | None = None

try:
    from src.modules.C13.backend import (
        SearchResult,
        get_connection,
        nl_search_pipeline,
        get_search_history,
        get_cohorts,
        get_cohort_members,
    )
except Exception as e:
    _BACKEND_IMPORT_ERROR = e

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

        :root {
            --primary-color: #6366F1;
            --primary-deep: #4F46E5;
            --accent-color: #06B6D4;
            --success-color: #10B981;
            --warning-color: #F59E0B;
            --bg-main: #0F172A;
            --bg-elevated: rgba(30, 41, 59, 0.74);
            --bg-soft: rgba(15, 23, 42, 0.52);
            --border-soft: rgba(148, 163, 184, 0.24);
            --text-primary: #F8FAFC;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --shadow-soft: 0 10px 24px rgba(2, 6, 23, 0.24);
        }

        [data-testid="stHeader"], [data-testid="stToolbar"], footer {
            display: block !important;
            visibility: visible !important;
        }

        .stApp {
            background: radial-gradient(circle at top right, #1E293B 0%, #0F172A 62%, #0B1220 100%) !important;
            color: var(--text-primary) !important;
        }
        .block-container {
            padding: 2rem 2.2rem !important;
            max-width: 100% !important;
            margin: 18px !important;
            border-radius: 18px;
            background: var(--bg-soft);
            border: 1px solid var(--border-soft);
            box-shadow: var(--shadow-soft);
            backdrop-filter: blur(12px);
        }
        [data-testid="stSidebar"] > div:first-child {
            background: linear-gradient(180deg, #131f36, #0f1a2d) !important;
            border-right: 1px solid var(--border-soft) !important;
        }

        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 99px; }

        div[data-testid="stSidebar"] div[data-testid="stButton"] button {
            width: 100% !important;
            background: transparent !important;
            color: var(--text-secondary) !important;
            border: 1px solid transparent !important;
            border-radius: 10px !important;
            text-align: left !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            padding: 10px 12px !important;
            justify-content: flex-start !important;
            transition: all .18s ease !important;
        }
        div[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
            background: rgba(99, 102, 241, 0.12) !important;
            border-color: rgba(99, 102, 241, 0.32) !important;
            color: #C7D2FE !important;
        }
        .nav-active button {
            background: rgba(99, 102, 241, 0.16) !important;
            border-color: rgba(99, 102, 241, 0.36) !important;
            color: #E0E7FF !important;
        }

        .ms-title {
            font-size: 26px;
            font-weight: 800;
            color: var(--text-primary);
            letter-spacing: -.4px;
        }
        .ms-sub {
            color: var(--text-secondary);
            font-size: 13px;
            margin-top: 4px;
            margin-bottom: 18px;
        }

        [data-testid="stTextInput"] input {
            background: #0F172A !important;
            border: 1px solid #334155 !important;
            border-radius: 12px !important;
            color: var(--text-primary) !important;
            font-size: 13px !important;
            padding: 11px 14px !important;
        }
        [data-testid="stTextInput"] input::placeholder { color: var(--text-muted) !important; }
        [data-testid="stTextInput"] input:focus {
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 2px rgba(99, 102, 241, .2) !important;
        }
        [data-testid="stTextInput"] > label { display: none !important; }

        div[data-testid="stButton"] > button {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-deep)) !important;
            border: none !important;
            border-radius: 12px !important;
            color: #fff !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            box-shadow: 0 8px 18px rgba(99, 102, 241, .28) !important;
            transition: transform .16s ease, box-shadow .16s ease !important;
        }
        div[data-testid="stButton"] > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 12px 20px rgba(99, 102, 241, .34) !important;
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
            display: grid; grid-template-columns: repeat(3, minmax(0,1fr));
            gap: 12px; margin: 18px 0 14px;
        }
        .metric-box {
            background: var(--bg-elevated);
            border: 1px solid var(--border-soft);
            border-radius: 14px;
            padding: 16px 18px;
            box-shadow: var(--shadow-soft);
        }
        .metric-val { font-size: 28px; font-weight: 800; color: var(--text-primary); line-height: 1; }
        .metric-lbl { font-size: 10px; color: var(--text-secondary); font-weight: 700;
                      text-transform: uppercase; letter-spacing: .8px; margin-top: 4px; }

        /* ── result row ── */
        .pt-row {
            display: flex; align-items: center;
            background: var(--bg-elevated);
            border: 1px solid var(--border-soft);
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 8px;
            box-shadow: var(--shadow-soft);
            transition: transform .15s ease, background .15s ease;
        }
        .pt-row:hover {
            background: rgba(51, 65, 85, .58);
            transform: translateY(-1px);
        }
        .pt-avatar {
            width: 36px; height: 36px; border-radius: 50%;
            background: linear-gradient(135deg, rgba(99, 102, 241, .24), rgba(6, 182, 212, .2));
            display: flex; align-items: center; justify-content: center;
            font-size: 14px; flex-shrink: 0; margin-right: 12px;
        }
        .pt-body     { flex: 1; min-width: 0; }
        .pt-name     { font-weight: 700; color: var(--text-primary); font-size: 14px; }
        .pt-meta     { color: var(--text-secondary); font-size: 11px; margin-top: 2px; }
        .pt-meta span { color: #cbd5e1; }
        .pt-right    { text-align: right; flex-shrink: 0; margin-left: 16px; }
        .pt-count    { font-size: 20px; font-weight: 800; color: var(--text-primary); line-height: 1; }
        .pt-clabel   { font-size: 10px; color: var(--text-secondary); font-weight: 600;
                       text-transform: uppercase; letter-spacing: .7px; margin-top: 2px; }

        /* badge */
        .badge { display:inline-block; padding:2px 8px; border-radius:99px;
                 font-size:10px; font-weight:600; margin-right:4px; }
        .badge-f { background:rgba(236, 72, 153, .15); color:#F9A8D4; }
        .badge-m { background:rgba(14, 165, 233, .16); color:#93C5FD; }
        .badge-a { background:rgba(16, 185, 129, .15); color:#6EE7B7; }
        .badge-d { background:rgba(245, 158, 11, .15); color:#FCD34D; }

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
            background: var(--bg-elevated);
            border: 1px solid var(--border-soft);
            border-radius: 12px; padding: 14px 16px; margin-bottom: 8px;
            gap: 12px;
            box-shadow: var(--shadow-soft);
        }
        .hist-row:hover { background: rgba(51, 65, 85, .56); }
        .hist-ico {
            width: 32px; height: 32px; border-radius: 50%;
            background: #0f172a; border: 1px solid var(--border-soft);
            display:flex; align-items:center; justify-content:center;
            font-size:13px; flex-shrink:0;
        }
        .hist-body { flex:1; min-width:0; }
        .hist-q    { color: var(--text-primary); font-size: 13px; font-weight: 600; }
        .hist-q b  { color: #C7D2FE; font-weight: 700; }
        .hist-meta { color: var(--text-secondary); font-size: 11px; margin-top: 3px; }
        .hist-meta span { color: #cbd5e1; }
        .hist-right { text-align:right; flex-shrink:0; }
        .hist-num   { font-size:20px; font-weight:800; color:var(--text-primary); }
        .hist-nlbl  { font-size:10px; color:var(--text-secondary); font-weight:600;
                      text-transform:uppercase; letter-spacing:.6px; }

        /* filter input */
        .filter-wrap { margin-bottom: 16px; }

        /* ── history stat strip ── */
        .hist-stats {
            display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:20px;
        }

        /* dataframe */
        [data-testid="stDataFrame"] {
            border-radius: 12px !important;
            overflow: hidden !important;
            border: 1px solid var(--border-soft) !important;
        }
        hr { border-color: var(--border-soft) !important; }

        /* ── detail card / expander polish ── */
        [data-testid="stExpander"] {
            border: 1px solid var(--border-soft) !important;
            border-radius: 14px !important;
            background: rgba(15, 23, 42, .55) !important;
            margin-bottom: 10px !important;
            overflow: hidden !important;
            box-shadow: var(--shadow-soft) !important;
        }
        [data-testid="stExpander"] details summary {
            background: linear-gradient(180deg, rgba(99,102,241,.2), rgba(30,41,59,.9)) !important;
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            border-bottom: 1px solid var(--border-soft) !important;
        }
        .detail-shell {
            background: var(--bg-elevated);
            border: 1px solid var(--border-soft);
            border-radius: 12px;
            padding: 12px 14px;
            margin-bottom: 12px;
            box-shadow: var(--shadow-soft);
        }
        .detail-hero {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 8px;
        }
        .detail-name {
            color: var(--text-primary);
            font-size: 16px;
            font-weight: 700;
        }
        .detail-sub {
            color: var(--text-secondary);
            font-size: 11px;
            margin-top: 2px;
        }
        .detail-pill {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 999px;
            border: 1px solid rgba(99, 102, 241, .38);
            background: rgba(99, 102, 241, .14);
            color: #C7D2FE;
            font-size: 10px;
            font-weight: 600;
            margin-right: 6px;
        }
        .chip-wrap {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin: 6px 0 10px;
        }
        .detail-chip {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 999px;
            border: 1px solid var(--border-soft);
            background: rgba(30, 41, 59, .86);
            color: #E2E8F0;
            font-size: 10px;
            font-weight: 500;
        }
        .section-cap {
            color: var(--text-secondary);
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: .8px;
            font-weight: 700;
            margin-top: 8px;
        }

        /* ── light theme alignment override ── */
        :root {
            --primary-color: #4F46E5;
            --primary-deep: #4338CA;
            --accent-color: #0EA5E9;
            --success-color: #059669;
            --warning-color: #D97706;
            --bg-main: #F8FAFC;
            --bg-elevated: #FFFFFF;
            --bg-soft: #F8FAFC;
            --border-soft: #E2E8F0;
            --text-primary: #0F172A;
            --text-secondary: #475569;
            --text-muted: #64748B;
            --shadow-soft: 0 10px 24px rgba(15, 23, 42, 0.08);
        }

        .stApp {
            background: radial-gradient(circle at top right, #EEF2FF 0%, #F8FAFC 60%, #FFFFFF 100%) !important;
            color: var(--text-primary) !important;
        }
        .block-container {
            background: #FFFFFF !important;
            border: 1px solid var(--border-soft) !important;
            box-shadow: var(--shadow-soft) !important;
            backdrop-filter: none !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            background: #FFFFFF !important;
            border-right: 1px solid var(--border-soft) !important;
        }
        div[data-testid="stSidebar"] div[data-testid="stButton"] button {
            color: #334155 !important;
        }
        div[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
            background: rgba(79, 70, 229, 0.08) !important;
            border-color: rgba(79, 70, 229, 0.25) !important;
            color: #3730A3 !important;
        }
        .nav-active button {
            background: rgba(79, 70, 229, 0.12) !important;
            border-color: rgba(79, 70, 229, 0.30) !important;
            color: #312E81 !important;
        }

        .metric-box,
        .pt-row,
        .hist-row,
        .detail-shell,
        .admin-stat-box,
        .tmpl-card {
            background: #FFFFFF !important;
            border: 1px solid var(--border-soft) !important;
            box-shadow: var(--shadow-soft) !important;
            backdrop-filter: none !important;
        }
        .ms-title,
        .pt-name,
        .hist-q,
        .tmpl-name,
        .detail-name,
        .metric-val,
        .pt-count,
        .hist-num,
        .admin-stat-val {
            color: #0F172A !important;
        }
        .ms-sub,
        .metric-lbl,
        .pt-meta,
        .hist-meta,
        .tmpl-meta,
        .detail-sub,
        .section-cap {
            color: #475569 !important;
        }
        .pt-meta span,
        .hist-meta span,
        .tmpl-meta b {
            color: #334155 !important;
        }

        [data-testid="stTextInput"] input {
            background: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            color: #0F172A !important;
        }
        [data-testid="stTextInput"] input::placeholder {
            color: #94A3B8 !important;
        }
        [data-testid="stTextInput"] input:focus {
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 2px rgba(79, 70, 229, .15) !important;
        }

        div[data-testid="stButton"] > button {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-deep)) !important;
            box-shadow: 0 8px 18px rgba(79, 70, 229, .20) !important;
        }

        [data-testid="stExpander"] {
            background: #FFFFFF !important;
            border: 1px solid var(--border-soft) !important;
            box-shadow: var(--shadow-soft) !important;
        }
        [data-testid="stExpander"] details summary {
            background: linear-gradient(180deg, #EEF2FF, #FFFFFF) !important;
            color: #0F172A !important;
            border-bottom: 1px solid var(--border-soft) !important;
        }
        .detail-pill {
            border-color: rgba(79, 70, 229, .28) !important;
            background: rgba(79, 70, 229, .10) !important;
            color: #4338CA !important;
        }
        .detail-chip {
            border-color: #CBD5E1 !important;
            background: #F8FAFC !important;
            color: #1E293B !important;
        }
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


def _load_patient_details(patient_id: int) -> dict | None:
    """Fetch detailed patient context for the details panel."""

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    p.patient_id,
                    p.first_name,
                    p.last_name,
                    p.gender,
                    DATE_PART('year', AGE(p.date_of_birth))::int AS age,
                    p.city
                FROM patients p
                WHERE p.patient_id = %s
                """,
                (patient_id,),
            )
            row = cur.fetchone()
            if not row:
                return None

            cur.execute(
                """
                SELECT
                    v.visit_date,
                    v.diagnosis,
                    COALESCE(d.specialization, 'General Medicine') AS department,
                    COALESCE(d.doctor_name, 'Unknown Doctor') AS doctor_name
                FROM visits v
                LEFT JOIN doctors d ON d.doctor_id = v.doctor_id
                WHERE v.patient_id = %s
                ORDER BY v.visit_date DESC
                LIMIT 20
                """,
                (patient_id,),
            )
            visits = [
                {
                    "visit_date": v[0],
                    "diagnosis": v[1],
                    "department": v[2],
                    "doctor_name": v[3],
                }
                for v in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT DISTINCT s.symptom_name
                FROM visits v
                JOIN patient_symptoms ps ON ps.visit_id = v.visit_id
                JOIN symptoms s ON s.symptom_id = ps.symptom_id
                WHERE v.patient_id = %s
                ORDER BY s.symptom_name
                LIMIT 12
                """,
                (patient_id,),
            )
            symptoms = [r[0] for r in cur.fetchall()]

            cur.execute(
                """
                SELECT
                    COALESCE(d.doctor_name, 'Unknown Doctor') AS doctor_name,
                    COUNT(*)::int AS visit_count
                FROM visits v
                LEFT JOIN doctors d ON d.doctor_id = v.doctor_id
                WHERE v.patient_id = %s
                GROUP BY COALESCE(d.doctor_name, 'Unknown Doctor')
                ORDER BY visit_count DESC, doctor_name
                """,
                (patient_id,),
            )
            doctor_visits = [
                {"doctor_name": r[0], "visit_count": r[1]}
                for r in cur.fetchall()
            ]

            diagnoses = sorted({(v.get("diagnosis") or "").strip() for v in visits if v.get("diagnosis")})

        return {
            "id": row[0],
            "name": f"{row[1]} {row[2]}".strip(),
            "gender": row[3],
            "age": row[4],
            "city": row[5],
            "visits": visits,
            "visit_count": len(visits),
            "doctor_visits": doctor_visits,
            "diagnoses": diagnoses,
            "symptoms": symptoms,
        }
    except Exception:
        return None
    finally:
        if conn:
            conn.close()


def _resolve_patient_details(item: dict) -> dict:
    """Resolve detailed patient data from DB with a safe fallback payload."""

    details = None
    patient_id = item.get("id")
    if isinstance(patient_id, int):
        details = _load_patient_details(patient_id)

    if details is None:
        details = {
            "id": item.get("id"),
            "name": item.get("name", "Unknown"),
            "gender": item.get("gender", "Unknown"),
            "age": item.get("age", "—"),
            "city": item.get("city", "—"),
            "visit_count": 0,
            "doctor_visits": [],
            "diagnoses": item.get("diagnoses", []),
            "visits": [],
            "symptoms": item.get("symptoms", []),
        }
    return details


def _chip_html(values: list) -> str:
    if not values:
        return ""
    chips = "".join(f'<span class="detail-chip">{escape(str(v))}</span>' for v in values if str(v).strip())
    return f'<div class="chip-wrap">{chips}</div>' if chips else ""


def render_patient_detail_card(item: dict, label_prefix: str = "Open patient card") -> None:
    """Render one expandable patient detail card with clinical context."""

    label = f"{label_prefix}: {item.get('name', 'Unknown')} ({item.get('id', '—')})"
    with st.expander(label, expanded=False):
        details = _resolve_patient_details(item)

        st.markdown(
            f"""
            <div class="detail-shell">
                <div class="detail-hero">
                    <div>
                        <div class="detail-name">{escape(str(details.get('name', 'Unknown')))}</div>
                        <div class="detail-sub">Patient deep-dive summary</div>
                    </div>
                    <div>
                        <span class="detail-pill">ID {escape(str(details.get('id', '—')))}</span>
                        <span class="detail-pill">{escape(str(details.get('gender', '—')))}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
        meta_col1.metric("Patient ID", str(details.get("id", "—")))
        meta_col2.metric("Age", str(details.get("age", "—")))
        meta_col3.metric("Gender", str(details.get("gender", "—")))
        meta_col4.metric("Location", str(details.get("city", "—")))

        left_col, right_col = st.columns(2)
        with left_col:
            diagnoses = details.get("diagnoses", [])
            if diagnoses:
                st.markdown('<div class="section-cap">Disease / Diagnosis</div>', unsafe_allow_html=True)
                st.markdown(_chip_html(diagnoses), unsafe_allow_html=True)
            symptoms = details.get("symptoms", [])
            if symptoms:
                st.markdown('<div class="section-cap">Symptoms</div>', unsafe_allow_html=True)
                st.markdown(_chip_html(symptoms), unsafe_allow_html=True)

        with right_col:
            st.metric("Total Visits", int(details.get("visit_count", 0) or 0))
            doctor_rows = details.get("doctor_visits", [])
            if doctor_rows:
                st.markdown("**Visits by Doctor**")
                st.dataframe(
                    doctor_rows,
                    width="stretch",
                    hide_index=True,
                )

        visits = details.get("visits", [])
        if visits:
            visit_rows = []
            for v in visits[:10]:
                vd = v.get("visit_date")
                if hasattr(vd, "strftime"):
                    vd = vd.strftime("%Y-%m-%d")
                visit_rows.append(
                    {
                        "Visit Date": vd,
                        "Doctor": v.get("doctor_name", "—"),
                        "Department": v.get("department", "—"),
                        "Diagnosis": v.get("diagnosis", "—"),
                    }
                )
            st.markdown("**Recent Visits**")
            st.dataframe(visit_rows, width="stretch", hide_index=True)


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
                clicked = st.button(label, width="stretch", key=key)
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
        searched = st.button("🔍 Search", width="stretch", key="ms_search_btn")

    run = searched or st.session_state.pop("_ms_run", False)

    if run and (query or "").strip():
        use_mock = False
        try:
            conn = get_connection()
            result = nl_search_pipeline(conn, st.session_state.get("ms_user_id", 1), query)
            raw_results = result.get("results", [])
            enriched = []
            for p in raw_results:
                enriched.append({
                    "id": getattr(p, "patient_id", None),
                    "name": f"{getattr(p,'first_name','')} {getattr(p,'last_name','')}".strip(),
                    "age": getattr(p, "age", "—"),
                    "gender": getattr(p, "gender", ""),
                    "department": "—",
                    "status": getattr(p, "status", "Active"),
                    "symptoms": [], "diagnoses": [],
                })
            conn.close()
        except Exception as e:
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
            if _BACKEND_IMPORT_ERROR is not None:
                st.caption(f"Backend import error: {type(_BACKEND_IMPORT_ERROR).__name__}: {_BACKEND_IMPORT_ERROR}")
            st.caption(f"Runtime error: {type(e).__name__}: {e}")

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

            for idx, p in enumerate(enriched):
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

                render_patient_detail_card(p)
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

    def _display_cohort_name(raw: str) -> str:
        text = str(raw or "").strip()
        # Normalize legacy generated names: "U1 | clinical | query text" -> "query text"
        if "|" in text:
            parts = [p.strip() for p in text.split("|") if p.strip()]
            if len(parts) >= 3 and parts[0].lower().startswith("u"):
                return parts[-1]
        return text or "Untitled Cohort"

    # Deduplicate cohorts by normalized display name; keep the latest record for each name.
    unique_by_name = {}
    for item in cohorts:
        raw_name = _display_cohort_name(item.get("cohort_name"))
        key = " ".join(raw_name.lower().split())
        created_at = str(item.get("created_at") or "")
        prev = unique_by_name.get(key)
        if prev is None or created_at > str(prev.get("created_at") or ""):
            unique_by_name[key] = item

    cohorts = sorted(
        unique_by_name.values(),
        key=lambda c: str(c.get("created_at") or ""),
        reverse=True,
    )

    if not cohorts:
        st.info("No cohorts available.")
        return

    # --- TOP STATS ---
    c1, c2, c3, c4 = st.columns(4)
    total_members = sum(int(c.get("member_count", 0) or 0) for c in cohorts)
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
        grid_cols = st.columns(2)
        for idx, c in enumerate(cohorts):
            with grid_cols[idx % 2]:
                cid = c.get("cohort_id")
                name_raw = c.get("cohort_name") or "Untitled Cohort"
                name = _display_cohort_name(name_raw)
                count = int(c.get("member_count", 0) or 0)
                date = c.get("created_at")
                theme_color = ["#00b4d8", "#4FD1C5", "#F6AD55", "#E53E3E"][idx % 4]

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
                    unsafe_allow_html=True,
                )

                exp_label = f"Open Cohort #{cid} - {name}"
                with st.expander(exp_label, expanded=False):
                    members = []
                    member_conn = None
                    try:
                        member_conn = get_connection()
                        members = get_cohort_members(member_conn, int(cid), limit=200)
                    except Exception:
                        members = []
                    finally:
                        try:
                            if member_conn:
                                member_conn.close()
                        except Exception:
                            pass

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
                        st.dataframe(pd.DataFrame(member_rows), width="stretch", hide_index=True)
                    else:
                        st.info(f"No members found for Cohort #{cid}.")

    with anal_col:
        st.markdown("#### 📊 Clinical Distribution")
        labels = ["Diabetes", "Hypertension", "Asthma", "Cardiac", "Others"]
        sizes = [35, 30, 15, 10, 10]

        fig, ax = plt.subplots(figsize=(4, 4))
        colors = ["#00b4d8", "#4FD1C5", "#F6AD55", "#E53E3E", "#1E293B"]
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#ffffff")

        ax.pie(
            sizes,
            labels=None,
            startangle=140,
            colors=colors,
            wedgeprops=dict(width=0.4, edgecolor="#ffffff", linewidth=2),
        )

        ax.text(0, 0, f"{total_members}\nTotal", ha="center", va="center", fontsize=14, fontweight="bold", color="#0f172a")
        ax.axis("equal")
        st.pyplot(fig)

        for i, label in enumerate(labels):
            st.markdown(
                f'''
                <div style="display:flex; justify-content: space-between; align-items:center; margin-bottom:8px; background:#f8fafc; padding:4px 10px; border-radius:6px; border-left: 2px solid {colors[i]};">
                    <span style="font-size:11px; color:#334155;">{label}</span>
                    <span style="font-size:11px; font-weight:700; color:{colors[i]};">{sizes[i]}%</span>
                </div>
                ''',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="ms-sub" style="margin-top:10px;">Click a cohort card and expand it to view that cohort\'s patient list.</div>', unsafe_allow_html=True)


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
