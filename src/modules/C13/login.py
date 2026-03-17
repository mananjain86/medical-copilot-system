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

        /* ── full background ── */
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(ellipse at 35% 40%, #0e2040 0%, #080f1e 55%, #050b16 100%);
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
            background: #111827;
            border: 1px solid #1f2d44;
            border-radius: 16px;
            padding: 36px 32px 28px;
            width: 420px;
            box-shadow: 0 8px 40px rgba(0,0,0,0.6);
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
        .logo-title { font-size: 22px; font-weight: 800; color: #f0f6ff; }
        .logo-sub   { font-size: 12px; color: #4b6278; margin-top: 1px; }

        .card-divider {
            height: 1px; background: #1f2d44; margin: 20px 0 18px;
        }

        /* ── label above role ── */
        .role-hint { color: #6b8290; font-size: 12px; margin-bottom: 10px; }

        /* ── Streamlit radio → pill toggle ── */
        div[data-testid="stRadio"] {
            background: #0d1828 !important;
            border: 1px solid #1f2d44 !important;
            border-radius: 10px !important;
            padding: 3px !important;
            margin-bottom: 20px !important;
        }
        div[data-testid="stRadio"] > div { display: flex !important; gap: 0 !important; }
        div[data-testid="stRadio"] label {
            flex: 1 !important; text-align: center !important;
            padding: 8px 0 !important; border-radius: 8px !important;
            font-size: 13px !important; font-weight: 500 !important;
            color: #4b6278 !important; cursor: pointer !important;
            transition: all .18s !important;
        }
        div[data-testid="stRadio"] label:has(input:checked) {
            background: linear-gradient(135deg, #00b4d8, #0070f3) !important;
            color: #fff !important;
        }
        div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] { display: none; }

        /* ── field label ── */
        .f-label {
            color: #8ba5b8; font-size: 12px; font-weight: 500;
            margin-bottom: 6px; margin-top: 14px;
        }

        /* ── inputs ── */
        [data-testid="stTextInput"] input {
            background: #0d1828 !important;
            border: 1px solid #1f2d44 !important;
            border-radius: 8px !important;
            color: #cce4f6 !important;
            font-size: 13px !important;
            font-family: 'Inter', sans-serif !important;
            padding: 11px 14px !important;
        }
        [data-testid="stTextInput"] input:focus {
            border-color: #00b4d8 !important;
            box-shadow: 0 0 0 2px rgba(0,180,216,.15) !important;
        }
        [data-testid="stTextInput"] input::placeholder { color: #2a3f52 !important; }
        [data-testid="stTextInput"] > label { display: none !important; }

        /* ── sign-in button ── */
        div[data-testid="stButton"] > button {
            width: 100% !important;
            background: linear-gradient(90deg, #00b4d8, #0070f3) !important;
            color: #fff !important; border: none !important;
            border-radius: 8px !important;
            padding: 12px 0 !important;
            font-size: 14px !important; font-weight: 700 !important;
            font-family: 'Inter', sans-serif !important;
            margin-top: 6px !important;
            box-shadow: 0 2px 14px rgba(0,180,216,.3) !important;
            transition: opacity .18s !important;
        }
        div[data-testid="stButton"] > button:hover { opacity: .88 !important; }

        /* ── demo hint ── */
        .demo-hint {
            text-align: center; font-size: 11px; color: #38516a; margin-top: 16px;
        }
        .demo-hint a { color: #00b4d8; text-decoration: none; }
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
                    <div class="logo-sub">Natural Language Patient Search System</div>
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
        if st.button("Sign In", use_container_width=True):
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
