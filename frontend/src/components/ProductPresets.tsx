"use client";

import { Package, Sparkles, Phone, Shield, Mic2, Radio, Gamepad2, Plane, BookOpen, Cross, Moon, GraduationCap } from "lucide-react";

export interface ProductPreset {
  id: string;
  name: string;
  icon: React.ReactNode;
  shortDesc: string;
  fullDescription: string;
  category: "ai" | "voice" | "connectivity" | "enterprise" | "entertainment" | "education" | "lifestyle";
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
3. SmartConnect greets user and offers relevant solutions
4. User selects option → service delivered instantly

Revenue Impact:
- 5% revenue uplift for operators
- 25% improvement in subscriber retention
- Handles 8-9 million calls daily per operator

Value Proposition:
- FREE platform — no promotion cost needed
- Daily automatic traffic of millions of users
- Users are voluntarily engaging (not push marketing)
- No spam complaints or Truecaller blocking issues

Subscription Mechanism:
- Automatic — no subscription needed
- User is routed when they have insufficient balance`,
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

How It Works:
1. Business registers their brand and call purposes
2. When making outbound calls, caller ID shows business name + purpose
3. Recipient sees "BNG Services - Product Offer" instead of unknown number
4. Pickup rate increases to 93%+ because call appears trustworthy

Revenue Impact:
- 93% call pickup rate (vs 15-20% for unknown numbers)
- 4x improvement in OBD campaign effectiveness

Subscription Mechanism:
- Enterprise API integration
- Self-service portal for campaign management`,
  },
  {
    id: "magicvoice",
    name: "Magic Voice",
    icon: <Mic2 className="w-4 h-4" />,
    shortDesc: "World's #1 voice changer for calls — voice avatars & ambience",
    category: "voice",
    fullDescription: `Magic Voice - World's #1 Voice Changer

Product Overview:
Magic Voice is the world's leading voice changer platform that lets users transform their voice during live calls. Available via IVR (short-code dial) and Mobile App, users can choose from voice avatars (Female, Kid, Celebrity, Cartoon) and background ambience effects (Concert, Airport, Traffic, James Bond) to create fun, personalized calling experiences.

Key Features:
- Real-time voice changing during live calls — voice avatars: Female, Cartoon, Celebrity, Kid
- Background ambience effects: Concert, Airport, Traffic, James Bond
- Available on IVR (dial short-code + mobile number) and Mobile App
- IVR flow: User dials short-code → selects voice/ambience → call connected to B-party with changed voice
- App flow: Register → Choose a voice → Dial a number → Enjoy the call
- Subscription via SMS download link, web landing page, or banner ads
- Works with standard phone calls — no internet needed for the call

Global Presence:
- Deployed with partners across Nigeria, Ivory Coast, Indonesia, Cambodia, Jordan, Yemen, Zambia, Uganda, Mongolia
- Partnerships with MTN, Orange, Mobicom and other major operators

Deployment Timeline:
- Week 1: Hardware/cloud finalization
- Week 2-3: Installation
- Week 3: Testing & Go Live

Subscription Mechanism:
- User selects desired pack on landing page
- Activation confirmation via SMS with product link
- Available through IVR short-code or app download`,
  },
  {
    id: "magiccall",
    name: "Magic Call App",
    icon: <Phone className="w-4 h-4" />,
    shortDesc: "Voice changer & caller entertainment app (20M+ downloads)",
    category: "voice",
    fullDescription: `Magic Call App - Voice Changer & Caller Entertainment

Product Overview:
Magic Call is BNG's consumer app that lets users change their voice during live calls, add background sounds, and create fun calling experiences. With 20 million+ downloads, it's one of BNG's most successful consumer products.

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

Revenue Model:
- Freemium with premium voice packs
- In-app purchases for special effects
- Subscription for unlimited access

Value for Telcos:
- Drives voice call minutes (users make more calls for fun)
- Co-branding opportunity with operator
- Data revenue from app usage
- Youth segment engagement`,
  },
  {
    id: "dreamtravel",
    name: "DreamTravel",
    icon: <Plane className="w-4 h-4" />,
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

How It Works:
1. Customers opt-in through SMS, IVR, or website
2. Subscribe and join the quiz
3. Answer fun and interactive quizzes related to travel or brand themes
4. Win a dream vacation, discounts, or telco offers
5. Winners receive all-expenses-paid trip to dream destination

Engagement Model:
- Gamification drives frequent use and in-app purchases
- Unlock levels and earn rewards, encouraging longer engagement
- Challenges keep users coming back, increasing data usage and plan upgrades

Revenue Model:
- Subscription-based: revenue share with telecom operators
- Flexible and customizable commercial model
- Rapid 6-week deployment

Deployment Timeline:
- Week 1: Agreements and commercial closure
- Week 2: VM allocation
- Week 3: API integration
- Week 4: UAT
- Week 5: Billing integration
- Week 6: Go Live

Scale: 160+ telecom partners, 90+ countries, 290Mn+ monthly users served`,
  },
  {
    id: "mobibattle",
    name: "MobiBattle",
    icon: <Gamepad2 className="w-4 h-4" />,
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

How It Works (Casual Games):
1. User selects a game from listed games
2. Play free games or play with MobiBattle coins/credits
3. Recommendation system finds live opponent
4. Matched opponents play against each other in real-time

How It Works (E-Sports):
1. User registers for upcoming tournaments via MobiBattle coins
2. Receives Tournament ID & password
3. Participates in tournaments on the native game app
4. Returns to MobiBattle portal to view results & rewards

What's In It for Operators:
- Be at the forefront of e-sports revolution in your country
- Capture loyalty and brand recognition of age group 18-35
- Generate GMV of $2M per million digital customers
- Increase data usage per gamer by 20%
- Increase engagement by 81%, revenue jump by 85%, lower acquisition cost by 90%

Deployment: Full hosting on cloud (2 weeks) + Billing integration (2 weeks) = Go Live (4 weeks)`,
  },
  {
    id: "swipenwin",
    name: "SwipeNWin",
    icon: <BookOpen className="w-4 h-4" />,
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

Quiz Categories:
- World Travel, History, Science, Pop Culture, Sports, Geography, Entertainment, General Knowledge and more
- Addition/deletion of categories based on user behavior and trends

Revenue Model:
- Subscription-based product
- Buy more chances anytime (in-app purchase)
- Daily/weekly/monthly prizes drive engagement
- High engagement gamified experience

Value for Telcos:
- Gamified quiz experience drives daily active usage
- Enhanced leaderboard creates competitive retention
- Event-based and spot quizzes keep content fresh
- Customizable per operator and market`,
  },
  {
    id: "islamicportal",
    name: "Islamic Portal",
    icon: <Moon className="w-4 h-4" />,
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

Channels:
- App: Home, Prayer Alerts, Mosque Finder, Holy Quran (read/listen), Dua, Prayer Timing Settings
- WAP/Web: Audio & Text Quran, Duas (Rabbanas & Rukyahs), Hadith, Nasheeds, 99 Names of Allah, Videos, Wallpapers
- IVR: Audio Quran, Duas, Hadith, Nasheeds, 99 Names of Allah — regional language support
- SMS: Quran Verses, Islamic Facts, Daily Hadith, Salat Alerts

Scale & Impact:
- 42 million users
- 20+ countries
- Touching lives of thousands more every day
- Over 1.6 billion potential audience (second largest religion, 1400 years of tradition)

Subscription Mechanism:
- Available via IVR, App, WAP, SMS
- Subscription packs with auto-renewal`,
  },
  {
    id: "christianity",
    name: "Christianity Portal",
    icon: <Cross className="w-4 h-4" />,
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

Subscription Flow (Web):
1. User subscribes on web using Header Enrichment
2. Receives confirmation SMS with App link
3. Downloads App from Google Play Store
4. Subscribed user logs in instantly

Subscription Flow (USSD):
1. User dials USSD code or short code for IVR subscription
2. Follows simple selection to subscribe
3. Receives confirmation SMS after successful subscription

App Flow:
- Home: Access to daily verse, stories, and live streaming
- Live Streaming/Glory: Live prayer exclusively for subscribers
- Read/Listen Verse: Read or listen to Bible daily
- Books Collection: 1000+ audiobooks and ebooks
- Manage Settings: Biblical stories, gospel songs, and user settings

Scale & Impact:
- 42 million users, 32+ countries
- Touching lives of thousands more every day`,
  },
  {
    id: "learnenglish",
    name: "Learn English",
    icon: <GraduationCap className="w-4 h-4" />,
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

Benefits for Telcos:
- Subscriber Management: drives daily engagement
- New Revenue Stream: subscription-based model
- Enhanced Customer Loyalty: educational value retains subscribers
- Competitive Edge: unique VAS offering in the market

Why English Matters (Target Markets):
- Education and Research opportunities
- Employment Opportunities in global markets
- Travel and Tourism communication
- Cultural Exchange and connectivity

Subscription Mechanism:
- IVR-based subscription via short code
- Web-based subscription
- SMS-driven content delivery`,
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
