#!/usr/bin/env python3
"""
Seed market_countries, market_telcos, and market_languages in Supabase.
Run after applying scripts/market_options_schema.sql.

  python3 scripts/seed_market_options.py

Uses the same data as the frontend fallback (CountryTelcoSelect + countryCurrency).
Skips countries that already exist.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
except ImportError:
    pass

from backend.database import supabase

# Country id/name, currency_code, display_order (match frontend COUNTRIES order)
COUNTRIES = [
    ("Botswana", "BWP", 0),
    ("Bangladesh", "BDT", 1),
    ("Cameroon", "XAF", 2),
    ("Congo (DRC)", "CDF", 3),
    ("Congo (Republic)", "XAF", 4),
    ("Ethiopia", "ETB", 5),
    ("Ghana", "GHS", 6),
    ("Guyana", "GYD", 7),
    ("Haiti", "HTG", 8),
    ("India", "INR", 9),
    ("Indonesia", "IDR", 10),
    ("Kenya", "KES", 11),
    ("Mozambique", "MZN", 12),
    ("Nigeria", "NGN", 13),
    ("Pakistan", "PKR", 14),
    ("Philippines", "PHP", 15),
    ("Rwanda", "RWF", 16),
    ("Senegal", "XOF", 17),
    ("Somalia", "SOS", 18),
    ("South Africa", "ZAR", 19),
    ("Tanzania", "TZS", 20),
    ("Uganda", "UGX", 21),
    ("Zambia", "ZMW", 22),
    ("Zimbabwe", "ZWL", 23),
]

TELCOS = {
    "Botswana": ["Mascom", "Orange Botswana", "beMobile", "BTC"],
    "Bangladesh": ["Grameenphone", "Robi", "Banglalink", "Teletalk"],
    "Cameroon": ["MTN Cameroon", "Orange Cameroon", "Nexttel"],
    "Congo (DRC)": ["Vodacom DRC", "Airtel DRC", "Orange DRC", "Africell DRC"],
    "Congo (Republic)": ["MTN Congo", "Airtel Congo"],
    "Ethiopia": ["Ethio Telecom", "Safaricom Ethiopia"],
    "Ghana": ["MTN Ghana", "Vodafone Ghana", "AirtelTigo"],
    "Guyana": ["Digicel Guyana", "GTT"],
    "Haiti": ["Digicel Haiti", "Natcom"],
    "India": ["Jio", "Airtel India", "Vi (Vodafone Idea)", "BSNL"],
    "Indonesia": ["Telkomsel", "Indosat", "XL Axiata", "Tri"],
    "Kenya": ["Safaricom", "Airtel Kenya", "Telkom Kenya"],
    "Mozambique": ["Vodacom Mozambique", "Movitel", "Tmcel"],
    "Nigeria": ["MTN Nigeria", "Airtel Nigeria", "Glo", "9mobile"],
    "Pakistan": ["Jazz", "Telenor Pakistan", "Zong", "Ufone"],
    "Philippines": ["Globe", "Smart", "DITO"],
    "Rwanda": ["MTN Rwanda", "Airtel Rwanda"],
    "Senegal": ["Orange Senegal", "Free Senegal", "Expresso"],
    "Somalia": ["Hormuud", "Somtel", "Golis"],
    "South Africa": ["Vodacom", "MTN SA", "Cell C", "Telkom SA"],
    "Tanzania": ["Vodacom Tanzania", "Airtel Tanzania", "Tigo", "Halotel"],
    "Uganda": ["MTN Uganda", "Airtel Uganda", "Africell Uganda"],
    "Zambia": ["MTN Zambia", "Airtel Zambia", "Zamtel"],
    "Zimbabwe": ["Econet", "NetOne", "Telecel"],
}

LANGUAGES = {
    "Botswana": ["English", "Setswana"],
    "Bangladesh": ["Bengali", "English"],
    "Cameroon": ["French", "English", "Pidgin English"],
    "Congo (DRC)": ["French", "Lingala", "Swahili"],
    "Congo (Republic)": ["French", "Lingala"],
    "Ethiopia": ["Amharic", "Oromo", "English"],
    "Ghana": ["English", "Twi", "Pidgin English"],
    "Guyana": ["English", "Creolese"],
    "Haiti": ["Haitian Creole", "French"],
    "India": ["Hindi", "Hinglish", "Tamil", "Telugu", "Bengali", "Kannada", "Malayalam", "English"],
    "Indonesia": ["Indonesian", "English"],
    "Kenya": ["English", "Swahili"],
    "Mozambique": ["Portuguese"],
    "Nigeria": ["English", "Pidgin English", "Hausa", "Yoruba", "Igbo"],
    "Pakistan": ["Urdu", "English", "Punjabi"],
    "Philippines": ["Filipino", "English", "Tagalog"],
    "Rwanda": ["Kinyarwanda", "English", "French"],
    "Senegal": ["French", "Wolof"],
    "Somalia": ["Somali", "Arabic", "English"],
    "South Africa": ["English", "Zulu", "Afrikaans", "Xhosa"],
    "Tanzania": ["Swahili", "English"],
    "Uganda": ["English", "Luganda", "Swahili"],
    "Zambia": ["English", "Bemba", "Nyanja"],
    "Zimbabwe": ["English", "Shona", "Ndebele"],
}


def main():
    if not supabase:
        print("❌ Supabase is not available. Install supabase and set SUPABASE_URL / SUPABASE_SERVICE_KEY.")
        sys.exit(1)
    try:
        existing = supabase.table("market_countries").select("id").execute()
        existing_ids = {r["id"] for r in (existing.data or [])}
    except Exception as e:
        print("❌ Tables may not exist. Run scripts/market_options_schema.sql first.")
        print(e)
        sys.exit(1)

    countries_added = 0
    for country_id, currency_code, display_order in COUNTRIES:
        if country_id in existing_ids:
            continue
        try:
            supabase.table("market_countries").insert({
                "id": country_id,
                "name": country_id,
                "currency_code": currency_code,
                "display_order": display_order,
            }).execute()
            countries_added += 1
        except Exception as e:
            print(f"⚠️  Country {country_id}: {e}")
            continue

        for i, telco in enumerate(TELCOS.get(country_id, [])):
            try:
                supabase.table("market_telcos").insert({
                    "country_id": country_id,
                    "name": telco,
                    "display_order": i,
                }).execute()
            except Exception as e:
                print(f"⚠️  Telco {country_id} / {telco}: {e}")
        for i, lang in enumerate(LANGUAGES.get(country_id, [])):
            try:
                supabase.table("market_languages").insert({
                    "country_id": country_id,
                    "name": lang,
                    "display_order": i,
                }).execute()
            except Exception as e:
                print(f"⚠️  Language {country_id} / {lang}: {e}")

    print(f"✅ Market options: {countries_added} countries added (telcos/languages per country).")


if __name__ == "__main__":
    main()
