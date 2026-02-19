"""Campaign generation wizard with 2-phase audio pipeline."""

from __future__ import annotations

import asyncio
import sys
import uuid
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

st.title("Generate Campaign")

# ── Reference data ──

COUNTRIES = [
    "India", "Nigeria", "Kenya", "Tanzania", "South Africa", "Ghana",
    "Cameroon", "Senegal", "Congo (DRC)", "Ethiopia", "Mozambique",
    "Rwanda", "Uganda", "Zambia", "Zimbabwe", "Botswana", "Bangladesh",
    "Pakistan", "Indonesia", "Philippines", "Somalia",
]

TELCOS: dict[str, list[str]] = {
    "India": ["Jio", "Airtel India", "Vi (Vodafone Idea)", "BSNL"],
    "Nigeria": ["MTN Nigeria", "Airtel Nigeria", "Glo", "9mobile"],
    "Kenya": ["Safaricom", "Airtel Kenya", "Telkom Kenya"],
    "Tanzania": ["Vodacom Tanzania", "Airtel Tanzania", "Tigo", "Halotel"],
    "South Africa": ["Vodacom", "MTN SA", "Cell C", "Telkom SA"],
    "Ghana": ["MTN Ghana", "Vodafone Ghana", "AirtelTigo"],
    "Cameroon": ["MTN Cameroon", "Orange Cameroon", "Nexttel"],
    "Senegal": ["Orange Senegal", "Free Senegal", "Expresso"],
    "Congo (DRC)": ["Vodacom DRC", "Airtel DRC", "Orange DRC"],
    "Ethiopia": ["Ethio Telecom", "Safaricom Ethiopia"],
    "Mozambique": ["Vodacom Mozambique", "Movitel", "Tmcel"],
    "Rwanda": ["MTN Rwanda", "Airtel Rwanda"],
    "Uganda": ["MTN Uganda", "Airtel Uganda", "Africell Uganda"],
    "Zambia": ["MTN Zambia", "Airtel Zambia", "Zamtel"],
    "Zimbabwe": ["Econet", "NetOne", "Telecel"],
    "Botswana": ["Mascom", "Orange Botswana", "beMobile"],
    "Bangladesh": ["Grameenphone", "Robi", "Banglalink", "Teletalk"],
    "Pakistan": ["Jazz", "Telenor Pakistan", "Zong", "Ufone"],
    "Indonesia": ["Telkomsel", "Indosat", "XL Axiata", "Tri"],
    "Philippines": ["Globe", "Smart", "DITO"],
    "Somalia": ["Hormuud", "Somtel", "Golis"],
}

LANGUAGES: dict[str, list[str]] = {
    "India": ["Hindi", "Hinglish", "Tamil", "Telugu", "Bengali", "Kannada", "Malayalam", "English"],
    "Nigeria": ["English", "Pidgin English", "Hausa", "Yoruba", "Igbo"],
    "Kenya": ["English", "Swahili"],
    "Tanzania": ["Swahili", "English"],
    "South Africa": ["English", "Zulu", "Afrikaans", "Xhosa"],
    "Ghana": ["English", "Twi", "Pidgin English"],
    "Cameroon": ["French", "English", "Pidgin English"],
    "Senegal": ["French", "Wolof"],
    "Congo (DRC)": ["French", "Lingala", "Swahili"],
    "Ethiopia": ["Amharic", "Oromo", "English"],
    "Mozambique": ["Portuguese"],
    "Rwanda": ["Kinyarwanda", "English", "French"],
    "Uganda": ["English", "Luganda", "Swahili"],
    "Zambia": ["English", "Bemba", "Nyanja"],
    "Zimbabwe": ["English", "Shona", "Ndebele"],
    "Botswana": ["English", "Setswana"],
    "Bangladesh": ["Bengali", "English"],
    "Pakistan": ["Urdu", "English", "Punjabi"],
    "Indonesia": ["Indonesian", "English"],
    "Philippines": ["Filipino", "English", "Tagalog"],
    "Somalia": ["Somali", "Arabic", "English"],
}

PROMOTION_TYPES = {
    "obd_standard": {
        "name": "OBD Campaign",
        "description": "Standard outbound dialer with IVR and DTMF",
        "guidance": "Standard OBD promotional call. Hook (5s) + Body (15-18s) + CTA with DTMF (5-7s). Total under 30 seconds.",
    },
    "sms_followup": {
        "name": "SMS + OBD Combo",
        "description": "OBD script paired with follow-up SMS text",
        "guidance": "Combined OBD + SMS campaign. Generate both a 30-second OBD script and a follow-up SMS (160 chars max).",
    },
}


def _run_async(coro):
    """Run an async coroutine from synchronous Streamlit context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        pass
    return asyncio.run(coro)


# ── Input Form ──

with st.form("campaign_form"):
    st.subheader("Campaign Configuration")

    product_text = st.text_area(
        "Product / Service Description",
        height=150,
        placeholder="Paste your product documentation, feature list, or marketing brief here...",
    )

    uploaded_file = st.file_uploader(
        "Or upload a document (PDF, DOCX, TXT, PPTX)",
        type=["pdf", "docx", "txt", "pptx"],
    )

    col1, col2 = st.columns(2)
    with col1:
        country = st.selectbox("Target Country", COUNTRIES, index=0)
    with col2:
        telco_options = TELCOS.get(country, ["Other"])
        telco = st.selectbox("Telco Operator", telco_options)

    col3, col4 = st.columns(2)
    with col3:
        lang_options = LANGUAGES.get(country, ["English"])
        language = st.selectbox("Language", lang_options)
    with col4:
        promo_keys = list(PROMOTION_TYPES.keys())
        promo_labels = [PROMOTION_TYPES[k]["name"] for k in promo_keys]
        promo_idx = st.selectbox("Promotion Type", range(len(promo_keys)), format_func=lambda i: promo_labels[i])
        promo_type = promo_keys[promo_idx]

    tts_engine = st.radio(
        "TTS Engine",
        ["auto", "murf", "elevenlabs", "edge-tts"],
        horizontal=True,
        help="Auto selects the best available engine based on API keys configured.",
    )

    submitted = st.form_submit_button("Generate Scripts & Hook Previews", use_container_width=True, type="primary")


# ── File upload text extraction ──

def _extract_text_from_file(uploaded) -> str:
    """Extract text from uploaded file."""
    suffix = Path(uploaded.name).suffix.lower()
    content = uploaded.read()

    if suffix == ".txt":
        return content.decode("utf-8", errors="replace")
    elif suffix == ".pdf":
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=content, filetype="pdf")
            return "\n".join(page.get_text() for page in doc)
        except ImportError:
            st.warning("PyMuPDF not installed. Please paste text manually.")
            return ""
    elif suffix == ".docx":
        try:
            import docx
            import io
            doc = docx.Document(io.BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            st.warning("python-docx not installed. Please paste text manually.")
            return ""
    return ""


# ── Pipeline Execution ──

if submitted:
    final_text = product_text
    if uploaded_file and not final_text.strip():
        final_text = _extract_text_from_file(uploaded_file)

    if not final_text.strip():
        st.error("Please provide product text or upload a document.")
        st.stop()

    engine_choice = tts_engine if tts_engine != "auto" else None

    with st.status("Running AI pipeline...", expanded=True) as status:
        from backend.orchestrator import PipelineOrchestrator

        progress_messages: list[str] = []

        async def _progress_cb(agent: str, state: str, data: dict):
            msg = data.get("message", "")
            if msg:
                progress_messages.append(f"**{agent}**: {msg}")

        orchestrator = PipelineOrchestrator(on_progress=_progress_cb)

        async def _run_pipeline():
            return await orchestrator.run(
                product_text=final_text,
                country=country,
                telco=telco,
                language=language,
                tts_engine=engine_choice,
            )

        result = _run_async(_run_pipeline())

        for msg in progress_messages:
            st.write(msg)

        if "error" in result:
            status.update(label="Pipeline failed", state="error")
            st.error(result["error"])
            st.stop()

        status.update(label="Pipeline complete!", state="complete")

    st.session_state["pipeline_result"] = result
    st.session_state["tts_engine_choice"] = engine_choice
    st.session_state["campaign_meta"] = {
        "country": country, "telco": telco, "language": language,
    }


# ── Display Results ──

if "pipeline_result" not in st.session_state:
    st.info("Configure your campaign above and click **Generate** to start.")
    st.stop()

result = st.session_state["pipeline_result"]
engine_choice = st.session_state.get("tts_engine_choice")
meta = st.session_state.get("campaign_meta", {})

# Scripts
st.divider()
st.subheader("Generated Scripts")

final_scripts = result.get("final_scripts", {})
script_list = final_scripts.get("scripts", [])

if not script_list:
    st.warning("No scripts were generated.")
    st.stop()

# Editable scripts
if "edited_scripts" not in st.session_state:
    st.session_state["edited_scripts"] = {}

tabs = st.tabs([f"Variant {s.get('variant_id', i+1)}: {s.get('theme', '')}" for i, s in enumerate(script_list)])

for tab, script in zip(tabs, script_list):
    vid = script.get("variant_id", 0)
    with tab:
        for section in ["hook", "body", "cta", "full_script", "fallback_1", "fallback_2", "polite_closure"]:
            text = script.get(section, "")
            if text:
                key = f"script_{vid}_{section}"
                edited = st.text_area(
                    section.replace("_", " ").title(),
                    value=st.session_state["edited_scripts"].get(key, text),
                    key=key,
                    height=80 if section != "full_script" else 120,
                )
                st.session_state["edited_scripts"][key] = edited

# Hook Previews
st.divider()
st.subheader("Hook Voice Previews")
st.caption("Listen to each voice and select your preferred one per variant.")

hook_previews = result.get("hook_previews", {})
preview_files = hook_previews.get("audio_files", [])
voice_pool_info = hook_previews.get("voice_pool", [])
session_id = result.get("session_id", "")

if not preview_files:
    st.warning("No hook previews were generated. You can still generate full audio with default voices.")

# Voice selection per variant
if "voice_choices" not in st.session_state:
    st.session_state["voice_choices"] = {}

variant_ids = sorted(set(s.get("variant_id", 0) for s in script_list))

for vid in variant_ids:
    st.markdown(f"#### Variant {vid}")
    variant_previews = [f for f in preview_files if f.get("variant_id") == vid]

    if not variant_previews:
        st.session_state["voice_choices"][vid] = 1
        continue

    cols = st.columns(min(3, len(variant_previews)))
    for i, preview in enumerate(variant_previews):
        voice_idx = preview.get("voice_index", i + 1)
        label = preview.get("voice_label", f"Voice {voice_idx}")
        file_path = preview.get("file_path", "")

        with cols[i % 3]:
            st.markdown(f"**{label}**")
            if file_path and Path(file_path).exists():
                audio_bytes = Path(file_path).read_bytes()
                st.audio(audio_bytes, format="audio/mp3")
            else:
                st.caption("Audio not available")

    voice_labels = [f"Voice {p.get('voice_index', i+1)}: {p.get('voice_label', '')}" for i, p in enumerate(variant_previews)]
    voice_indices = [p.get("voice_index", i + 1) for i, p in enumerate(variant_previews)]

    if voice_labels:
        chosen_idx = st.radio(
            f"Select voice for Variant {vid}",
            range(len(voice_labels)),
            format_func=lambda i, vl=voice_labels: vl[i],
            key=f"voice_radio_{vid}",
            horizontal=True,
        )
        st.session_state["voice_choices"][vid] = voice_indices[chosen_idx]
    else:
        st.session_state["voice_choices"][vid] = 1


# ── Phase 2: Full Audio Generation ──

st.divider()
st.subheader("Generate Final Audio")

voice_summary = ", ".join(
    f"V{vid}=Voice {st.session_state['voice_choices'].get(vid, 1)}"
    for vid in variant_ids
)
st.caption(f"Selected voices: {voice_summary}")

if st.button("Generate Full Audio with Selected Voices", type="primary", use_container_width=True):
    # Apply edits to scripts
    edited_scripts = dict(final_scripts)
    edited_list = []
    for script in script_list:
        vid = script.get("variant_id", 0)
        new_script = dict(script)
        for section in ["hook", "body", "cta", "full_script", "fallback_1", "fallback_2", "polite_closure"]:
            key = f"script_{vid}_{section}"
            if key in st.session_state["edited_scripts"]:
                new_script[section] = st.session_state["edited_scripts"][key]
        edited_list.append(new_script)
    edited_scripts["scripts"] = edited_list

    voice_choices = {vid: st.session_state["voice_choices"].get(vid, 1) for vid in variant_ids}

    with st.status("Generating final audio...", expanded=True) as status:
        from backend.orchestrator import PipelineOrchestrator

        progress_msgs: list[str] = []

        async def _progress_cb2(agent: str, state: str, data: dict):
            msg = data.get("message", "")
            if msg:
                progress_msgs.append(f"**{agent}**: {msg}")

        orchestrator = PipelineOrchestrator(on_progress=_progress_cb2)
        voice_selection = result.get("voice_selection", {})

        async def _run_final():
            return await orchestrator.run_full_audio(
                scripts=edited_scripts,
                voice_selection=voice_selection,
                voice_choices=voice_choices,
                session_id=session_id,
                country=meta.get("country", ""),
                language=meta.get("language"),
                tts_engine=engine_choice,
            )

        audio_result = _run_async(_run_final())

        for msg in progress_msgs:
            st.write(msg)

        if "error" in audio_result:
            status.update(label="Audio generation failed", state="error")
            st.error(audio_result["error"])
        else:
            status.update(label="Audio generation complete!", state="complete")
            st.session_state["final_audio"] = audio_result

# ── Display Final Audio ──

if "final_audio" in st.session_state:
    st.divider()
    st.subheader("Final Audio Files")

    audio_result = st.session_state["final_audio"]
    audio_files = audio_result.get("audio_files", [])
    tts_used = audio_result.get("tts_engine", "unknown")

    st.caption(f"TTS Engine: **{tts_used}** | Files: **{len(audio_files)}**")

    for vid in variant_ids:
        variant_files = [f for f in audio_files if f.get("variant_id") == vid]
        if not variant_files:
            continue

        with st.expander(f"Variant {vid}", expanded=True):
            for af in variant_files:
                file_path = af.get("file_path", "")
                file_name = af.get("file_name", "")
                audio_type = af.get("type", "")
                size_kb = af.get("file_size_bytes", 0) / 1024

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{audio_type}** -- {file_name} ({size_kb:.0f} KB)")
                    if file_path and Path(file_path).exists():
                        st.audio(Path(file_path).read_bytes(), format="audio/mp3")
                with col2:
                    if file_path and Path(file_path).exists():
                        st.download_button(
                            "Download",
                            data=Path(file_path).read_bytes(),
                            file_name=file_name,
                            mime="audio/mpeg",
                            key=f"dl_{file_name}",
                        )
