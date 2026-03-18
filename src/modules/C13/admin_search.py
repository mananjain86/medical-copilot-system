"""
Module C13 – MediSearch Admin Search Page  (matches target design)
"""

import streamlit as st
from src.modules.C13.backend import get_connection, nl_search_pipeline, get_search_history, get_cohorts
from src.modules.C13.patient_search import (
    MOCK_PATIENTS, MOCK_HISTORY, _search_mock_patients,
    _inject_css as _shared_css,
    _history_section,
)

# ── mock NL templates (matching target Admin Panel screenshot) ─────────────────
MOCK_TEMPLATES = [
    {
        "name": "Age Range Search",
        "category": "DEMOGRAPHIC",
        "sql": "SELECT * FROM PATIENT WHERE age >= :min_age",
        "params": ["min_age", "max_age"],
        "uses": 142,
        "success": 91,
        "updated": "2024-02-10",
    },
    {
        "name": "Symptom-Based Search",
        "category": "CLINICAL",
        "sql": "SELECT * FROM PATIENT WHERE symptoms LIKE :s",
        "params": ["symptom"],
        "uses": 289,
        "success": 88,
        "updated": "2024-02-15",
    },
    {
        "name": "Demographic + Clinical Combo",
        "category": "DEMOGRAPHIC",
        "sql": "SELECT * FROM PATIENT NHERL gender = :gender",
        "params": ["gender", "age", "symptom"],
        "uses": 198,
        "success": 84,
        "updated": "2024-03-01",
    },
    {
        "name": "Department Search",
        "category": "DEMOGRAPHIC",
        "sql": "SELECT * FROM PATIENT WHERE department = :dc",
        "params": ["department"],
        "uses": 76,
        "success": 97,
        "updated": "2024-01-20",
    },
    {
        "name": "Temporal Search",
        "category": "TEMPORAL",
        "sql": "SELECT * FROM PATIENT WHERE admission_date f",
        "params": ["start_date", "end_date"],
        "uses": 54,
        "success": 85,
        "updated": "2024-02-08",
    },
]

SUGGESTIONS = [
    "female patients over 60",
    "diabetic patients",
    "patients with hypertension",
    "elderly patients with heart disease",
    "patients in cardiology department",
    "female patients with diabetes over 60",
]


def _inject_css() -> None:
    _shared_css()
    st.markdown(
        """
        <style>
        /* admin avatar purple */
        .ms-ava { background: linear-gradient(135deg,#9b59b6,#6c3483) !important; }
        .ms-ava-role { color: #9b59b6 !important; }

        /* ── Admin Panel stat strip ── */
        .admin-stats {
            display: grid; grid-template-columns: repeat(3, auto);
            gap: 12px; margin-bottom: 24px;
        }
        .admin-stat-box {
            background: #111f30; border: 1px solid #1a2e44;
            border-radius: 10px; padding: 16px 22px;
        }
        .admin-stat-lbl { font-size: 10px; color: #2e4a60; font-weight: 700;
                          text-transform: uppercase; letter-spacing: .8px; margin-bottom: 4px; }
        .admin-stat-val { font-size: 28px; font-weight: 800; color: #e8f4fd; }

        /* ── Template card grid ── */
        .tmpl-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 14px;
        }
        .tmpl-card {
            background: #111f30; border: 1px solid #1a2e44;
            border-radius: 12px; padding: 16px 18px;
            position: relative;
        }
        .tmpl-header {
            display: flex; justify-content: space-between;
            align-items: center; margin-bottom: 10px;
        }
        .tmpl-name { color: #d4eaf8; font-size: 14px; font-weight: 700; }
        .tmpl-cat-demo { background: rgba(0,180,216,.12); color:#00b4d8;
                         font-size:9px; font-weight:700; padding:3px 8px;
                         border-radius:99px; letter-spacing:.5px; }
        .tmpl-cat-clin { background: rgba(0,200,120,.10); color:#4ade80;
                         font-size:9px; font-weight:700; padding:3px 8px;
                         border-radius:99px; letter-spacing:.5px; }
        .tmpl-cat-temp { background: rgba(250,170,60,.10); color:#fbbf24;
                         font-size:9px; font-weight:700; padding:3px 8px;
                         border-radius:99px; letter-spacing:.5px; }
        .tmpl-sql {
            background: #0d1828; border: 1px solid #1a2e44;
            border-radius: 6px; padding: 8px 10px;
            font-family: 'Courier New', monospace; font-size: 11px;
            color: #4b7594; white-space: nowrap; overflow: hidden;
            text-overflow: ellipsis; margin-bottom: 10px;
        }
        .tmpl-params-lbl { font-size:10px; color:#2e4a60; font-weight:700;
                           text-transform:uppercase; letter-spacing:.7px; margin-bottom:6px; }
        .tmpl-param-tag {
            display: inline-block;
            background: #0d1828; border: 1px solid #1a2e44;
            color: #4b7594; font-size: 11px;
            padding: 2px 8px; border-radius: 5px; margin-right: 4px; margin-bottom: 4px;
        }
        .tmpl-footer {
            display: flex; align-items: center; justify-content: space-between;
            margin-top: 10px; padding-top: 10px; border-top: 1px solid #1a2e44;
        }
        .tmpl-meta { color: #2e4a60; font-size: 11px; }
        .tmpl-meta b { color: #3a6278; }
        .tmpl-success { color: #4ade80; font-size: 11px; font-weight: 600; }

        /* ── new-template button ── */
        .new-tmpl-wrap {
            position: absolute; top: 1.8rem; right: 2rem;
        }

        /* Website-aligned admin overrides */
        .tmpl-card,
        .admin-stat-box {
            background: #ffffff !important;
            border: 1px solid #e5e7eb !important;
        }
        .tmpl-name,
        .admin-stat-val { color: #111827 !important; }
        .tmpl-meta,
        .admin-stat-lbl { color: #6b7280 !important; }
        .tmpl-meta b { color: #4b5563 !important; }
        .tmpl-sql {
            background: #f9fafb !important;
            border: 1px solid #e5e7eb !important;
            color: #374151 !important;
        }
        .tmpl-param-tag {
            background: #f9fafb !important;
            border: 1px solid #e5e7eb !important;
            color: #374151 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _sidebar() -> str:
    with st.sidebar:
        st.markdown("## MediCare")
        st.caption("Clinical Query Copilot")

        st.session_state.setdefault("ms_current_page", "Patient Search")
        page = st.session_state.ms_current_page

        def _nav(label: str, key: str):
            active = page == label
            if active:
                st.markdown('<div class="nav-active">', unsafe_allow_html=True)
            clicked = st.button(label, use_container_width=True, key=key)
            if active:
                st.markdown("</div>", unsafe_allow_html=True)
            if clicked:
                st.session_state.ms_current_page = label
                st.rerun()

        _nav("Patient Search", "nav_ps")
        _nav("Search History", "nav_sh")
        _nav("Admin Panel", "nav_ap")

        st.divider()
        st.caption("Role: Administrator")

    return st.session_state.ms_current_page


def _search_section() -> None:
    st.markdown(
        '<div class="ms-title">Patient Search</div>'
        '<div class="ms-sub">Administrator view — full access to all patient records</div>',
        unsafe_allow_html=True,
    )

    col_in, col_btn = st.columns([6, 1], gap="small")
    with col_in:
        query = st.text_input(
            "q", placeholder='e.g. "female patients over 60 with diabetes"',
            label_visibility="collapsed", key="ms_admin_query",
        )
    with col_btn:
        searched = st.button("🔍 Search", use_container_width=True, key="ms_adm_btn")

    run = searched or st.session_state.pop("_ma_run", False)

    if run and (query or "").strip():
        patients_raw = []
        use_mock = False
        try:
            conn = get_connection()
            result = nl_search_pipeline(conn, 1, query)
            conn.close()
            patients_raw = result.get("results", [])
        except Exception:
            use_mock = True
            patients_raw = _search_mock_patients(query)
            st.info("Demo mode — database unavailable.", icon="ℹ️")

        if patients_raw:
            import pandas as pd
            rows = []
            for p in patients_raw:
                pid  = getattr(p, "patient_id", None)
                mock = next((m for m in MOCK_PATIENTS if m["id"] == pid), None)
                rows.append({
                    "ID": mock["id"] if mock else pid,
                    "Name": mock["name"] if mock else f"{getattr(p,'first_name','')} {getattr(p,'last_name','')}".strip(),
                    "Age": mock["age"] if mock else "—",
                    "Gender": mock["gender"] if mock else getattr(p, "gender", ""),
                    "Department": mock["department"] if mock else "—",
                    "Status": mock["status"] if mock else "Active",
                })
            st.success(f"Found **{len(rows)}** patient(s)")
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.markdown(
                '<div class="empty"><div class="empty-ico">🔍</div>'
                '<div class="empty-ttl">No patients found</div></div>',
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


def _admin_panel_section() -> None:
    # Title + "+ New Template" button
    hdr_col, btn_col = st.columns([6, 1], gap="small")
    with hdr_col:
        st.markdown(
            '<div class="ms-title">Admin Panel</div>'
            '<div class="ms-sub">Manage NL query templates used by the search engine</div>',
            unsafe_allow_html=True,
        )
    with btn_col:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("＋ New Template", key="new_tmpl", use_container_width=True)

    # Stat strip
    total_uses = sum(t["uses"] for t in MOCK_TEMPLATES)
    avg_success = int(sum(t["success"] for t in MOCK_TEMPLATES) / len(MOCK_TEMPLATES))
    st.markdown(
        f"""
        <div class="admin-stats">
            <div class="admin-stat-box">
                <div class="admin-stat-lbl">Total Templates</div>
                <div class="admin-stat-val">{len(MOCK_TEMPLATES)}</div>
            </div>
            <div class="admin-stat-box">
                <div class="admin-stat-lbl">Total Uses</div>
                <div class="admin-stat-val">{total_uses}</div>
            </div>
            <div class="admin-stat-box">
                <div class="admin-stat-lbl">Avg Success Rate</div>
                <div class="admin-stat-val">{avg_success}%</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Recent Cohorts")
    try:
        conn = get_connection()
        cohorts = get_cohorts(conn)
        conn.close()
    except Exception:
        cohorts = []

    if cohorts:
        import pandas as pd

        rows = []
        for c in cohorts[:10]:
            rows.append({
                "Cohort ID": c.get("cohort_id"),
                "Name": c.get("cohort_name"),
                "Members": c.get("member_count", 0),
                "Created At": c.get("created_at"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No cohorts available yet. Run a few searches to generate cohorts.")

    st.divider()

    # Template grid — 2 columns
    CAT_CLASS = {
        "DEMOGRAPHIC": "tmpl-cat-demo",
        "CLINICAL":    "tmpl-cat-clin",
        "TEMPORAL":    "tmpl-cat-temp",
    }

    # Split into rows of 2
    for row_start in range(0, len(MOCK_TEMPLATES), 2):
        col1, col2 = st.columns(2, gap="medium")
        for col_idx, col in enumerate([col1, col2]):
            tmpl_idx = row_start + col_idx
            if tmpl_idx >= len(MOCK_TEMPLATES):
                break
            t = MOCK_TEMPLATES[tmpl_idx]
            cat_class = CAT_CLASS.get(t["category"], "tmpl-cat-demo")
            params_html = "".join(
                f'<span class="tmpl-param-tag">{p}</span>' for p in t["params"]
            )
            with col:
                st.markdown(
                    f"""
                    <div class="tmpl-card">
                        <div class="tmpl-header">
                            <div class="tmpl-name">{t['name']}</div>
                            <div class="{cat_class}">{t['category']}</div>
                        </div>
                        <div class="tmpl-sql">{t['sql']}</div>
                        <div class="tmpl-params-lbl">Parameters</div>
                        <div>{params_html}</div>
                        <div class="tmpl-footer">
                            <span class="tmpl-meta">
                                <b>{t['uses']} uses</b>
                                &nbsp;·&nbsp; Updated {t['updated']}
                            </span>
                            <span class="tmpl-success">● {t['success']}% success</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                # Edit / Delete under each card
                ec, dc = st.columns(2, gap="small")
                with ec:
                    st.button("✏ Edit",   key=f"edit_{tmpl_idx}",   use_container_width=True)
                with dc:
                    st.button("🗑 Delete", key=f"delete_{tmpl_idx}", use_container_width=True)


# ── public entry ──────────────────────────────────────────────────────────────

def admin_search_page() -> None:
    _inject_css()
    page = _sidebar()

    if page == "Patient Search":
        _search_section()
    elif page == "Search History":
        _history_section()
    elif page == "Admin Panel":
        _admin_panel_section()
