"""OBD SuperStar Agent -- Streamlit App."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path so `backend.*` imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from components.auth import init_auth_db, require_auth, show_login_form

st.set_page_config(
    page_title="OBD SuperStar Agent",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_auth_db()

user = require_auth()

if not user:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        show_login_form()
    st.stop()

# Sidebar
with st.sidebar:
    st.markdown(f"### OBD SuperStar Agent")
    st.caption(f"Signed in as **{user['username']}** ({user['role']})")
    st.divider()
    if st.button("Sign Out", use_container_width=True):
        del st.session_state["user"]
        st.rerun()

st.markdown(
    """
    ## Welcome to OBD SuperStar Agent

    Generate professional outbound dialer scripts and broadcast-quality audio
    with AI-powered multi-agent pipeline.

    **Use the sidebar to navigate:**
    - **Generate** -- Create new campaign scripts & audio
    - **Dashboard** -- View saved campaigns
    """
    + ("- **Admin** -- Manage users\n" if user["role"] == "admin" else "")
)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Your Role", user["role"].title())
