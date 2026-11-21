"""Small local demo login helper. Not production-grade authentication."""

import streamlit as st
from backend.database import authenticate

def login_screen():
    st.title("PrivaSense X")
    st.subheader("Privacy-first assistive event intelligence")
    st.info("Prototype demo accounts are provided in README.md. Change all demo passwords before any real deployment.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        user = authenticate(username, password)
        if user:
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("Invalid username or password.")

def require_login():
    if "user" not in st.session_state:
        login_screen()
        st.stop()
