import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from backend.database import (
    initialize_database, get_current_state, get_readings,
    get_authorized_incidents, get_notifications_for_user,
    update_incident_status, get_users, set_responder_permission
)
from backend.sensor_simulator import SCENARIOS
from backend.service import process_scenario
from dashboard.auth import require_login

st.set_page_config(page_title="PrivaSense X", page_icon="🛡️", layout="wide")
initialize_database()
require_login()
user = st.session_state["user"]

st.sidebar.title("🛡️ PrivaSense X")
st.sidebar.caption(f"Signed in: {user['display_name']}")
st.sidebar.caption(f"Role: {user['role']}")
page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Live Monitoring", "Incident History", "Personalized Alerts", "Users & Permissions"]
)
if st.sidebar.button("Sign out", use_container_width=True):
    del st.session_state["user"]
    st.rerun()

st.title("PrivaSense X")
st.caption("Privacy-first, role-aware assistive event intelligence")
st.warning(
    "Prototype notice: sensor values are simulated. This application is for demonstration, "
    "not a certified safety-monitoring or emergency-dispatch system."
)

def severity_badge(severity):
    if severity == "CRITICAL":
        st.error("CRITICAL")
    elif severity == "WARNING":
        st.warning("WARNING")
    else:
        st.success("NORMAL")

def visible_incidents():
    return get_authorized_incidents(user)

if page == "Overview":
    st.subheader("System overview")
    state = get_current_state()
    if state:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Temperature", f"{state['temperature_c']:.1f} °C")
        c2.metric("Gas sensor raw value", state["gas_raw"])
        c3.metric("Motion", "Detected" if state["motion"] else "Not detected")
        c4.metric("System status", state["severity"])
        st.caption(f"Last updated: {state['timestamp']}")
        st.write("Latest event:", state["event"])
    else:
        st.info("No sensor readings yet. Open Live Monitoring and run a simulation.")

    records = visible_incidents()
    st.subheader("Recent incidents visible to your role")
    if records:
        st.dataframe(pd.DataFrame(records).head(8), use_container_width=True, hide_index=True)
    else:
        st.info("No incidents are currently visible to this account.")

elif page == "Live Monitoring":
    st.subheader("Sensor simulation")
    st.write("Choose a test scenario to simulate the three inputs from your Tinkercad circuit.")
    scenario = st.selectbox("Simulation scenario", list(SCENARIOS.keys()))
    if st.button("▶ Run sensor simulation", type="primary"):
        output = process_scenario(scenario)
        st.session_state["last_output"] = output
        st.success("Sensor values processed and current state saved.")
        st.json({
            "sensor_data": output["sensor_data"],
            "event_result": output["result"],
            "incident_id": output["incident_id"],
            "notification_count": len(output["notifications"]),
        })

    state = get_current_state()
    if state:
        st.subheader("Current sensor state")
        a, b, c, d = st.columns(4)
        a.metric("Temperature", f"{state['temperature_c']:.1f} °C")
        b.metric("Gas raw value", state["gas_raw"])
        c.metric("Motion", "Yes" if state["motion"] else "No")
        d.metric("Severity", state["severity"])

    readings = get_readings()
    if readings:
        df = pd.DataFrame(readings)
        st.subheader("Sensor readings over time")
        st.line_chart(df.set_index("timestamp")[["temperature_c", "gas_raw"]])
        st.dataframe(df.tail(15), use_container_width=True, hide_index=True)

elif page == "Incident History":
    st.subheader("Incident history")
    records = visible_incidents()
    if not records:
        st.info("No incident history is available to this role.")
    else:
        df = pd.DataFrame(records)
        severities = ["All"] + sorted(df["severity"].dropna().unique().tolist())
        selected = st.selectbox("Filter by severity", severities)
        if selected != "All":
            df = df[df["severity"] == selected]
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Only assigned care roles and admin can update incident status in this demo.
        if user["role"] in ("Caregiver", "Admin"):
            st.subheader("Acknowledge or resolve an incident")
            open_items = [r for r in records if r["status"] != "RESOLVED"]
            if open_items:
                options = {
                    f"#{r['id']} — {r['event']} ({r['status']})": r["id"]
                    for r in open_items
                }
                chosen_label = st.selectbox("Select incident", list(options))
                x, y = st.columns(2)
                if x.button("Acknowledge"):
                    update_incident_status(options[chosen_label], "ACKNOWLEDGED", user["username"])
                    st.success("Incident acknowledged.")
                    st.rerun()
                if y.button("Resolve"):
                    update_incident_status(options[chosen_label], "RESOLVED", user["username"])
                    st.success("Incident marked resolved.")
                    st.rerun()
            else:
                st.caption("No unresolved incidents.")

elif page == "Personalized Alerts":
    st.subheader("Notifications for your account")
    notifications = get_notifications_for_user(user)
    if notifications:
        for item in notifications:
            with st.container(border=True):
                st.caption(f"{item['timestamp']} · {item['recipient_role']} · {item['delivery_status']}")
                st.write(item["message"])
                st.caption(f"Incident ID: {item['incident_id']} · Channel: {item['channel']}")
    else:
        st.info("No notifications have been generated for this account.")

    st.caption("Notifications are stored in the dashboard database. Telegram delivery is not enabled in this version.")

elif page == "Users & Permissions":
    st.subheader("Users and permissions")
    if user["role"] != "Admin":
        st.info("Only the Admin demo account can manage permission settings.")
    else:
        st.write("Demo users")
        users = get_users()
        st.dataframe(pd.DataFrame(users), use_container_width=True, hide_index=True)
        responders = [u for u in users if u["role"] == "Responder"]
        if responders:
            st.subheader("Responder access control")
            responder = st.selectbox("Responder account", [u["username"] for u in responders])
            current = next(u for u in responders if u["username"] == responder)
            allowed = st.checkbox(
                "Allow this responder to view critical incident details",
                value=bool(current["responder_authorized"])
            )
            if st.button("Save responder permission"):
                set_responder_permission(responder, allowed)
                st.success("Permission updated. Sign out and sign in again for the responder account to refresh its session.")
        st.caption("This is a student demonstration of role-based access. It is not a production identity-management system.")
