"""Shared UI theme: CSS injection and small HTML component helpers.

Keeping the presentation layer in one module means app.py and auth.py stay
readable and the look of the dashboard can be adjusted in a single place.
"""

import streamlit as st

# Severity -> (text color, soft background, accent/border) used across the UI.
SEVERITY_COLORS = {
    "CRITICAL": ("#b42318", "#fef3f2", "#f04438"),
    "WARNING": ("#b54708", "#fffaeb", "#f79009"),
    "NORMAL": ("#067647", "#ecfdf3", "#17b26a"),
}

STATUS_COLORS = {
    "OPEN": ("#b42318", "#fef3f2"),
    "ACKNOWLEDGED": ("#b54708", "#fffaeb"),
    "RESOLVED": ("#067647", "#ecfdf3"),
}

ROLE_ICONS = {
    "Resident": "🏠",
    "Caregiver": "🧑‍⚕️",
    "Responder": "🚑",
    "Admin": "🛠️",
}


def inject_css():
    """Apply the global look and feel. Safe to call on every rerun."""
    st.markdown(
        """
        <style>
        :root {
            --ps-bg: #f6f8fb;
            --ps-card: #ffffff;
            --ps-border: #e4e7ec;
            --ps-text: #101828;
            --ps-muted: #667085;
            --ps-primary: #3538cd;
            --ps-primary-soft: #eef0ff;
        }

        /* Page background + base typography */
        .stApp { background: var(--ps-bg); }
        html, body, [class*="css"] { color: var(--ps-text); }

        /* Tighten the top padding Streamlit leaves by default */
        .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1180px; }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: #0f1a2b;
        }
        section[data-testid="stSidebar"] * { color: #e7ecf3; }
        section[data-testid="stSidebar"] .stRadio label { color: #c5cedb !important; }

        /* Metric cards */
        div[data-testid="stMetric"] {
            background: var(--ps-card);
            border: 1px solid var(--ps-border);
            border-radius: 14px;
            padding: 16px 18px;
            box-shadow: 0 1px 2px rgba(16,24,40,.05);
        }
        div[data-testid="stMetric"] label { color: var(--ps-muted) !important; font-weight: 600; }
        div[data-testid="stMetricValue"] { font-size: 1.6rem; }

        /* Primary buttons */
        .stButton > button[kind="primary"] {
            background: var(--ps-primary);
            border: none;
            border-radius: 10px;
            font-weight: 600;
            padding: .55rem 1rem;
        }
        .stButton > button[kind="primary"]:hover { background: #2d2fb3; }
        .stButton > button { border-radius: 10px; font-weight: 600; }

        /* Dataframes */
        div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }

        /* Generic card helper */
        .ps-card {
            background: var(--ps-card);
            border: 1px solid var(--ps-border);
            border-radius: 14px;
            padding: 18px 20px;
            box-shadow: 0 1px 2px rgba(16,24,40,.05);
            margin-bottom: 14px;
        }

        /* App header band */
        .ps-header {
            background: linear-gradient(135deg, #3538cd 0%, #5b5ef0 100%);
            border-radius: 18px;
            padding: 22px 26px;
            color: #ffffff;
            margin-bottom: 18px;
        }
        .ps-header h1 { color: #fff; font-size: 1.7rem; margin: 0 0 4px 0; }
        .ps-header p { color: #dfe1ff; margin: 0; font-size: .95rem; }

        /* Status banner (severity aware) */
        .ps-banner {
            border-radius: 16px;
            padding: 20px 24px;
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            gap: 18px;
        }
        .ps-banner .dot {
            width: 14px; height: 14px; border-radius: 50%;
            box-shadow: 0 0 0 5px rgba(0,0,0,.06);
        }
        .ps-banner .txt small { display:block; font-weight:600; letter-spacing:.04em; text-transform:uppercase; opacity:.8; font-size:.72rem; }
        .ps-banner .txt strong { font-size: 1.25rem; }

        /* Pills / badges */
        .ps-pill {
            display: inline-block;
            padding: 3px 12px;
            border-radius: 999px;
            font-size: .74rem;
            font-weight: 700;
            letter-spacing: .03em;
        }

        /* Sidebar user card */
        .ps-user {
            background: rgba(255,255,255,.06);
            border: 1px solid rgba(255,255,255,.12);
            border-radius: 12px;
            padding: 12px 14px;
            margin-bottom: 10px;
        }
        .ps-user .name { font-weight: 700; font-size: .98rem; }
        .ps-user .role { font-size: .8rem; opacity: .8; }

        /* Notification card */
        .ps-note {
            background: var(--ps-card);
            border: 1px solid var(--ps-border);
            border-left: 4px solid var(--ps-primary);
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 10px;
        }
        .ps-note .meta { color: var(--ps-muted); font-size: .78rem; margin-bottom: 4px; }
        .ps-note .msg { font-size: .95rem; }
        .ps-note .foot { color: var(--ps-muted); font-size: .74rem; margin-top: 6px; }

        /* Section label */
        .ps-section { font-size: 1.1rem; font-weight: 700; margin: 6px 0 2px 0; }
        .ps-sub { color: var(--ps-muted); font-size: .85rem; margin-bottom: 10px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def app_header(title: str, subtitle: str):
    st.markdown(
        f'<div class="ps-header"><h1>🛡️ {title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def status_banner(severity: str, event: str, timestamp: str | None = None):
    text, bg, accent = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["NORMAL"])
    label = {
        "CRITICAL": "Attention needed",
        "WARNING": "Caution",
        "NORMAL": "All clear",
    }.get(severity, "Status")
    ts = f'<span style="margin-left:auto;color:{text};opacity:.7;font-size:.8rem">{timestamp}</span>' if timestamp else ""
    st.markdown(
        f"""
        <div class="ps-banner" style="background:{bg};border:1px solid {accent}33;">
            <div class="dot" style="background:{accent}"></div>
            <div class="txt" style="color:{text}">
                <small>{label} · {severity}</small>
                <strong>{event}</strong>
            </div>
            {ts}
        </div>
        """,
        unsafe_allow_html=True,
    )


def severity_pill(severity: str) -> str:
    text, bg, _ = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["NORMAL"])
    return f'<span class="ps-pill" style="color:{text};background:{bg}">{severity}</span>'


def status_pill(status: str) -> str:
    text, bg = STATUS_COLORS.get(status, ("#344054", "#f2f4f7"))
    return f'<span class="ps-pill" style="color:{text};background:{bg}">{status}</span>'


def section(title: str, subtitle: str | None = None):
    st.markdown(f'<div class="ps-section">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="ps-sub">{subtitle}</div>', unsafe_allow_html=True)
