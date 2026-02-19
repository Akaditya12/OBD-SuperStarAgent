"""Dashboard -- view saved campaigns and their scripts/audio."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from components.auth import require_auth

user = require_auth()
if not user:
    st.warning("Please sign in first.")
    st.stop()

st.title("Campaign Dashboard")

from backend.database import init_db, list_campaigns, get_campaign, delete_campaign

init_db()
campaigns = list_campaigns()

if not campaigns:
    st.info("No campaigns saved yet. Generate one from the **Generate** page and save it.")
    st.stop()

st.caption(f"**{len(campaigns)}** campaigns saved")

# Search
search = st.text_input("Search campaigns", placeholder="Filter by name, country, telco...")

filtered = campaigns
if search:
    q = search.lower()
    filtered = [
        c for c in campaigns
        if q in c.get("name", "").lower()
        or q in c.get("country", "").lower()
        or q in c.get("telco", "").lower()
        or q in c.get("language", "").lower()
    ]

for campaign in filtered:
    cid = campaign["id"]
    name = campaign.get("name", "Untitled")
    created = campaign.get("created_at", "")
    country = campaign.get("country", "")
    telco = campaign.get("telco", "")
    language = campaign.get("language", "")
    script_count = campaign.get("script_count", 0)
    has_audio = campaign.get("has_audio", False)

    with st.expander(f"{name}  --  {country} / {telco} ({language})", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Scripts", script_count)
        col2.metric("Audio", "Yes" if has_audio else "No")
        col3.metric("Language", language or "Default")
        col4.caption(f"Created: {created}")

        detail = get_campaign(cid)
        if detail:
            result = detail.get("result", {})
            final_scripts = result.get("final_scripts", {})
            script_list = final_scripts.get("scripts", [])

            if script_list:
                st.markdown("**Scripts:**")
                for script in script_list:
                    vid = script.get("variant_id", 0)
                    theme = script.get("theme", "")
                    full = script.get("full_script", "")
                    st.markdown(f"*Variant {vid} -- {theme}*")
                    st.text(full[:300] + ("..." if len(full) > 300 else ""))

            audio_data = result.get("audio", result.get("final_audio", {}))
            audio_files = audio_data.get("audio_files", [])
            if audio_files:
                st.markdown("**Audio Files:**")
                for af in audio_files:
                    fp = af.get("file_path", "")
                    fname = af.get("file_name", "")
                    atype = af.get("type", "")
                    if fp and Path(fp).exists():
                        st.markdown(f"_{atype}_ -- {fname}")
                        st.audio(Path(fp).read_bytes(), format="audio/mp3")

        if st.button(f"Delete", key=f"del_{cid}", type="secondary"):
            delete_campaign(cid)
            st.rerun()
