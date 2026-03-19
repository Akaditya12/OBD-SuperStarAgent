#!/usr/bin/env python3
"""Seed flow_configs table with example flows (e.g. BTC Christianity 3-step). Requires Supabase env and flow_configs table."""

import os
import sys

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Set SUPABASE_URL and SUPABASE_SERVICE_KEY (e.g. in .env). Exiting.")
    sys.exit(1)

try:
    from supabase import create_client
except ImportError:
    print("Run: pip install supabase")
    sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

BTC_CHRISTIANITY_STEPS = [
    {"id": "welcome", "purpose": "Welcome with verse; pitch Bible portal; Press 1 to activate", "max_words": 40},
    {"id": "pack_details", "purpose": "Press 1 = daily 2 pula, Press 2 = weekly 5 pula, Press 3 = monthly 10 pula", "max_words": 35},
    {"id": "thanks", "purpose": "Thank; confirm activation; dial 1195 anytime; remember 1195", "max_words": 25},
]

# Vodacom Tanzania MagicVoice: welcome (no CTA) → subscription/double consent (price) → thanks (CTA + shortcode)
VODACOM_TANZANIA_MAGICVOICE_STEPS = [
    {"id": "welcome", "purpose": "Warm welcome; introduce MagicVoice; invite to continue. Do not say shortcode or dial number yet.", "max_words": 40},
    {"id": "subscription_doubleconsent", "purpose": "Subscription options and price point; double consent / confirm choice (e.g. Press 1 for X, Press 2 for Y).", "max_words": 40},
    {"id": "thanks", "purpose": "Thank you; confirm activation; CTA and shortcode (dial X, remember X).", "max_words": 25},
]

rows = [
    {
        "account_key": "BTC",
        "service_key": "Christianity",
        "display_name": "BTC Christianity 3-step",
        "steps": BTC_CHRISTIANITY_STEPS,
        "is_default": True,
    },
    {
        "account_key": "Vodacom Tanzania",
        "service_key": "MagicVoice",
        "display_name": "Vodacom Tanzania MagicVoice 3-step",
        "steps": VODACOM_TANZANIA_MAGICVOICE_STEPS,
        "is_default": True,
    },
]

for r in rows:
    try:
        client.table("flow_configs").upsert(r, on_conflict="account_key,service_key").execute()
        print(f"Upserted: {r['display_name']} ({r['account_key']} / {r['service_key']})")
    except Exception as e:
        print(f"Error upserting {r.get('display_name')}: {e}")

print("Done. List flows via GET /api/flow-configs.")
