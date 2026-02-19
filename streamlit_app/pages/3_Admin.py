"""Admin panel -- manage users (admin role only)."""

from __future__ import annotations

import time

import streamlit as st
from components.auth import (
    require_auth,
    create_user,
    list_users,
    toggle_user_active,
    delete_user,
    reset_password,
)

user = require_auth()
if not user:
    st.warning("Please sign in first.")
    st.stop()

if user.get("role") != "admin":
    st.error("Access denied. Admin privileges required.")
    st.stop()

st.title("User Management")

# ── Create User ──

st.subheader("Create New User")

with st.form("create_user_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        new_username = st.text_input("Username", placeholder="e.g. john_doe")
    with col2:
        new_password = st.text_input("Password", type="password", placeholder="Min 6 characters")
    with col3:
        new_role = st.selectbox("Role", ["user", "admin"])

    create_submitted = st.form_submit_button("Create User", use_container_width=True)

if create_submitted:
    if not new_username or not new_password:
        st.error("Username and password are required.")
    elif len(new_password) < 6:
        st.error("Password must be at least 6 characters.")
    else:
        ok = create_user(new_username, new_password, new_role, created_by=user["username"])
        if ok:
            st.success(f"User **{new_username}** created with role **{new_role}**.")
            st.rerun()
        else:
            st.error(f"Username **{new_username}** already exists.")

# ── User List ──

st.divider()
st.subheader("Existing Users")

users = list_users()

if not users:
    st.info("No users found.")
    st.stop()

for u in users:
    uid = u["id"]
    uname = u["username"]
    role = u["role"]
    active = u["is_active"]
    created_by = u.get("created_by", "system")
    created_at = u.get("created_at", 0)

    status_badge = "Active" if active else "Disabled"
    status_color = "green" if active else "red"

    with st.container():
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

        with col1:
            st.markdown(f"**{uname}** :{status_color}[{status_badge}]")
            st.caption(f"Role: {role} | Created by: {created_by}")

        with col2:
            if active:
                if st.button("Disable", key=f"disable_{uid}", type="secondary"):
                    toggle_user_active(uid, False)
                    st.rerun()
            else:
                if st.button("Enable", key=f"enable_{uid}"):
                    toggle_user_active(uid, True)
                    st.rerun()

        with col3:
            new_pw = st.text_input("New PW", key=f"pw_{uid}", type="password", label_visibility="collapsed", placeholder="New password")

        with col4:
            if st.button("Reset PW", key=f"reset_{uid}"):
                if new_pw and len(new_pw) >= 6:
                    reset_password(uid, new_pw)
                    st.success(f"Password reset for {uname}.")
                else:
                    st.warning("Enter a password (min 6 chars) first.")

        with col5:
            if uname != user["username"]:
                if st.button("Delete", key=f"del_{uid}", type="secondary"):
                    delete_user(uid)
                    st.rerun()
            else:
                st.caption("(you)")

        st.divider()
