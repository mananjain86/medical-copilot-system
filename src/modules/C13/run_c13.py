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
    page_title="MediCare - Natural Language Patient Search",
    page_icon="🩺",
    layout="wide",
)

# Keep standalone behavior aligned with main website flow: no extra login layer.
st.session_state.setdefault("ms_user_role", "Clinician")

role = st.session_state.ms_user_role
if role == "Administrator":
    from src.modules.C13.admin_search import admin_search_page

    admin_search_page()
else:
    from src.modules.C13.patient_search import patient_search_page

    patient_search_page(role="Clinician")
