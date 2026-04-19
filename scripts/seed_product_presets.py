#!/usr/bin/env python3
"""
Seed the product_presets table in Supabase with the default BNG product list.
Run after applying scripts/product_presets_schema.sql.

  python3 scripts/seed_product_presets.py

Uses the same fallback content as the frontend so the app behaves identically
when reading from DB. Skips insert if a row with the same id already exists.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env so SUPABASE_URL and SUPABASE_SERVICE_KEY are set when running from CLI
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
except ImportError:
    pass

from backend.database import supabase

# Default presets (mirrors frontend FALLBACK_RAW). full_description must match preset structure.
SEED = [
    {"id": "ai-personal-assistant", "name": "AI personal assistant", "icon": "Sparkles", "short_desc": "When you can't pick up, EVA PA picks up for you", "category": "ai", "display_order": 0,
     "full_description": "EVA — Your AI Personal Assistant\n\nWhen you can't pick up, EVA PA picks up for you.\n\nThe Problem:\nEvery day, people miss calls that matter. Life doesn't pause for phone calls. People are driving, in meetings, spending time with family, or simply too occupied to answer. When they can't pick up, the call just rings out. The caller gets no response, no information, nothing. Important messages are lost, urgent requests go unheard, and callbacks pile up.\n\nWhen you are driving or commuting, you can't safely answer — the caller gives up and may not call back. When you are in a meeting or at work, your phone is on silent and urgent calls go completely unnoticed. When your phone is switched off or has no network, the caller hears nothing — there is no way to leave information. When you are busy with family or personal time, interrupting personal moments for every call isn't an option — but missing them has consequences.\n\nHow EVA Solves This:\nWhen a subscriber is busy, switched off, or unavailable, EVA PA answers the incoming call on behalf of the subscriber. It talks to the caller like a real person — listens, responds naturally, collects the caller's message, and sends a summary to the subscriber via SMS so they know exactly who called and why.\n\nWhat EVA Does:\n1. Takes subscriber's calls like a human — EVA PA carries a natural, empathetic conversation with the caller, taking all necessary information on the subscriber's behalf.\n2. Speaks in the caller's language — EVA converses with natural pronunciation and cultural awareness, respecting the sentiments, demographics, and sensitivities of the caller's region.\n3. Sends a call summary to the subscriber — after every call, EVA sends an SMS with who called, what they wanted, and any information they shared.\n4. Alerts instantly for urgent calls — if EVA detects urgency, it sends a flash SMS so the subscriber can act right away.\n5. Learns from every call — EVA learns caller behavior and nature from past interactions and trains itself to respond better in favor of the subscriber, making every subsequent call smoother.\n6. Customizable persona — subscribers can name their EVA, choose a voice, and set a personality tone. If they skip setup, a default persona works out of the box.\n\nHow It Works:\nWhen a subscriber's number is busy, switched off, or goes unanswered, the telecom operator's core network detects the condition and conditionally forwards the call to BlackNGreen's EVA servers. EVA's AI personal assistant answers the call in real time, has a natural conversation with the caller, collects the message, and delivers a call summary back to the subscriber via SMS. The subscriber does not need any app, internet connection, or smartphone — the service works on any phone through the operator's network.\n\nShortcode / CTA:\n\n\nPricing:\n"},
    {"id": "smartconnect", "name": "SmartConnect AI", "icon": "Radio", "short_desc": "Zero-balance revenue & engagement platform", "category": "connectivity", "display_order": 1,
     "full_description": "SmartConnect AI - Revenue & Engagement Platform\n\nProduct Overview:\nSmartConnect AI is a revolutionary platform that transforms failed/incomplete calls into revenue opportunities. When a subscriber has zero or low balance and tries to make a call, instead of hearing \"insufficient balance,\" they are routed to SmartConnect — a platform offering instant solutions like airtime loans, digital services, and promotions.\n\nKey Features:\n- Intercepts zero-balance and incomplete calls automatically\n- Offers instant airtime loans through integrated lending partners\n- Promotes operator's own VAS services to engaged users\n- Intellisense AI technology personalizes offers based on user behavior\n- No base requirement — traffic comes automatically from the network\n- Zero complaints — user initiates the interaction voluntarily\n\nShortcode / CTA:\n\n\nPricing:\n"},
    {"id": "callsignature", "name": "Call Signature", "icon": "Shield", "short_desc": "Verified business caller ID with 93% pickup rate", "category": "enterprise", "display_order": 2,
     "full_description": "Call Signature - Named CLI & Verified Caller ID\n\nProduct Overview:\nCall Signature transforms regular outbound calls by displaying verified business names, logos, and purpose instead of unknown numbers. This dramatically improves call pickup rates — from an industry average of 15-20% to over 93%.\n\nKey Features:\n- Displays business name and logo on recipient's phone\n- Verified caller badge prevents spam classification\n- Works across all phone types (feature phones show text, smartphones show rich media)\n- Real-time call purpose display (\"Delivery Update\", \"Appointment Reminder\")\n- Anti-spam protection — calls are never flagged by Truecaller or network filters\n- Analytics dashboard showing pickup rates, call duration, and engagement\n\nShortcode / CTA:\n\n\nPricing:\n"},
    {"id": "magicvoice", "name": "Magic Voice", "icon": "Mic2", "short_desc": "World's #1 voice changer for calls — voice avatars & ambience", "category": "voice", "display_order": 3,
     "full_description": "Magic Voice - World's #1 Voice Changer\n\nProduct Overview:\nMagic Voice is the world's leading voice changer platform that lets users transform their voice during live calls. Available via IVR (short-code dial) and Mobile App, users can choose from voice avatars (Female, Kid, Celebrity, Cartoon) and background ambience effects (Concert, Airport, Traffic, James Bond) to create fun, personalized calling experiences.\n\nKey Features:\n- Real-time voice changing during live calls — voice avatars: Female, Cartoon, Celebrity, Kid\n- Background ambience effects: Concert, Airport, Traffic, James Bond\n- Available on IVR (dial short-code + mobile number) and Mobile App\n- Works with standard phone calls — no internet needed for the call\n- Subscription via SMS download link, web landing page, or banner ads\n\nShortcode / CTA:\n\n\nPricing:\n"},
    {"id": "magiccall", "name": "Magic Call App", "icon": "Phone", "short_desc": "Voice changer & caller entertainment app (20M+ downloads)", "category": "voice", "display_order": 4,
     "full_description": "Magic Call App - Voice Changer & Caller Entertainment\n\nProduct Overview:\nMagic Call is BNG's consumer app that lets users change their voice during live calls, add background sounds, and create fun calling experiences. With 20 million+ downloads, it's one of BNG's most successful consumer products.\n\nKey Features:\n- Real-time voice changing during calls (male, female, child, robot, etc.)\n- Background sound effects (rain, traffic, office, party)\n- Voice recording and sharing\n- Prank call features with pre-set scenarios\n- Works with regular phone calls — no internet needed for the call itself\n- Available on Android and iOS\n\nShortcode / CTA:\n\n\nPricing:\n"},
    {"id": "dreamtravel", "name": "DreamTravel", "icon": "Plane", "short_desc": "Interactive quiz platform — win dream travel trips", "category": "entertainment", "display_order": 5,
     "full_description": "DreamTravel - Unlock Rewards with Every Challenge\n\nProduct Overview:\nDreamTravel is an interactive quiz platform where users answer fun, engaging quizzes for a chance to win a trip to their dream destination. Available via WAP and IVR, it is tailored for telecom operators seeking gamified engagement and loyalty programs.\n\nKey Features:\n- Interactive quiz platform: users answer quizzes for a chance to win a dream vacation\n- Tailored for telecom operators — customizable per brand and customer segment\n- Seamless integration with existing telecom billing and loyalty programs\n- Available via SMS opt-in, IVR, or web\n- Gamified experience drives long-term customer interaction and retention\n- All-expenses-paid trip as the grand prize, plus discounts and telco offers\n- Plus-one option: winners bring a companion\n\nShortcode / CTA:\n\n\nPricing:\n"},
    {"id": "mobibattle", "name": "MobiBattle", "icon": "Gamepad2", "short_desc": "Real-time competitive gaming platform for telcos", "category": "entertainment", "display_order": 6,
     "full_description": "MobiBattle - A Real-Time Competitive Gaming Platform\n\nProduct Overview:\nMobiBattle is a real-time competitive gaming platform where players battle other players on popular casual games and global e-sports. Designed for telecom operators, it captures the massive mobile gaming market (188.6B revenue by 2027, 1.7B multiplayer gamers).\n\nKey Features:\n- Real-time multiplayer casual games (2-4 players)\n- Large-scale competitive e-sports tournaments (100-500 players)\n- In-app purchases via prepaid balance, operator mobile money, or 3rd party payment\n- Live streaming integration (YouTube, Twitch, Nimo)\n- Gratification/reward system based on leaderboards\n- 50+ casual games, top e-sports titles\n- Rewards: data packs, airtime, prizes\n\nShortcode / CTA:\n\n\nPricing:\n"},
    {"id": "swipenwin", "name": "SwipeNWin", "icon": "BookOpen", "short_desc": "Gamified quiz platform — swipe, play, triumph", "category": "entertainment", "display_order": 7,
     "full_description": "SwipeNWin - Unleash Your Quiz Superpowers\n\nProduct Overview:\nSwipeNWin is a gamified quiz platform offering multiple quiz formats — Moment Quiz (trending topics), Category Quiz (MCQs across topics), and Swipe Quiz (True/False format). Features enhanced leaderboards, daily/weekly/monthly prizes, and event-based quizzes.\n\nKey Features:\n- Moment Quiz: Daily quizzes on trending topics and current events, curated by experts\n- Category Quiz: MCQ quizzes across 10,000+ questions in multiple categories (History, Science, Pop Culture, Sports, Travel, etc.)\n- Swipe Quiz: Fast-paced True/False format with swipe gestures — ideal for mobile\n- Enhanced Leaderboard: Ranks users on overall performance, motivates frequent play\n- Event-based quizzes: Christmas, Valentine's, Ramadan, festive themes\n- Spot Quizzes: Scheduled timed quizzes for competitive thrill\n- Social sharing integration for scores\n- Customizable in multiple languages\n- Subscription-based with buy-more-chances option\n\nShortcode / CTA:\n\n\nPricing:\n"},
    {"id": "islamicportal", "name": "Islamic Portal", "icon": "Moon", "short_desc": "Islamic content platform — Quran, Duas, Salat alerts", "category": "lifestyle", "display_order": 8,
     "full_description": "Islamic Portal - Connect with Your Faith\n\nProduct Overview:\nIslamic Portal is BNG's multi-channel Islamic content platform serving 42 million subscribers across 32 countries. Available via IVR, App, WAP, and SMS, it helps Muslims stay connected to their faith through audio Quran, Duas, Salat alerts, Nasheeds, and more.\n\nKey Features:\n- Audio Quran: Listen to the Holy Quran on basic handsets or app\n- 40 Most Powerful Rabbanas/Duas from the Quran\n- Salat Alerts: 5 times a day prayer reminders\n- Nasheeds: Soothing Islamic songs\n- 99 Names of Allah: Listen or recite\n- Dhikr practice on mobile phones\n- Educational Islamic videos\n- Islamic wallpapers\n- Content available in regional languages\n- Available via IVR, App, WAP, SMS\n\nShortcode / CTA:\n\n\nPricing:\n"},
    {"id": "christianity", "name": "Christianity Portal", "icon": "Cross", "short_desc": "Christian content platform — Bible, prayers, gospel songs", "category": "lifestyle", "display_order": 9,
     "full_description": "Christianity Portal - Stay Connected to Your Faith\n\nProduct Overview:\nChristianity Portal allows subscribers to access Bible verses, 1000+ audiobooks, live prayers, Bible stories, gospel songs, and more. Available via App and IVR, it has reached 42 million subscribers across 32 countries.\n\nKey Features:\n- Audio Bible: Listen to the Bible anytime\n- Daily Verse: Receive daily inspirational Bible verses\n- 1000+ Audiobooks & Ebooks across 50+ categories\n- Live Prayer streaming exclusive for subscribers\n- Biblical Stories collection\n- Gospel Songs library\n- Morning/Evening Glory devotionals\n- Exclusive Christian videos\n- Daily Feed Story\n- Available via App and IVR\n\nShortcode / CTA:\n\n\nPricing:\n"},
    {"id": "learnenglish", "name": "Learn English", "icon": "GraduationCap", "short_desc": "Interactive English learning platform via IVR & Web", "category": "education", "display_order": 10,
     "full_description": "Learn English - Empower Your Subscribers\n\nProduct Overview:\nLearn English is a comprehensive and interactive language learning platform designed to help individuals of all ages and backgrounds acquire proficiency in the English language. Available via IVR and Web.\n\nKey Features:\n- Structured modules for learning English\n- Trivia and Tests for engagement\n- Fill-in-the-blank quizzes\n- SMS Dictionary: SMS-driven content for learning on the go\n- Available via IVR and Web platforms\n- Interactive and gamified learning experience\n\nShortcode / CTA:\n\n\nPricing:\n"},
    {"id": "custom", "name": "Custom Product", "icon": "Package", "short_desc": "Upload your own product documentation", "category": "enterprise", "display_order": 11,
     "full_description": ""},
]


def main():
    if not supabase:
        print("❌ Supabase is not available. Do both of the following:")
        print("  1. Install the Supabase Python package:  pip install supabase")
        print("  2. Set SUPABASE_URL and SUPABASE_SERVICE_KEY in a .env file in the project root,")
        print("     or export them in your shell.")
        sys.exit(1)
    try:
        existing = supabase.table("product_presets").select("id").execute()
        ids = {r["id"] for r in (existing.data or [])}
    except Exception as e:
        print("❌ Table product_presets may not exist. Run scripts/product_presets_schema.sql first.")
        print(e)
        sys.exit(1)
    inserted = 0
    skipped = 0
    for row in SEED:
        if row["id"] in ids:
            skipped += 1
            continue
        try:
            supabase.table("product_presets").insert({
                "id": row["id"],
                "name": row["name"],
                "icon": row["icon"],
                "short_desc": row["short_desc"],
                "full_description": row["full_description"],
                "category": row["category"],
                "display_order": row["display_order"],
            }).execute()
            inserted += 1
        except Exception as e:
            print(f"⚠️  Failed to insert {row['id']}: {e}")
    print(f"✅ Product presets: {inserted} inserted, {skipped} already present.")


if __name__ == "__main__":
    main()
