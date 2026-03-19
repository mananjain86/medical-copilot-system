# views/cohort_patients.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from components.cards import premium_card, stats_card

def show_cohort_patients():
    st.markdown("# 👥 Cohort Patients Analysis")
    st.markdown("*Group and analyze patient populations based on clinical criteria*")
    
    st.divider()
    
    # Cohort Overview Stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        stats_card("Total Cohorts", "12", "+2 this month", "📁")
    with c2:
        stats_card("Patients in Cohorts", "1,245", "65% of total", "👥")
    with c3:
        stats_card("Active Research", "4", "Ongoing", "🔬")
    with c4:
        stats_card("High Risk Groups", "3", "Requires attention", "⚠️")
        
    st.divider()
    
    # Cohort Management Tabs
    tab1, tab2, tab3 = st.tabs(["📋 My Cohorts", "🔍 Create New Cohort", "📊 Analytics"])
    
    with tab1:
        st.subheader("Your Active Cohorts")
        
        cohorts = [
            {"name": "Diabetes Type 2 - High Risk", "patients": 145, "created": "2024-01-10", "status": "Active"},
            {"name": "Post-Op Cardiac Follow-up", "patients": 82, "created": "2024-02-15", "status": "Review Required"},
            {"name": "Pediatric Asthma Group A", "patients": 210, "created": "2023-11-20", "status": "Active"},
            {"name": "Geriatric Mobility Study", "patients": 56, "created": "2024-03-01", "status": "New"}
        ]
        
        for cohort in cohorts:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.markdown(f"### {cohort['name']}")
                    st.caption(f"Created on {cohort['created']}")
                with col2:
                    st.metric("Patients", cohort['patients'])
                with col3:
                    st.info(cohort['status'])
                with col4:
                    if st.button("View Details", key=f"btn_{cohort['name']}"):
                        st.session_state.current_cohort = cohort
                st.markdown("---")
        
        # Detailed View if a cohort is selected
        if "current_cohort" in st.session_state:
            c = st.session_state.current_cohort
            st.markdown(f"## 📋 Details: {c['name']}")
            st.write(f"**Created:** {c['created']} | **Status:** {c['status']}")
            
            # Mock patient list for this cohort
            st.dataframe(pd.DataFrame({
                "Patient ID": [f"P{i:03d}" for i in range(1, 11)],
                "Name": ["Sarah Hostern", "John Lane", "Maria Garcia", "David Miller", "Emma Wilson", "James Taylor", "Linda Anderson", "Robert Thomas", "Barbara Moore", "Michael Jackson"],
                "Age": [45, 62, 38, 55, 29, 74, 51, 68, 42, 33],
                "Condition": ["Controlled" if i%2==0 else "Unstable" for i in range(10)]
            }))
            
            if st.button("Close Details"):
                del st.session_state.current_cohort
                st.rerun()

    with tab2:
        st.subheader("Define New Patient Cohort")
        with st.form("new_cohort"):
            name = st.text_input("Cohort Name", placeholder="e.g., Hypertension Adults 40-60")
            
            col1, col2 = st.columns(2)
            with col1:
                age_range = st.slider("Age Range", 0, 100, (30, 60))
                gender = st.multiselect("Gender", ["Male", "Female", "Other"], default=["Male", "Female"])
            
            with col2:
                diagnosis = st.multiselect("Clinical Diagnosis", ["Hypertension", "Diabetes", "Asthma", "Cardiac", "Chronic Pain"])
                medications = st.multiselect("Specific Medications", ["Metformin", "Lisinopril", "Albuterol", "Atorvastatin"])
            
            criteria = st.text_area("Additional SQL Criteria (Optional)", placeholder="SELECT * FROM patients WHERE last_visit > '2024-01-01'")
            
            submitted = st.form_submit_button("Preview Cohort")
            
        if submitted:
            st.success(f"Cohort generated! Found 87 patients matching criteria.")
            st.dataframe(pd.DataFrame({
                "Patient ID": ["P001", "P023", "P145"],
                "Name": ["John Doe", "Jane Smith", "Robert Brown"],
                "Age": [45, 52, 38],
                "Last Visit": ["2024-03-10", "2024-03-12", "2024-03-05"]
            }))
            if st.button("Save Cohort"):
                st.balloons()
                st.success("Cohort saved successfully!")

    with tab3:
        st.subheader("Cohort Distribution Analysis")
        
        # Mock Data for Analytics
        labels = ['Diabetes', 'Hypertension', 'Asthma', 'Cardiac', 'Others']
        sizes = [35, 30, 15, 10, 10]
        
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['#5B47D8', '#4FD1C5', '#F6AD55', '#E53E3E', '#A0AEC0'])
        ax.axis('equal')
        st.pyplot(fig)
        
        st.markdown("#### Patient Growth in Cohorts")
        chart_data = pd.DataFrame(
            np.random.randn(20, 3),
            columns=['Diabetes', 'Hypertension', 'Asthma']
        )
        st.line_chart(chart_data)

if __name__ == "__main__":
    show_cohort_patients()
