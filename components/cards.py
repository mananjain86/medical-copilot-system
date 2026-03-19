# components/cards.py
import streamlit as st

def premium_card(title, content, icon="🏥", footer=None):
    st.markdown(f"""
    <div class="medical-card">
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <span style="font-size: 24px; margin-right: 12px;">{icon}</span>
            <h3 style="margin: 0;">{title}</h3>
        </div>
        <div style="color: #4A5568; margin-bottom: 15px;">
            {content}
        </div>
        {f'<div style="font-size: 12px; color: #A0AEC0; border-top: 1px solid #E2E8F0; padding-top: 10px;">{footer}</div>' if footer else ''}
    </div>
    """, unsafe_allow_html=True)

def stats_card(label, value, delta=None, icon="📈"):
    st.markdown(f"""
    <div class="medical-card" style="padding: 15px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 14px; color: #718096; margin-bottom: 5px;">{icon} {label}</div>
                <div style="font-size: 24px; font-weight: 700; color: #5B47D8;">{value}</div>
            </div>
            {f'<div style="color: {"#38A169" if "+" in delta else "#E53E3E"}; font-weight: 600;">{delta}</div>' if delta else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

def patient_row(name, time, diagnosis, icon_text="SH"):
    st.markdown(f"""
    <div class="medical-card" style="padding: 10px; margin-bottom: 10px;">
        <div style="display: flex; align-items: center;">
            <div class="patient-avatar">{icon_text}</div>
            <div style="flex-grow: 1;">
                <div style="font-weight: 600; color: #2D3748;">{name}</div>
                <div style="font-size: 12px; color: #718096;">{diagnosis} • {time}</div>
            </div>
            <button style="background: none; border: none; cursor: pointer; color: #A0AEC0;">⋮</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
