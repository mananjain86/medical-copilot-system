"""
Run the C13 MediSearch UI (standalone Streamlit entry point).

Usage (from project root):
    python3 -m streamlit run src/modules/C13/run_c13.py --server.port 8502
"""
import sys
from pathlib import Path

# ensure project root is on the path so submodule imports work
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import streamlit as st

st.set_page_config(
    page_title="MediSearch – Natural Language Patient Search",
    page_icon="🩺",
    layout="wide",
)

# session defaults
st.session_state.setdefault("ms_logged_in", False)
st.session_state.setdefault("ms_user_role", None)

if not st.session_state.ms_logged_in:
    # import directly from the file – avoids loading backend.py (psycopg2) at startup
    from src.modules.C13.login import login_page
    login_page()
else:
    role = st.session_state.ms_user_role
    if role == "Administrator":
        from src.modules.C13.admin_search import admin_search_page
        admin_search_page()
    else:
        from src.modules.C13.patient_search import patient_search_page
        patient_search_page(role="Clinician")
