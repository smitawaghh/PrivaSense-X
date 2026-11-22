"""Small local demo login helper. Not production-grade authentication."""

import streamlit as st

from backend.database import authenticate
from dashboard.theme import inject_css

# Credentials shown on the login screen so the classroom demo is easy to try.
DEMO_ACCOUNTS = [
    ("🏠 Resident", "resident", "Resident123!"),
    ("🧑‍⚕️ Caregiver", "caregiver", "Caregiver123!"),
    ("🚑 Responder", "responder", "Responder123!"),
    ("🛠️ Admin", "admin", "Admin123!"),
]


def login_screen():
    inject_css()

    # Center the login card in the middle third of the page.
    left, center, right = st.columns([1, 1.4, 1])
    with center:
        st.markdown(
            """
            <div class="ps-header" style="text-align:center;">
                <h1>🛡️ PrivaSense X</h1>
                <p>Privacy-first, role-aware assistive event intelligence</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown("#### Sign in")
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="e.g. caregiver")
                password = st.text_input("Password", type="password", placeholder="Your demo password")
                submitted = st.form_submit_button("Sign in", use_container_width=True, type="primary")

            if submitted:
                user = authenticate(username, password)
                if user:
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        with st.expander("Demo accounts", expanded=False):
            st.caption("Prototype credentials for classroom use. Change all passwords before any real deployment.")
            for label, uname, pwd in DEMO_ACCOUNTS:
                a, b, c = st.columns([1.2, 1, 1.2])
                a.markdown(f"**{label}**")
                b.code(uname, language=None)
                c.code(pwd, language=None)

        st.caption(
            "Prototype notice: sensor values are simulated. This is a demonstration, "
            "not a certified safety-monitoring or emergency-dispatch system."
        )


def require_login():
    if "user" not in st.session_state:
        login_screen()
        st.stop()
