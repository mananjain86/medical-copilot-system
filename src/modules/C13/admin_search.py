"""
Module C13 – MediSearch Admin Search Page  (matches target design)
"""

import streamlit as st
from src.modules.C13.patient_search import (
    _inject_css as _shared_css,
    render_patient_detail_card,
    _history_section,
    _cohorts_section,
    _search_mock_patients,
    _record_mock_search,
    _ensure_mock_state,
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
        "sql": "SELECT * FROM PATIENT WHERE gender = :gender",
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
        "sql": "SELECT * FROM PATIENT WHERE admission_date BETWEEN :start_date AND :end_date",
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
        .ms-ava { background: linear-gradient(135deg,#6366F1,#4F46E5) !important; }
        .ms-ava-role { color: #C7D2FE !important; }

        .admin-stats {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin-bottom: 22px;
        }
        .admin-stat-box {
            background: rgba(30, 41, 59, 0.74);
            border: 1px solid rgba(148, 163, 184, 0.24);
            border-radius: 14px;
            padding: 16px 18px;
            box-shadow: 0 10px 24px rgba(2, 6, 23, 0.24);
            backdrop-filter: blur(12px);
        }
        .admin-stat-lbl {
            font-size: 10px;
            color: #94A3B8;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .8px;
            margin-bottom: 4px;
        }
        .admin-stat-val {
            font-size: 28px;
            font-weight: 800;
            color: #F8FAFC;
        }

        .tmpl-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 14px;
        }
        .tmpl-card {
            background: rgba(30, 41, 59, 0.74);
            border: 1px solid rgba(148, 163, 184, 0.24);
            border-radius: 14px;
            padding: 16px 18px;
            position: relative;
            box-shadow: 0 10px 24px rgba(2, 6, 23, 0.22);
            backdrop-filter: blur(12px);
        }
        .tmpl-header {
            display: flex; justify-content: space-between;
            align-items: center; margin-bottom: 10px;
        }
        .tmpl-name { color: #F8FAFC; font-size: 14px; font-weight: 700; }
        .tmpl-cat-demo { background: rgba(99,102,241,.16); color:#E0E7FF;
                         font-size:9px; font-weight:700; padding:3px 8px;
                         border-radius:99px; letter-spacing:.5px; }
        .tmpl-cat-clin { background: rgba(16,185,129,.14); color:#6EE7B7;
                         font-size:9px; font-weight:700; padding:3px 8px;
                         border-radius:99px; letter-spacing:.5px; }
        .tmpl-cat-temp { background: rgba(245,158,11,.14); color:#FCD34D;
                         font-size:9px; font-weight:700; padding:3px 8px;
                         border-radius:99px; letter-spacing:.5px; }
        .tmpl-sql {
            background: rgba(15, 23, 42, .72); border: 1px solid rgba(148, 163, 184, .22);
            border-radius: 6px; padding: 8px 10px;
            font-family: 'Courier New', monospace; font-size: 11px;
            color: #CBD5E1; white-space: nowrap; overflow: hidden;
            text-overflow: ellipsis; margin-bottom: 10px;
        }
        .tmpl-params-lbl { font-size:10px; color:#94A3B8; font-weight:700;
                           text-transform:uppercase; letter-spacing:.7px; margin-bottom:6px; }
        .tmpl-param-tag {
            display: inline-block;
            background: rgba(15, 23, 42, .72); border: 1px solid rgba(148, 163, 184, .22);
            color: #CBD5E1; font-size: 11px;
            padding: 2px 8px; border-radius: 5px; margin-right: 4px; margin-bottom: 4px;
        }
        .tmpl-footer {
            display: flex; align-items: center; justify-content: space-between;
            margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(148, 163, 184, .24);
        }
        .tmpl-meta { color: #94A3B8; font-size: 11px; }
        .tmpl-meta b { color: #E2E8F0; }
        .tmpl-success { color: #6EE7B7; font-size: 11px; font-weight: 600; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _sidebar() -> str:
    with st.sidebar:
        st.markdown("## MediCare")
        st.caption("Clinical Query Copilot")

        st.session_state.setdefault("ms_current_page", "Patient")
        page = st.session_state.ms_current_page

        def _nav(label: str, key: str):
            active = page == label
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

    def _trigger_search_on_enter() -> None:
        st.session_state["_ma_run"] = True

    col_in, col_btn = st.columns([6, 1], gap="small")
    with col_in:
        query = st.text_input(
            "q", placeholder='e.g. "female patients over 60 with diabetes"',
            label_visibility="collapsed", key="ms_admin_query", on_change=_trigger_search_on_enter,
        )
    with col_btn:
        searched = st.button("🔍 Search", width="stretch", key="ms_adm_btn")

    run = searched or st.session_state.pop("_ma_run", False)

    if run and (query or "").strip():
        user_id = 5 # Administrator ID
        try:
            import requests
            API_BASE_URL = "http://127.0.0.1:8000/api/v1"
            resp = requests.post(f"{API_BASE_URL}/search", json={"user_id": user_id, "query": query})
            if resp.status_code == 200:
                response = resp.json()
                patients_raw = response.get("results", [])
                
                # Map backend results to UI format
                rows = []
                detail_items = []
                for r in patients_raw:
                    row = {
                        "ID": r.get("patient_id"),
                        "Name": f"{r.get('first_name')} {r.get('last_name')}",
                        "Age": r.get("age"),
                        "Gender": r.get("gender"),
                        "Department": "—",
                        "Status": r.get("status", "Active"),
                    }
                    rows.append(row)
                    detail_items.append({
                        "id": r.get("patient_id"),
                        "name": row["Name"],
                        "age": r.get("age"),
                        "gender": r.get("gender"),
                        "city": "—",
                        "diagnoses": [],
                        "symptoms": [],
                    })
            else:
                raise RuntimeError("API Search Failed")
        except Exception:
            patients_raw = _search_mock_patients(query)
            _record_mock_search(query, patients_raw)
            # ... process mock as before if needed, but the original code had its own logic
            rows = []
            detail_items = []
            for p in patients_raw:
                row = {
                    "ID": p.get("id"),
                    "Name": p.get("name", "Unknown"),
                    "Age": p.get("age", "—"),
                    "Gender": p.get("gender", ""),
                    "Department": p.get("department", "—"),
                    "Status": p.get("status", "Active"),
                }
                rows.append(row)
                detail_items.append({
                    "id": row["ID"],
                    "name": row["Name"],
                    "age": row["Age"],
                    "gender": row["Gender"],
                    "city": "—",
                    "diagnoses": [],
                    "symptoms": [],
                })
        finally:
            if conn:
                conn.close()

        if isinstance(sql_payload, dict) and "sql" in sql_payload:
            with st.expander("🔍 Generated SQL Query", expanded=False):
                if sql_payload.get("explanation"):
                    st.info(sql_payload.explanation)
                from src.modules.C13.patient_search import _render_sql
                rendered = _render_sql(sql_payload["sql"], sql_payload.get("params", {}))
                st.code(rendered, language="sql")

        if rows:
            import pandas as pd
            st.success(f"Found **{len(rows)}** patient(s)")
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

            st.markdown("### Patient Detail Cards")
            for item in detail_items:
                render_patient_detail_card(item)
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
        st.button("＋ New Template", key="new_tmpl", width="stretch")

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
    _ensure_mock_state()
    cohorts = st.session_state.ms_mock_cohorts

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
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
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
                    st.button("✏ Edit",   key=f"edit_{tmpl_idx}",   width="stretch")
                with dc:
                    st.button("🗑 Delete", key=f"delete_{tmpl_idx}", width="stretch")


# ── public entry ──────────────────────────────────────────────────────────────

def admin_search_page() -> None:
    _inject_css()
    page = _sidebar()

    if page == "Patient":
        _search_section()
    elif page == "History":
        _history_section()
    elif page == "Cohort":
        _cohorts_section()
    elif page == "Admin Panel":
        _admin_panel_section()
