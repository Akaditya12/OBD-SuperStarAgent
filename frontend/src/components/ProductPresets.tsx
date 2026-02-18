"use client";

import { Package, Sparkles, Phone, Shield, Mic2, Radio } from "lucide-react";

export interface ProductPreset {
  id: string;
  name: string;
  icon: React.ReactNode;
  shortDesc: string;
  fullDescription: string;
  category: "ai" | "voice" | "connectivity" | "enterprise";
}

export const BNG_PRODUCTS: ProductPreset[] = [
  {
    id: "eva",
    name: "EVA - AI Personal Assistant",
    icon: <Sparkles className="w-4 h-4" />,
    shortDesc: "AI assistant that handles calls when you're busy",
    category: "ai",
    fullDescription: `EVA - AI Personal Assistant on Voice Call

Product Overview:
EVA is a voice-first AI conversational assistant designed for telecom subscribers. When a user is busy, unavailable, or on another call, EVA answers on their behalf — acting as a smart, AI-powered personal assistant.

Key Features:
- Answers calls when the subscriber is busy, unavailable, or on DND
- Understands caller intent through natural conversation in 95+ languages
- Integrates with calendars (Google, Outlook, Apple) to schedule appointments
- Sends call summaries via WhatsApp, Email, or SMS to the subscriber
- Learns the subscriber's preferences over time for personalized responses
- Works on any phone — no app download required, activated via USSD/SMS

How It Works:
1. Caller dials subscriber → subscriber is busy/unavailable
2. Call is forwarded to EVA
3. EVA greets the caller naturally and asks how it can help
4. EVA takes messages, schedules callbacks, or provides information
5. Subscriber receives a summary of the call with action items

Pricing:
- Subscription: $0.30 to $3 per user per month (varies by market)
- Expected penetration: 5-8% of subscriber base
- Revenue potential: $1.5M to $25M per month depending on operator size

Value Proposition for Subscribers:
- Never miss an important call again
- Professional call handling 24/7
- Smart scheduling and message taking
- Works in local languages

Value Proposition for Telcos:
- New recurring revenue stream with zero CAPEX
- Revenue share model — no upfront investment
- Reduces churn by adding sticky value-added service
- Increases ARPU by $0.30-$3 per active user
- Quick deployment — 4-6 weeks to launch

Subscription Mechanism:
- USSD activation: Dial *123# → Select EVA → Subscribe
- SMS activation: Send "EVA" to short code
- OBD promotion: Press 1 to activate during promotional call`,
  },
  {
    id: "smartconnect",
    name: "SmartConnect AI",
    icon: <Radio className="w-4 h-4" />,
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

How It Works:
1. Subscriber with low/zero balance tries to make a call
2. Instead of "insufficient balance" tone, call routes to SmartConnect
3. SmartConnect greets user and offers relevant solutions:
   - Press 1 for instant airtime loan
   - Press 2 for data bundle offers
   - Press 3 for VAS service subscriptions
   - Press 4 for partner promotions
4. User selects option → service delivered instantly

Revenue Impact:
- 5% revenue uplift for operators
- 25% improvement in subscriber retention
- Handles 8-9 million calls daily per operator
- No dependency on subscriber base provisioning

Value Proposition:
- FREE platform — no promotion cost needed
- Daily automatic traffic of millions of users
- Users are voluntarily engaging (not push marketing)
- No spam complaints or Truecaller blocking issues
- No base rotation needed — fresh traffic every day
- Cross-sell and upsell opportunity for all VAS products

Subscription Mechanism:
- Automatic — no subscription needed
- User is routed when they have insufficient balance
- Services activated via DTMF during the call`,
  },
  {
    id: "callsignature",
    name: "Call Signature",
    icon: <Shield className="w-4 h-4" />,
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

The Problem It Solves:
- 41% of calls from unknown numbers go unanswered
- OBD campaigns suffer from low pickup rates (15-20%)
- Truecaller and network spam filters block legitimate business calls
- Short codes and long codes are increasingly recognized as promotional

How It Works:
1. Business registers their brand and call purposes
2. When making outbound calls, caller ID shows business name + purpose
3. Recipient sees "BNG Services - Product Offer" instead of unknown number
4. Pickup rate increases to 93%+ because call appears trustworthy

Revenue Impact:
- 93% call pickup rate (vs 15-20% for unknown numbers)
- 4x improvement in OBD campaign effectiveness
- Reduces wasted call minutes on unanswered calls
- Higher conversion rates due to trust factor

Pricing:
- Per-call pricing model
- Volume discounts for high-traffic campaigns
- Revenue share option for telco partners

Subscription Mechanism:
- Enterprise API integration
- Self-service portal for campaign management
- Bulk upload of caller ID profiles`,
  },
  {
    id: "magicvoice",
    name: "Magic Voice IVR",
    icon: <Mic2 className="w-4 h-4" />,
    shortDesc: "Interactive voice response entertainment platform",
    category: "voice",
    fullDescription: `Magic Voice IVR - Interactive Voice Entertainment Platform

Product Overview:
Magic Voice IVR is BNG's flagship interactive voice response platform that provides entertainment, information, and utility services through simple phone calls. It's designed for markets with high feature phone penetration where app-based services aren't accessible.

Key Features:
- Voice-based entertainment: jokes, stories, music, horoscopes
- Information services: news, weather, sports scores, exam results
- Utility services: balance check, recharge options, service activation
- Multi-language support with local voice artists
- DTMF-based navigation — works on any phone
- Customizable IVR flows per operator and market

How It Works:
1. Subscriber dials a short code or is connected via OBD/SmartConnect
2. Greeted with a dynamic, engaging IVR menu
3. Navigates using keypad (Press 1 for..., Press 2 for...)
4. Content delivered via pre-recorded or AI-generated voice
5. Subscription options presented at natural break points

Revenue Model:
- Per-minute charges during IVR session
- Subscription packages (daily, weekly, monthly)
- Premium content tiers
- Ad-supported free tier with partner promotions

Scale:
- Handles 1 billion+ transactions per month globally
- Deployed across 100+ countries
- Serves 290+ million active users

Value for Telcos:
- Proven revenue generator with 15+ years track record
- Low churn — entertainment services are sticky
- Works on feature phones — massive addressable market
- Quick deployment with BNG's cloud infrastructure

Subscription Mechanism:
- USSD: Dial *456# to subscribe
- SMS: Send keyword to short code
- OBD: Press 1 during promotional call
- Auto-renewal with easy opt-out`,
  },
  {
    id: "magiccall",
    name: "Magic Call App",
    icon: <Phone className="w-4 h-4" />,
    shortDesc: "Voice changer & caller entertainment app (20M+ downloads)",
    category: "voice",
    fullDescription: `Magic Call App - Voice Changer & Caller Entertainment

Product Overview:
Magic Call is BNG's consumer app that lets users change their voice during live calls, add background sounds, and create fun calling experiences. The app grew from 1 million to 20 million downloads rapidly, making it one of BNG's most successful consumer products.

Key Features:
- Real-time voice changing during calls (male, female, child, robot, etc.)
- Background sound effects (rain, traffic, office, party)
- Voice recording and sharing
- Prank call features with pre-set scenarios
- Works with regular phone calls — no internet needed for the call itself
- Available on Android and iOS

Growth Metrics:
- 20 million+ downloads
- Rapid viral growth through word-of-mouth
- High daily active user engagement
- Strong retention due to entertainment value

Revenue Model:
- Freemium with premium voice packs
- In-app purchases for special effects
- Subscription for unlimited access
- Ad-supported free tier

Value for Telcos:
- Drives voice call minutes (users make more calls for fun)
- Co-branding opportunity with operator
- Data revenue from app usage
- Youth segment engagement

Promotion Points for OBD:
- "Want to prank your friends? Download Magic Call!"
- "Change your voice to anyone — celebrity, cartoon, robot!"
- "20 million people are already having fun — join them!"
- Press 1 to get the download link via SMS`,
  },
  {
    id: "custom",
    name: "Custom Product",
    icon: <Package className="w-4 h-4" />,
    shortDesc: "Upload your own product documentation",
    category: "enterprise",
    fullDescription: "",
  },
];

interface ProductPresetsProps {
  selectedProduct: string;
  onSelect: (product: ProductPreset) => void;
}

export default function ProductPresets({
  selectedProduct,
  onSelect,
}: ProductPresetsProps) {
  const categories = [
    { id: "ai", label: "AI Solutions" },
    { id: "connectivity", label: "Connectivity" },
    { id: "voice", label: "Voice & Entertainment" },
    { id: "enterprise", label: "Enterprise" },
  ];

  return (
    <div className="space-y-3">
      <label className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)]">
        <Package className="w-4 h-4 text-[var(--accent)]" />
        BNG Product
        <span className="text-xs text-[var(--text-tertiary)] ml-1">
          (select to auto-fill or choose Custom)
        </span>
      </label>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {BNG_PRODUCTS.filter((p) => p.id !== "smartconnect").map((product) => {
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
