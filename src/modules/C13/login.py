"""
Module C13 – MediSearch Login Page  (matches target design)
"""
import streamlit as st

DEMO_CREDENTIALS = {
    "Clinician":     {"email": "clinician@medisearch.com", "password": "demo123"},
    "Administrator": {"email": "admin@medisearch.com",     "password": "demo123"},
}


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
        #MainMenu, footer, [data-testid="stHeader"],
        [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; visibility: hidden !important; }

        :root {
            --primary-color: #6366F1;
            --primary-deep: #4F46E5;
            --bg-main: #0F172A;
            --text-primary: #F8FAFC;
            --text-secondary: #94A3B8;
            --border-soft: rgba(148, 163, 184, .22);
        }
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at top right, #1E293B 0%, #0F172A 62%, #0B1220 100%);
            min-height: 100vh;
        }
        .block-container { padding: 0 !important; max-width: 100% !important; }

        /* ── outer wrapper ── */
        .login-outer {
            display: flex; min-height: 100vh;
            align-items: center; justify-content: center;
        }

        /* ── card ── */
        .login-card {
            background: rgba(30, 41, 59, 0.78);
            border: 1px solid var(--border-soft);
            border-radius: 18px;
            padding: 34px 30px 28px;
            width: 430px;
            box-shadow: 0 12px 28px rgba(2, 6, 23, 0.30);
            backdrop-filter: blur(12px);
            animation: fadeUp .35s ease;
        }
        @keyframes fadeUp {
            from { opacity:0; transform:translateY(14px); }
            to   { opacity:1; transform:translateY(0); }
        }

        /* ── logo row ── */
        .logo-row {
            display: flex; align-items: center; gap: 12px; margin-bottom: 4px;
        }
        .logo-icon {
            width: 42px; height: 42px;
            background: linear-gradient(135deg, #00b4d8, #0070f3);
            border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            font-size: 22px;
        }
        .logo-title { font-size: 22px; font-weight: 800; color: var(--text-primary); }
        .logo-sub   { font-size: 12px; color: var(--text-secondary); margin-top: 1px; }

        .card-divider { height: 1px; background: var(--border-soft); margin: 18px 0 16px; }

        /* ── label above role ── */
        .role-hint { color: var(--text-secondary); font-size: 12px; margin-bottom: 10px; }

        /* ── Streamlit radio → pill toggle ── */
        div[data-testid="stRadio"] {
            background: rgba(15, 23, 42, 0.58) !important;
            border: 1px solid var(--border-soft) !important;
            border-radius: 10px !important;
            padding: 3px !important;
            margin-bottom: 20px !important;
        }
        div[data-testid="stRadio"] > div { display: flex !important; gap: 0 !important; }
        div[data-testid="stRadio"] label {
            flex: 1 !important; text-align: center !important;
            padding: 8px 0 !important; border-radius: 8px !important;
            font-size: 13px !important; font-weight: 500 !important;
            color: var(--text-secondary) !important; cursor: pointer !important;
            transition: all .18s !important;
        }
        div[data-testid="stRadio"] label:has(input:checked) {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-deep)) !important;
            color: #fff !important;
        }
        div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] { display: none; }

        /* ── field label ── */
        .f-label {
            color: #CBD5E1; font-size: 12px; font-weight: 500;
            margin-bottom: 6px; margin-top: 14px;
        }

        /* ── inputs ── */
        [data-testid="stTextInput"] input {
            background: #0F172A !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
            color: var(--text-primary) !important;
            font-size: 13px !important;
            font-family: 'Inter', sans-serif !important;
            padding: 11px 14px !important;
        }
        [data-testid="stTextInput"] input:focus {
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 2px rgba(99,102,241,.2) !important;
        }
        [data-testid="stTextInput"] input::placeholder { color: #64748B !important; }
        [data-testid="stTextInput"] > label { display: none !important; }

        /* ── sign-in button ── */
        div[data-testid="stButton"] > button {
            width: 100% !important;
            background: linear-gradient(135deg, var(--primary-color), var(--primary-deep)) !important;
            color: #fff !important; border: none !important;
            border-radius: 8px !important;
            padding: 12px 0 !important;
            font-size: 14px !important; font-weight: 700 !important;
            font-family: 'Inter', sans-serif !important;
            margin-top: 6px !important;
            box-shadow: 0 8px 18px rgba(99,102,241,.30) !important;
            transition: opacity .18s !important;
        }
        div[data-testid="stButton"] > button:hover { opacity: .88 !important; }

        /* ── demo hint ── */
        .demo-hint {
            text-align: center;
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 16px;
        }
        .demo-hint a { color: #C7D2FE; text-decoration: none; }

        /* light theme alignment override */
        :root {
            --primary-color: #4F46E5;
            --primary-deep: #4338CA;
            --bg-main: #F8FAFC;
            --text-primary: #0F172A;
            --text-secondary: #475569;
            --border-soft: #E2E8F0;
        }
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at top right, #EEF2FF 0%, #F8FAFC 60%, #FFFFFF 100%) !important;
        }
        .login-card {
            background: #FFFFFF !important;
            border: 1px solid var(--border-soft) !important;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08) !important;
            backdrop-filter: none !important;
        }
        .logo-title { color: var(--text-primary) !important; }
        .logo-sub,
        .role-hint,
        .demo-hint { color: var(--text-secondary) !important; }
        .card-divider { background: var(--border-soft) !important; }

        div[data-testid="stRadio"] {
            background: #F8FAFC !important;
            border: 1px solid var(--border-soft) !important;
        }
        div[data-testid="stRadio"] label { color: #475569 !important; }

        .f-label { color: #334155 !important; }
        [data-testid="stTextInput"] input {
            background: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            color: #0F172A !important;
        }
        [data-testid="stTextInput"] input::placeholder { color: #94A3B8 !important; }
        [data-testid="stTextInput"] input:focus {
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 2px rgba(79, 70, 229, .14) !important;
        }

        div[data-testid="stButton"] > button {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-deep)) !important;
            box-shadow: 0 8px 18px rgba(79, 70, 229, .20) !important;
        }
        .demo-hint a { color: #4338CA !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def login_page() -> None:
    _inject_css()

    st.session_state.setdefault("ms_logged_in", False)
    st.session_state.setdefault("ms_role_sel", "Clinician")

    col = st.columns([1, 2, 1])[1]           # centre column
    with col:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        # Logo
        role = st.session_state.get("ms_role_sel", "Clinician")
        creds = DEMO_CREDENTIALS[role]
        st.markdown(
            """
            <div class="logo-row">
                <div class="logo-icon">🫀</div>
                <div>
                    <div class="logo-title">MediSearch</div>
                    <div class="logo-sub">MediCare Natural Language Patient Search</div>
                </div>
            </div>
            <div class="card-divider"></div>
            <div class="role-hint">Select your role to autofill demo credentials:</div>
            """,
            unsafe_allow_html=True,
        )

        # Role toggle
        role = st.radio(
            "role", ["Clinician", "Administrator"],
            horizontal=True, label_visibility="collapsed",
            key="ms_role_sel",
        )
        creds = DEMO_CREDENTIALS[role]

        # Email
        st.markdown('<div class="f-label">Email Address</div>', unsafe_allow_html=True)
        email = st.text_input(
            "email", value=creds["email"],
            placeholder="Enter your email",
            label_visibility="collapsed", key="ms_email",
        )

        # Password
        st.markdown('<div class="f-label">Password</div>', unsafe_allow_html=True)
        password = st.text_input(
            "password", value=creds["password"],
            type="password", placeholder="Enter your password",
            label_visibility="collapsed", key="ms_password",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign In", width="stretch"):
            if email and password:
                st.session_state.ms_logged_in = True
                st.session_state.ms_user_role = role
                st.rerun()
            else:
                st.error("Please enter your email and password.")

        st.markdown(
            f'<div class="demo-hint">Demo: '
            f'<a href="#">{creds["email"]}</a> / '
            f'<a href="#">{creds["password"]}</a></div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
