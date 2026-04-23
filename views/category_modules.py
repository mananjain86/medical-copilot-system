import streamlit as st
from views.module_detail import module_detail

# Module catalogue shared across all categories (A–I).
# Each entry: (code, name)
MODULES = {
    "A - Patient Clinical Data": [
        ("A1", "Patient Demographics & Visit History Database"),
        ("A2", "Chronic Disease Patient Record Management"),
        ("A3", "Pediatric Patient Clinical Data System"),
        ("A4", "Geriatric Patient Health Record Database"),
        ("A5", "Patient Allergy & Immunization Tracking System"),
        ("A6", "Clinical Alert System for Abnormal Vital Values"),
    ],
    "B - Symptom-Disease Diagnosis": [
        ("B1", "Symptom-Disease Mapping Database"),
        ("B2", "Fever-Based Differential Diagnosis System"),
        ("B3", "Respiratory Symptom Diagnosis Database"),
        ("B4", "Gastrointestinal Disorder Diagnosis Support"),
        ("B5", "Neurological Symptom Analysis Database"),
        ("B6", "Rule-Based Disease Ranking System"),
    ],
    "C - Clinical Query Copilot": [
        ("C1", "Natural Language Patient Search System"),
        ("C2", "Clinical Query Translator for Laboratory Records"),
        ("C3", "Voice-Assisted Clinical Query System (Text Simulation)"),
        ("C4", "Doctor-Friendly SQL Query Dashboard"),
        ("C5", "Smart Clinical Views using SQL"),
        ("C6", "Question-Answering System for Hospital Database"),
    ],
    "D - Drug & Prescription Safety": [
        ("D1", "Drug-Drug Interaction Alert Database"),
        ("D2", "Prescription Validation & Consistency System"),
        ("D3", "Allergy-Aware Medication Alert System"),
        ("D4", "Polypharmacy Risk Detection Database"),
        ("D5", "High-Risk Drug Monitoring System"),
        ("D6", "Automated Prescription Audit System"),
    ],
    "E - ICU & Real-Time Monitoring": [
        ("E1", "ICU Vital Signs Monitoring Database"),
        ("E2", "Emergency Room Patient Alert System"),
        ("E3", "Cardiac ICU Monitoring Database"),
        ("E4", "Neonatal ICU Monitoring System"),
        ("E5", "Threshold-Based Clinical Alert Database"),
        ("E6", "Time-Series Patient Health Data System"),
    ],
    "F - Case-Based Decision Support": [
        ("F1", "Historical Case Comparison Database"),
        ("F2", "Treatment Outcome Analysis System"),
        ("F3", "Disease Progression Case Repository"),
        ("F4", "Readmission Risk Analysis Database"),
        ("F5", "Therapy Effectiveness Evaluation System"),
        ("F6", "Similar Patient Case Retrieval System"),
    ],
    "G - Secure EHR & Access Control": [
        ("G1", "Secure Electronic Health Record (EHR) Database"),
        ("G2", "Role-Based Access Control for Hospital Systems"),
        ("G3", "Clinical Audit Trail & Logging System"),
        ("G4", "Patient Consent & Data Privacy Database"),
        ("G5", "Multi-Role Access Control System"),
        ("G6", "Secure Clinical Summary View Generator"),
    ],
    "H - Laboratory Test Interpretation": [
        ("H1", "Laboratory Test Management Database"),
        ("H2", "Automated Lab Result Interpretation System"),
        ("H3", "Reference Range Validation Database"),
        ("H4", "Follow-Up Test Recommendation System"),
        ("H5", "Pathology Report Management Database"),
        ("H6", "Critical Lab Value Alert System"),
    ],
    "I - Integrated Capstone Projects": [
        ("I1", "Integrated Clinical Decision Support Database (Patients, Symptoms, Drugs, Labs)"),
        ("I2", "AI-Inspired Medical Copilot using DBMS Concept"),
    ],
}

# Legacy alias kept for backwards-compatibility with any existing session state
# that may still reference the old key name.
MODULES["A - Clinical Data"] = MODULES["A - Patient Clinical Data"]


def category_modules():
    if st.session_state.get("view") == "module_detail":
        module_detail()
        return

    selected_category = st.session_state.get("selected_category", "")
    category_label = selected_category.split(" - ", 1)[0] if " - " in selected_category else selected_category
    st.markdown(f"### Category {category_label} \u203a {selected_category}")
    st.markdown("## Modules")

    modules = MODULES.get(selected_category, [])
    if not modules:
        st.warning(f"No modules found for category: **{selected_category}**")
    else:
        cols = st.columns(3)
        for idx, module in enumerate(modules):
            with cols[idx % 3]:
                if st.button(f"{module[0]} \u2013 {module[1]}", key=f"mod_{category_label}_{module[0]}"):
                    st.session_state.selected_module = module
                    st.session_state.view = "module_detail"
                    st.rerun()

    st.divider()
    if st.button("\u2b05 Back to Dashboard"):
        st.session_state.view = "dashboard"
        st.rerun()
