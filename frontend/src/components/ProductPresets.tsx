"use client";

import { Package, Sparkles, Phone, Shield, Mic2, Radio, Gamepad2, Plane, BookOpen, Cross, Moon, GraduationCap } from "lucide-react";

export type ProductPresetCategory = "ai" | "voice" | "connectivity" | "enterprise" | "entertainment" | "education" | "lifestyle";

export interface ProductPreset {
  id: string;
  name: string;
  icon: React.ReactNode;
  shortDesc: string;
  fullDescription: string;
  category: ProductPresetCategory;
}

/** API shape (icon as string). */
export interface ProductPresetFromAPI {
  id: string;
  name: string;
  icon: string;
  shortDesc: string;
  fullDescription: string;
  category: ProductPresetCategory;
  displayOrder?: number;
}

const ICON_MAP: Record<string, React.ReactNode> = {
  Package: <Package className="w-4 h-4" />,
  Sparkles: <Sparkles className="w-4 h-4" />,
  Phone: <Phone className="w-4 h-4" />,
  Shield: <Shield className="w-4 h-4" />,
  Mic2: <Mic2 className="w-4 h-4" />,
  Radio: <Radio className="w-4 h-4" />,
  Gamepad2: <Gamepad2 className="w-4 h-4" />,
  Plane: <Plane className="w-4 h-4" />,
  BookOpen: <BookOpen className="w-4 h-4" />,
  Cross: <Cross className="w-4 h-4" />,
  Moon: <Moon className="w-4 h-4" />,
  GraduationCap: <GraduationCap className="w-4 h-4" />,
};

export function mapApiPresetToProductPreset(p: ProductPresetFromAPI): ProductPreset {
  return {
    id: p.id,
    name: p.name,
    icon: ICON_MAP[p.icon] ?? <Package className="w-4 h-4" />,
    shortDesc: p.shortDesc,
    fullDescription: p.fullDescription,
    category: p.category,
  };
}

/** Fallback data when API is unavailable (icon as string). */
const FALLBACK_RAW: ProductPresetFromAPI[] = [
  {
    id: "ai-personal-assistant",
    name: "AI personal assistant",
    icon: "Sparkles",
    shortDesc: "When you can't pick up, EVA PA picks up for you",
    category: "ai",
    fullDescription: `EVA — Your AI Personal Assistant

When you can't pick up, EVA PA picks up for you.

The Problem:
Every day, people miss calls that matter. Life doesn't pause for phone calls. People are driving, in meetings, spending time with family, or simply too occupied to answer. When they can't pick up, the call just rings out. The caller gets no response, no information, nothing. Important messages are lost, urgent requests go unheard, and callbacks pile up.

When you are driving or commuting, you can't safely answer — the caller gives up and may not call back. When you are in a meeting or at work, your phone is on silent and urgent calls go completely unnoticed. When your phone is switched off or has no network, the caller hears nothing — there is no way to leave information. When you are busy with family or personal time, interrupting personal moments for every call isn't an option — but missing them has consequences.

How EVA Solves This:
When a subscriber is busy, switched off, or unavailable, EVA PA answers the incoming call on behalf of the subscriber. It talks to the caller like a real person — listens, responds naturally, collects the caller's message, and sends a summary to the subscriber via SMS so they know exactly who called and why.

What EVA Does:
1. Takes subscriber's calls like a human — EVA PA carries a natural, empathetic conversation with the caller, taking all necessary information on the subscriber's behalf.
2. Speaks in the caller's language — EVA converses with natural pronunciation and cultural awareness, respecting the sentiments, demographics, and sensitivities of the caller's region.
3. Sends a call summary to the subscriber — after every call, EVA sends an SMS with who called, what they wanted, and any information they shared.
4. Alerts instantly for urgent calls — if EVA detects urgency, it sends a flash SMS so the subscriber can act right away.
5. Learns from every call — EVA learns caller behavior and nature from past interactions and trains itself to respond better in favor of the subscriber, making every subsequent call smoother.
6. Customizable persona — subscribers can name their EVA, choose a voice, and set a personality tone. If they skip setup, a default persona works out of the box.

How It Works:
When a subscriber's number is busy, switched off, or goes unanswered, the telecom operator's core network detects the condition and conditionally forwards the call to BlackNGreen's EVA servers. EVA's AI personal assistant answers the call in real time, has a natural conversation with the caller, collects the message, and delivers a call summary back to the subscriber via SMS. The subscriber does not need any app, internet connection, or smartphone — the service works on any phone through the operator's network.

Shortcode / CTA:


Pricing:
`,
  },
  {
    id: "smartconnect",
    name: "SmartConnect AI",
    icon: "Radio",
    shortDesc: "Zero-balance revenue & engagement platform",
    category: "connectivity",
    fullDescription: `SmartConnect AI - Revenue & Engagement Platform

Product Overview:
SmartConnect AI is a revolutionary platform that transforms failed/incomplete calls into revenue opportunities. When a subscriber has zero or low balance and tries to make a call, instead of hearing "insufficient balance," they are routed to SmartConnect — a platform offering instant solutions like airtime loans, digital services, and promotions.

Key Features:
- Intercepts zero-balance and incomplete calls automatically
- Offers instant airtime loans through integrated lending partners
- Promotes operator's own VAS services to engaged users
- Intellisense AI technology personalizes offers based on user behavior
- No base requirement — traffic comes automatically from the network
- Zero complaints — user initiates the interaction voluntarily

Shortcode / CTA:


Pricing:
`,
  },
  {
    id: "callsignature",
    name: "Call Signature",
    icon: "Shield",
    shortDesc: "Verified business caller ID with 93% pickup rate",
    category: "enterprise",
    fullDescription: `Call Signature - Named CLI & Verified Caller ID

Product Overview:
Call Signature transforms regular outbound calls by displaying verified business names, logos, and purpose instead of unknown numbers. This dramatically improves call pickup rates — from an industry average of 15-20% to over 93%.

Key Features:
- Displays business name and logo on recipient's phone
- Verified caller badge prevents spam classification
- Works across all phone types (feature phones show text, smartphones show rich media)
- Real-time call purpose display ("Delivery Update", "Appointment Reminder")
- Anti-spam protection — calls are never flagged by Truecaller or network filters
- Analytics dashboard showing pickup rates, call duration, and engagement

Shortcode / CTA:


Pricing:
`,
  },
  {
    id: "magicvoice",
    name: "Magic Voice",
    icon: "Mic2",
    shortDesc: "World's #1 voice changer for calls — voice avatars & ambience",
    category: "voice",
    fullDescription: `Magic Voice - World's #1 Voice Changer

Product Overview:
Magic Voice is the world's leading voice changer platform that lets users transform their voice during live calls. Available via IVR (short-code dial) and Mobile App, users can choose from voice avatars (Female, Kid, Celebrity, Cartoon) and background ambience effects (Concert, Airport, Traffic, James Bond) to create fun, personalized calling experiences.

Key Features:
- Real-time voice changing during live calls — voice avatars: Female, Cartoon, Celebrity, Kid
- Background ambience effects: Concert, Airport, Traffic, James Bond
- Available on IVR (dial short-code + mobile number) and Mobile App
- Works with standard phone calls — no internet needed for the call
- Subscription via SMS download link, web landing page, or banner ads

Shortcode / CTA:


Pricing:
`,
  },
  {
    id: "dreamtravel",
    name: "DreamTravel",
    icon: "Plane",
    shortDesc: "Interactive quiz platform — win dream travel trips",
    category: "entertainment",
    fullDescription: `DreamTravel - Unlock Rewards with Every Challenge

Product Overview:
DreamTravel is an interactive quiz platform where users answer fun, engaging quizzes for a chance to win a trip to their dream destination. Available via WAP and IVR, it is tailored for telecom operators seeking gamified engagement and loyalty programs.

Key Features:
- Interactive quiz platform: users answer quizzes for a chance to win a dream vacation
- Tailored for telecom operators — customizable per brand and customer segment
- Seamless integration with existing telecom billing and loyalty programs
- Available via SMS opt-in, IVR, or web
- Gamified experience drives long-term customer interaction and retention
- All-expenses-paid trip as the grand prize, plus discounts and telco offers
- Plus-one option: winners bring a companion

Shortcode / CTA:


Pricing:
`,
  },
  {
    id: "mobibattle",
    name: "MobiBattle",
    icon: "Gamepad2",
    shortDesc: "Real-time competitive gaming platform for telcos",
    category: "entertainment",
    fullDescription: `MobiBattle - A Real-Time Competitive Gaming Platform

Product Overview:
MobiBattle is a real-time competitive gaming platform where players battle other players on popular casual games and global e-sports. Designed for telecom operators, it captures the massive mobile gaming market (188.6B revenue by 2027, 1.7B multiplayer gamers).

Key Features:
- Real-time multiplayer casual games (2-4 players)
- Large-scale competitive e-sports tournaments (100-500 players)
- In-app purchases via prepaid balance, operator mobile money, or 3rd party payment
- Live streaming integration (YouTube, Twitch, Nimo)
- Gratification/reward system based on leaderboards
- 50+ casual games, top e-sports titles
- Rewards: data packs, airtime, prizes

Shortcode / CTA:


Pricing:
`,
  },
  {
    id: "swipenwin",
    name: "SwipeNWin",
    icon: "BookOpen",
    shortDesc: "Gamified quiz platform — swipe, play, triumph",
    category: "entertainment",
    fullDescription: `SwipeNWin - Unleash Your Quiz Superpowers

Product Overview:
SwipeNWin is a gamified quiz platform offering multiple quiz formats — Moment Quiz (trending topics), Category Quiz (MCQs across topics), and Swipe Quiz (True/False format). Features enhanced leaderboards, daily/weekly/monthly prizes, and event-based quizzes.

Key Features:
- Moment Quiz: Daily quizzes on trending topics and current events, curated by experts
- Category Quiz: MCQ quizzes across 10,000+ questions in multiple categories (History, Science, Pop Culture, Sports, Travel, etc.)
- Swipe Quiz: Fast-paced True/False format with swipe gestures — ideal for mobile
- Enhanced Leaderboard: Ranks users on overall performance, motivates frequent play
- Event-based quizzes: Christmas, Valentine's, Ramadan, festive themes
- Spot Quizzes: Scheduled timed quizzes for competitive thrill
- Social sharing integration for scores
- Customizable in multiple languages
- Subscription-based with buy-more-chances option

Shortcode / CTA:


Pricing:
`,
  },
  {
    id: "islamicportal",
    name: "Islamic Portal",
    icon: "Moon",
    shortDesc: "Islamic content platform — Quran, Duas, Salat alerts",
    category: "lifestyle",
    fullDescription: `Islamic Portal - Connect with Your Faith

Product Overview:
Islamic Portal is BNG's multi-channel Islamic content platform serving 42 million subscribers across 32 countries. Available via IVR, App, WAP, and SMS, it helps Muslims stay connected to their faith through audio Quran, Duas, Salat alerts, Nasheeds, and more.

Key Features:
- Audio Quran: Listen to the Holy Quran on basic handsets or app
- 40 Most Powerful Rabbanas/Duas from the Quran
- Salat Alerts: 5 times a day prayer reminders
- Nasheeds: Soothing Islamic songs
- 99 Names of Allah: Listen or recite
- Dhikr practice on mobile phones
- Educational Islamic videos
- Islamic wallpapers
- Content available in regional languages
- Available via IVR, App, WAP, SMS

Shortcode / CTA:


Pricing:
`,
  },
  {
    id: "christianity",
    name: "Christianity Portal",
    icon: "Cross",
    shortDesc: "Christian content platform — Bible, prayers, gospel songs",
    category: "lifestyle",
    fullDescription: `Christianity Portal - Stay Connected to Your Faith

Product Overview:
Christianity Portal allows subscribers to access Bible verses, 1000+ audiobooks, live prayers, Bible stories, gospel songs, and more. Available via App and IVR, it has reached 42 million subscribers across 32 countries.

Key Features:
- Audio Bible: Listen to the Bible anytime
- Daily Verse: Receive daily inspirational Bible verses
- 1000+ Audiobooks & Ebooks across 50+ categories
- Live Prayer streaming exclusive for subscribers
- Biblical Stories collection
- Gospel Songs library
- Morning/Evening Glory devotionals
- Exclusive Christian videos
- Daily Feed Story
- Available via App and IVR

Shortcode / CTA:


Pricing:
`,
  },
  {
    id: "learnenglish",
    name: "Learn English",
    icon: "GraduationCap",
    shortDesc: "Interactive English learning platform via IVR & Web",
    category: "education",
    fullDescription: `Learn English - Empower Your Subscribers

Product Overview:
Learn English is a comprehensive and interactive language learning platform designed to help individuals of all ages and backgrounds acquire proficiency in the English language. Available via IVR and Web.

Key Features:
- Structured modules for learning English
- Trivia and Tests for engagement
- Fill-in-the-blank quizzes
- SMS Dictionary: SMS-driven content for learning on the go
- Available via IVR and Web platforms
- Interactive and gamified learning experience

Shortcode / CTA:


Pricing:
`,
  },
  {
    id: "custom",
    name: "Custom Product",
    icon: "Package",
    shortDesc: "Upload your own product documentation",
    category: "enterprise",
    fullDescription: "",
  },
];

export function getFallbackPresets(): ProductPreset[] {
  return FALLBACK_RAW.map(mapApiPresetToProductPreset);
}

/** @deprecated Use presets from API + getFallbackPresets() for fallback. Kept for backwards compatibility. */
export const BNG_PRODUCTS: ProductPreset[] = getFallbackPresets();

interface ProductPresetsProps {
  selectedProduct: string;
  onSelect: (product: ProductPreset) => void;
  /** Presets from API; when null or empty, fallback to built-in list. */
  presets?: ProductPreset[] | null;
}

export default function ProductPresets({
  selectedProduct,
  onSelect,
  presets = null,
}: ProductPresetsProps) {
  const displayPresets = (presets?.length ? presets : getFallbackPresets()).filter(
    (p) => p.id !== "smartconnect" && p.id !== "magiccall"
  );
  return (
    <div className="space-y-3">
      <label className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)]">
        <Package className="w-4 h-4 text-[var(--accent)]" />
        BNG Product
        <span className="text-xs text-[var(--text-tertiary)] ml-1">
          (select to auto-fill or choose Custom)
        </span>
      </label>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
        {displayPresets.map((product) => {
          const isSelected = selectedProduct === product.id;
          return (
            <button
              key={product.id}
              onClick={() => onSelect(product)}
              className={`group relative flex flex-col items-start gap-1.5 p-3 rounded-xl border text-left transition-all duration-200 ${
                isSelected
                  ? "border-[var(--accent)] bg-[var(--accent-subtle)] shadow-sm"
                  : "border-[var(--card-border)] hover:border-[var(--card-border-hover)] hover:bg-[var(--card-hover)]"
              }`}
              style={
                isSelected
                  ? { boxShadow: `0 2px 8px var(--accent-glow)` }
                  : undefined
              }
            >
              <div
                className={`p-1.5 rounded-lg transition-colors ${
                  isSelected
                    ? "bg-[var(--accent)] text-white"
                    : "bg-[var(--input-bg)] text-[var(--text-tertiary)] group-hover:text-[var(--accent)]"
                }`}
              >
                {product.icon}
              </div>
              <div>
                <p
                  className={`text-xs font-semibold leading-tight ${
                    isSelected
                      ? "text-[var(--accent)]"
                      : "text-[var(--text-primary)]"
                  }`}
                >
                  {product.name}
                </p>
                <p className="text-[10px] text-[var(--text-tertiary)] mt-0.5 line-clamp-2">
                  {product.shortDesc}
                </p>
              </div>
              {isSelected && (
                <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
