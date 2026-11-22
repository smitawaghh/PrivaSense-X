import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backend.config import TEMP_WARNING_C, TEMP_CRITICAL_C, GAS_CRITICAL_RAW
from backend.database import (
    initialize_database, get_current_state, get_readings,
    get_authorized_incidents, get_notifications_for_user,
    update_incident_status, get_users, set_responder_permission
)
from backend.sensor_simulator import SCENARIOS
from backend.service import process_scenario
from dashboard.auth import require_login
from dashboard.theme import (
    inject_css, app_header, status_banner, severity_pill, status_pill,
    section, ROLE_ICONS, SEVERITY_COLORS,
)

st.set_page_config(page_title="PrivaSense X", page_icon="🛡️", layout="wide")
initialize_database()
inject_css()
require_login()
user = st.session_state["user"]

PAGES = {
    "Overview": "📊",
    "Live Monitoring": "📡",
    "Incident History": "🗂️",
    "Personalized Alerts": "🔔",
    "Users & Permissions": "👥",
}


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown("### 🛡️ PrivaSense X")
    role_icon = ROLE_ICONS.get(user["role"], "👤")
    st.markdown(
        f"""
        <div class="ps-user">
            <div class="name">{role_icon} {user['display_name']}</div>
            <div class="role">Signed in as {user['role']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Admins can manage people; everyone else gets a trimmed menu.
    available = list(PAGES.keys())
    if user["role"] != "Admin":
        available = [p for p in available if p != "Users & Permissions"]

    page = st.radio(
        "Navigation",
        available,
        format_func=lambda p: f"{PAGES[p]}  {p}",
        label_visibility="collapsed",
    )

    st.divider()
    if st.button("Sign out", use_container_width=True):
        del st.session_state["user"]
        st.rerun()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def visible_incidents():
    return get_authorized_incidents(user)


def incidents_table(records):
    """Render incidents as a tidy, labelled dataframe with icons."""
    df = pd.DataFrame(records)
    if df.empty:
        return df
    view = pd.DataFrame({
        "ID": df["id"],
        "Time": df["timestamp"],
        "Event": df["event"],
        "Severity": df["severity"],
        "Temp (°C)": df["temperature_c"].round(1),
        "Gas": df["gas_raw"],
        "Motion": df["motion"].map({1: "Yes", 0: "No"}),
        "Status": df["status"],
    })
    return view


def readings_chart(df: pd.DataFrame):
    """Line chart for temperature + gas with threshold reference lines."""
    df = df.copy()
    df["t"] = pd.to_datetime(df["timestamp"], errors="coerce")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["t"], y=df["temperature_c"], name="Temperature (°C)",
        mode="lines+markers", line=dict(color="#3538cd", width=2.5),
        yaxis="y1",
    ))
    fig.add_trace(go.Scatter(
        x=df["t"], y=df["gas_raw"], name="Gas (raw)",
        mode="lines+markers", line=dict(color="#f79009", width=2.5),
        yaxis="y2",
    ))
    # Threshold guides on the temperature axis.
    fig.add_hline(y=TEMP_WARNING_C, line=dict(color="#f79009", width=1, dash="dot"),
                  annotation_text="Temp warning", annotation_position="top left")
    fig.add_hline(y=TEMP_CRITICAL_C, line=dict(color="#f04438", width=1, dash="dot"),
                  annotation_text="Temp critical", annotation_position="top left")

    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        yaxis=dict(title="Temperature (°C)", gridcolor="#eef0f3"),
        yaxis2=dict(title="Gas (raw)", overlaying="y", side="right", showgrid=False),
        xaxis=dict(title=None, gridcolor="#eef0f3"),
    )
    return fig


# --------------------------------------------------------------------------- #
# Header + prototype notice
# --------------------------------------------------------------------------- #
app_header("PrivaSense X", "Privacy-first, role-aware assistive event intelligence")
st.caption(
    "⚠️ Prototype notice: sensor values are simulated. This application is for "
    "demonstration, not a certified safety-monitoring or emergency-dispatch system."
)


# --------------------------------------------------------------------------- #
# Overview
# --------------------------------------------------------------------------- #
if page == "Overview":
    state = get_current_state()
    if state:
        status_banner(state["severity"], state["event"], state.get("timestamp"))

        c1, c2, c3, c4 = st.columns(4)
        temp = state["temperature_c"]
        temp_delta = f"{temp - TEMP_WARNING_C:+.1f} vs warning"
        c1.metric("Temperature", f"{temp:.1f} °C", temp_delta,
                  delta_color="inverse")
        c2.metric("Gas sensor", state["gas_raw"],
                  f"{state['gas_raw'] - GAS_CRITICAL_RAW:+d} vs critical",
                  delta_color="inverse")
        c3.metric("Motion", "Detected" if state["motion"] else "Not detected")
        c4.metric("System status", state["severity"])
    else:
        st.info("No sensor readings yet. Open **Live Monitoring** and run a simulation to populate the dashboard.")

    st.write("")
    records = visible_incidents()
    section("Recent incidents", "Events visible to your role, most recent first.")
    if records:
        # Quick counts by severity.
        df_all = pd.DataFrame(records)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total", len(df_all))
        k2.metric("Critical", int((df_all["severity"] == "CRITICAL").sum()))
        k3.metric("Open", int((df_all["status"] == "OPEN").sum()))
        k4.metric("Resolved", int((df_all["status"] == "RESOLVED").sum()))
        st.dataframe(incidents_table(records).head(8), use_container_width=True, hide_index=True)
    else:
        st.info("No incidents are currently visible to this account.")


# --------------------------------------------------------------------------- #
# Live Monitoring
# --------------------------------------------------------------------------- #
elif page == "Live Monitoring":
    section("Sensor simulation", "Choose a test scenario to simulate the three inputs from your Tinkercad circuit.")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        scenario = st.selectbox("Simulation scenario", list(SCENARIOS.keys()))
        preset = SCENARIOS[scenario]
        st.caption(
            f"Preset values → Temperature: **{preset['temperature_c']} °C**, "
            f"Gas: **{preset['gas_raw']}**, Motion: **{'Yes' if preset['motion'] else 'No'}**"
        )
        run = st.button("▶ Run sensor simulation", type="primary")
    with col_b:
        st.markdown(
            f"""
            <div class="ps-card">
                <div class="ps-sub" style="margin:0 0 6px 0;">Active thresholds</div>
                <div>🌡️ Temp warning · <b>{TEMP_WARNING_C:.0f} °C</b></div>
                <div>🔥 Temp critical · <b>{TEMP_CRITICAL_C:.0f} °C</b></div>
                <div>💨 Gas critical · <b>{GAS_CRITICAL_RAW}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if run:
        output = process_scenario(scenario)
        st.session_state["last_output"] = output
        sev = output["result"]["severity"]
        if output["incident_id"] is None:
            st.success(
                f"Processed “{scenario}”. Severity: **{sev}** — no incident raised (conditions normal)."
            )
        else:
            st.success(
                f"Processed “{scenario}”. Severity: **{sev}** · "
                f"Incident #{output['incident_id']} · {len(output['notifications'])} notification(s) created."
            )

    st.write("")
    state = get_current_state()
    if state:
        status_banner(state["severity"], state["event"], state.get("timestamp"))
        a, b, c, d = st.columns(4)
        a.metric("Temperature", f"{state['temperature_c']:.1f} °C")
        b.metric("Gas raw value", state["gas_raw"])
        c.metric("Motion", "Yes" if state["motion"] else "No")
        d.metric("Severity", state["severity"])

    readings = get_readings()
    if readings:
        df = pd.DataFrame(readings)
        st.write("")
        section("Sensor readings over time")
        st.plotly_chart(readings_chart(df), use_container_width=True)

        with st.expander("Recent raw readings", expanded=False):
            recent = df.tail(15).iloc[::-1]
            view = pd.DataFrame({
                "Time": recent["timestamp"],
                "Temp (°C)": recent["temperature_c"].round(1),
                "Gas": recent["gas_raw"],
                "Motion": recent["motion"].map({1: "Yes", 0: "No"}),
                "Severity": recent["severity"],
            })
            st.dataframe(view, use_container_width=True, hide_index=True)
    else:
        st.info("Run a simulation above to start recording sensor readings.")


# --------------------------------------------------------------------------- #
# Incident History
# --------------------------------------------------------------------------- #
elif page == "Incident History":
    section("Incident history", "Full log of events recorded for your role.")
    records = visible_incidents()
    if not records:
        st.info("No incident history is available to this role.")
    else:
        df = pd.DataFrame(records)

        f1, f2 = st.columns(2)
        severities = ["All"] + sorted(df["severity"].dropna().unique().tolist())
        statuses = ["All"] + sorted(df["status"].dropna().unique().tolist())
        sel_sev = f1.selectbox("Filter by severity", severities)
        sel_status = f2.selectbox("Filter by status", statuses)

        filtered = records
        if sel_sev != "All":
            filtered = [r for r in filtered if r["severity"] == sel_sev]
        if sel_status != "All":
            filtered = [r for r in filtered if r["status"] == sel_status]

        st.caption(f"Showing **{len(filtered)}** of {len(records)} incidents.")
        if filtered:
            st.dataframe(incidents_table(filtered), use_container_width=True, hide_index=True)
        else:
            st.info("No incidents match the selected filters.")

        # Only assigned care roles and admin can update incident status in this demo.
        if user["role"] in ("Caregiver", "Admin"):
            st.write("")
            section("Acknowledge or resolve an incident")
            open_items = [r for r in records if r["status"] != "RESOLVED"]
            if open_items:
                options = {
                    f"#{r['id']} — {r['event']} ({r['status']})": r["id"]
                    for r in open_items
                }
                chosen_label = st.selectbox("Select incident", list(options))
                x, y = st.columns(2)
                if x.button("✓ Acknowledge", use_container_width=True):
                    update_incident_status(options[chosen_label], "ACKNOWLEDGED", user["username"])
                    st.success("Incident acknowledged.")
                    st.rerun()
                if y.button("✔ Resolve", type="primary", use_container_width=True):
                    update_incident_status(options[chosen_label], "RESOLVED", user["username"])
                    st.success("Incident marked resolved.")
                    st.rerun()
            else:
                st.caption("No unresolved incidents. 🎉")


# --------------------------------------------------------------------------- #
# Personalized Alerts
# --------------------------------------------------------------------------- #
elif page == "Personalized Alerts":
    section("Notifications for your account", "Alerts generated for your role, most recent first.")
    notifications = get_notifications_for_user(user)
    if notifications:
        for item in notifications:
            st.markdown(
                f"""
                <div class="ps-note">
                    <div class="meta">{item['timestamp']} · {item['recipient_role']} · {item['delivery_status']}</div>
                    <div class="msg">{item['message']}</div>
                    <div class="foot">Incident #{item['incident_id']} · Channel: {item['channel']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No notifications have been generated for this account.")

    st.caption("Notifications are stored in the dashboard database. Telegram delivery is not enabled in this version.")


# --------------------------------------------------------------------------- #
# Users & Permissions (Admin only; page is hidden otherwise)
# --------------------------------------------------------------------------- #
elif page == "Users & Permissions":
    section("Users and permissions", "Manage demo accounts and responder access.")
    if user["role"] != "Admin":
        st.info("Only the Admin demo account can manage permission settings.")
    else:
        users = get_users()
        udf = pd.DataFrame(users)
        view = pd.DataFrame({
            "User": udf["display_name"],
            "Username": udf["username"],
            "Role": udf["role"],
            "Responder access": udf["responder_authorized"].map({1: "✓ Allowed", 0: "— Not allowed"}),
            "Active": udf["active"].map({1: "Yes", 0: "No"}),
        })
        st.dataframe(view, use_container_width=True, hide_index=True)

        responders = [u for u in users if u["role"] == "Responder"]
        if responders:
            st.write("")
            section("Responder access control", "Control whether responders can view critical incident details.")
            responder = st.selectbox("Responder account", [u["username"] for u in responders])
            current = next(u for u in responders if u["username"] == responder)
            allowed = st.checkbox(
                "Allow this responder to view critical incident details",
                value=bool(current["responder_authorized"]),
            )
            if st.button("Save responder permission", type="primary"):
                set_responder_permission(responder, allowed)
                st.success("Permission updated. Sign out and sign in again for the responder account to refresh its session.")
        st.caption("This is a student demonstration of role-based access. It is not a production identity-management system.")
