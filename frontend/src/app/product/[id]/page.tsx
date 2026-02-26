"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Sparkles,
  Radio,
  Shield,
  Mic2,
  Phone,
  Package,
  Zap,
  Users,
  DollarSign,
  CheckCircle2,
  Globe,
  TrendingUp,
  Plane,
  Gamepad2,
  BookOpen,
  Moon,
  Cross,
  GraduationCap,
} from "lucide-react";
import { BNG_PRODUCTS } from "@/components/ProductPresets";

const ICON_MAP: Record<string, React.ReactNode> = {
  eva: <Sparkles className="w-6 h-6" />,
  smartconnect: <Radio className="w-6 h-6" />,
  callsignature: <Shield className="w-6 h-6" />,
  magicvoice: <Mic2 className="w-6 h-6" />,
  magiccall: <Phone className="w-6 h-6" />,
  dreamtravel: <Plane className="w-6 h-6" />,
  mobibattle: <Gamepad2 className="w-6 h-6" />,
  swipenwin: <BookOpen className="w-6 h-6" />,
  islamicportal: <Moon className="w-6 h-6" />,
  christianity: <Cross className="w-6 h-6" />,
  learnenglish: <GraduationCap className="w-6 h-6" />,
  custom: <Package className="w-6 h-6" />,
};

interface FlowStep {
  step: number;
  title: string;
  description: string;
}

const PRODUCT_FLOWS: Record<string, FlowStep[]> = {
  eva: [
    { step: 1, title: "Caller Dials Subscriber", description: "Someone calls the subscriber's number" },
    { step: 2, title: "Subscriber is Busy/Unavailable", description: "Call cannot be answered directly" },
    { step: 3, title: "Call Forwards to EVA", description: "EVA picks up and greets the caller naturally" },
    { step: 4, title: "EVA Handles the Call", description: "Takes messages, schedules callbacks, provides info" },
    { step: 5, title: "Summary Sent", description: "Subscriber gets call summary via WhatsApp/SMS/Email" },
  ],
  smartconnect: [
    { step: 1, title: "Subscriber Has Low/Zero Balance", description: "User tries to make a call but has insufficient balance" },
    { step: 2, title: "Routed to SmartConnect", description: "Instead of 'insufficient balance' tone, call routes to platform" },
    { step: 3, title: "Personalized Offers", description: "AI presents relevant solutions: loans, bundles, VAS" },
    { step: 4, title: "User Selects via DTMF", description: "Press 1 for loan, Press 2 for data, Press 3 for VAS" },
    { step: 5, title: "Instant Service Delivery", description: "Selected service activated immediately" },
  ],
  callsignature: [
    { step: 1, title: "Business Registers Brand", description: "Company sets up verified caller ID profile" },
    { step: 2, title: "Outbound Call Initiated", description: "Business makes a call to customer" },
    { step: 3, title: "Named CLI Displayed", description: "Recipient sees business name + purpose instead of unknown number" },
    { step: 4, title: "93%+ Pickup Rate", description: "Trust factor dramatically increases call answer rate" },
    { step: 5, title: "Higher Conversion", description: "Engaged customers convert at 4x the rate of unknown calls" },
  ],
  magicvoice: [
    { step: 1, title: "User Dials Short Code", description: "Subscriber dials short-code followed by the mobile number to call" },
    { step: 2, title: "Select Voice Avatar", description: "Choose from Female, Kid, Celebrity, Cartoon voice avatars" },
    { step: 3, title: "Select Ambience (Optional)", description: "Add background effects: Concert, Airport, Traffic, James Bond" },
    { step: 4, title: "Call Connected", description: "Call connected to B-party with the chosen voice or ambience applied in real-time" },
    { step: 5, title: "Fun Conversation", description: "Enjoy a fun, personalized calling experience" },
  ],
  magiccall: [
    { step: 1, title: "Download App", description: "User installs Magic Call from Play Store / App Store" },
    { step: 2, title: "Select Voice Effect", description: "Choose from male, female, child, robot, celebrity voices" },
    { step: 3, title: "Make a Call", description: "Dial any number through the app" },
    { step: 4, title: "Real-time Voice Change", description: "Voice is transformed live during the call" },
    { step: 5, title: "Share & Go Viral", description: "Users share experiences, driving organic growth" },
  ],
  dreamtravel: [
    { step: 1, title: "Subscribe & Join", description: "Customer opts in through SMS, IVR, or website" },
    { step: 2, title: "Answer Quizzes", description: "Fun, interactive quizzes related to travel or brand themes" },
    { step: 3, title: "Earn Points & Level Up", description: "Gamification drives frequent use and unlocks new levels" },
    { step: 4, title: "Win a Prize", description: "Chance to win a dream vacation, discounts, or telco offers" },
    { step: 5, title: "Redeem the Trip", description: "Winners receive an all-expenses-paid trip to a dream destination with a plus-one" },
  ],
  mobibattle: [
    { step: 1, title: "Select a Game", description: "User picks from 50+ casual games or e-sports tournaments" },
    { step: 2, title: "Play Free or With Coins", description: "Play free games or use MobiBattle coins/credits" },
    { step: 3, title: "Matched with Opponent", description: "Recommendation system finds a live player to compete against" },
    { step: 4, title: "Compete in Real-Time", description: "2-4 player casual games or 100-500 player e-sports tournaments" },
    { step: 5, title: "Win Rewards", description: "Data packs, airtime, and prizes based on leaderboard rankings" },
  ],
  swipenwin: [
    { step: 1, title: "Open SwipeNWin", description: "Access via web or mobile — subscribe to start quizzing" },
    { step: 2, title: "Choose Quiz Type", description: "Moment Quiz (trending), Category Quiz (MCQ), or Swipe Quiz (T/F)" },
    { step: 3, title: "Answer Questions", description: "Test knowledge across 10,000+ questions in multiple categories" },
    { step: 4, title: "Climb the Leaderboard", description: "Enhanced leaderboard ranks users on overall performance" },
    { step: 5, title: "Win Prizes", description: "Daily, weekly, and monthly prizes — buy more chances anytime" },
  ],
  islamicportal: [
    { step: 1, title: "Subscribe via IVR/App/SMS", description: "User subscribes through any available channel" },
    { step: 2, title: "Access Holy Quran", description: "Listen to or read the Holy Quran in regional languages" },
    { step: 3, title: "Duas & Nasheeds", description: "40 powerful Rabbanas/Duas, soothing Nasheeds, 99 Names of Allah" },
    { step: 4, title: "Salat Alerts", description: "Receive prayer reminders 5 times a day, find nearby mosques" },
    { step: 5, title: "Daily Islamic Content", description: "Quran verses, Islamic facts, daily Hadith via SMS" },
  ],
  christianity: [
    { step: 1, title: "Subscribe on Web/USSD", description: "User subscribes via web (Header Enrichment) or USSD code" },
    { step: 2, title: "Download the App", description: "Receive confirmation SMS with app download link" },
    { step: 3, title: "Daily Verse & Stories", description: "Access daily Bible verses, Biblical stories, and daily feed" },
    { step: 4, title: "Audio Bible & Books", description: "Listen to Audio Bible and 1000+ audiobooks across 50+ categories" },
    { step: 5, title: "Live Prayer & Gospel", description: "Exclusive live prayer streaming, gospel songs, morning/evening glory" },
  ],
  learnenglish: [
    { step: 1, title: "Subscribe via IVR/Web", description: "User subscribes through IVR short code or web platform" },
    { step: 2, title: "Access Learning Modules", description: "Structured English learning modules at different levels" },
    { step: 3, title: "Interactive Quizzes", description: "Fill-in-the-blank quizzes and trivia to test knowledge" },
    { step: 4, title: "SMS Dictionary", description: "Learn new words and phrases via SMS-driven content" },
    { step: 5, title: "Track Progress", description: "Monitor improvement and engage with new content daily" },
  ],
};

const PRODUCT_STATS: Record<string, { label: string; value: string; icon: React.ReactNode }[]> = {
  eva: [
    { label: "Languages", value: "95+", icon: <Globe className="w-4 h-4" /> },
    { label: "Deploy Time", value: "4-6 weeks", icon: <Zap className="w-4 h-4" /> },
    { label: "ARPU Uplift", value: "$0.30-$3", icon: <DollarSign className="w-4 h-4" /> },
    { label: "Penetration", value: "5-8%", icon: <Users className="w-4 h-4" /> },
  ],
  smartconnect: [
    { label: "Daily Traffic", value: "8-9M calls", icon: <TrendingUp className="w-4 h-4" /> },
    { label: "Revenue Uplift", value: "5%", icon: <DollarSign className="w-4 h-4" /> },
    { label: "Retention", value: "+25%", icon: <Users className="w-4 h-4" /> },
    { label: "Promo Cost", value: "$0", icon: <Zap className="w-4 h-4" /> },
  ],
  callsignature: [
    { label: "Pickup Rate", value: "93%+", icon: <TrendingUp className="w-4 h-4" /> },
    { label: "Improvement", value: "4x", icon: <Zap className="w-4 h-4" /> },
    { label: "Spam Block", value: "Zero", icon: <Shield className="w-4 h-4" /> },
    { label: "Phone Support", value: "All types", icon: <Phone className="w-4 h-4" /> },
  ],
  magicvoice: [
    { label: "Voice Avatars", value: "4+", icon: <Mic2 className="w-4 h-4" /> },
    { label: "Ambiences", value: "4+", icon: <Globe className="w-4 h-4" /> },
    { label: "Channels", value: "IVR + App", icon: <Phone className="w-4 h-4" /> },
    { label: "Go Live", value: "3 weeks", icon: <Zap className="w-4 h-4" /> },
  ],
  magiccall: [
    { label: "Downloads", value: "20M+", icon: <TrendingUp className="w-4 h-4" /> },
    { label: "Platforms", value: "Android + iOS", icon: <Phone className="w-4 h-4" /> },
    { label: "Growth", value: "Viral", icon: <Zap className="w-4 h-4" /> },
    { label: "Model", value: "Freemium", icon: <DollarSign className="w-4 h-4" /> },
  ],
  dreamtravel: [
    { label: "Telco Partners", value: "160+", icon: <Globe className="w-4 h-4" /> },
    { label: "Countries", value: "90+", icon: <Globe className="w-4 h-4" /> },
    { label: "Monthly Users", value: "290M+", icon: <Users className="w-4 h-4" /> },
    { label: "Deploy Time", value: "6 weeks", icon: <Zap className="w-4 h-4" /> },
  ],
  mobibattle: [
    { label: "Casual Games", value: "50+", icon: <Gamepad2 className="w-4 h-4" /> },
    { label: "Gaming Revenue", value: "$188.6B", icon: <DollarSign className="w-4 h-4" /> },
    { label: "Engagement", value: "+81%", icon: <TrendingUp className="w-4 h-4" /> },
    { label: "Go Live", value: "4 weeks", icon: <Zap className="w-4 h-4" /> },
  ],
  swipenwin: [
    { label: "Questions", value: "10,000+", icon: <BookOpen className="w-4 h-4" /> },
    { label: "Quiz Types", value: "3", icon: <Zap className="w-4 h-4" /> },
    { label: "Partners", value: "108+", icon: <Globe className="w-4 h-4" /> },
    { label: "Countries", value: "80+", icon: <Globe className="w-4 h-4" /> },
  ],
  islamicportal: [
    { label: "Subscribers", value: "42M+", icon: <Users className="w-4 h-4" /> },
    { label: "Countries", value: "32+", icon: <Globe className="w-4 h-4" /> },
    { label: "Channels", value: "IVR/App/WAP/SMS", icon: <Phone className="w-4 h-4" /> },
    { label: "Audience", value: "1.6B+", icon: <TrendingUp className="w-4 h-4" /> },
  ],
  christianity: [
    { label: "Subscribers", value: "42M+", icon: <Users className="w-4 h-4" /> },
    { label: "Countries", value: "32+", icon: <Globe className="w-4 h-4" /> },
    { label: "Audiobooks", value: "1000+", icon: <BookOpen className="w-4 h-4" /> },
    { label: "Categories", value: "50+", icon: <Zap className="w-4 h-4" /> },
  ],
  learnenglish: [
    { label: "Channels", value: "IVR + Web", icon: <Phone className="w-4 h-4" /> },
    { label: "Content", value: "SMS + Quiz", icon: <BookOpen className="w-4 h-4" /> },
    { label: "Engagement", value: "Daily", icon: <TrendingUp className="w-4 h-4" /> },
    { label: "Market", value: "Emerging", icon: <Globe className="w-4 h-4" /> },
  ],
};

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const productId = params.id as string;

  const product = BNG_PRODUCTS.find((p) => p.id === productId);

  if (!product || productId === "custom") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-[var(--text-tertiary)]">Product not found</p>
          <Link href="/" className="text-[var(--accent)] hover:underline text-sm">
            Go back home
          </Link>
        </div>
      </div>
    );
  }

  const flow = PRODUCT_FLOWS[productId] || [];
  const stats = PRODUCT_STATS[productId] || [];
  const icon = ICON_MAP[productId];

  const descSections = product.fullDescription.split("\n\n").filter(Boolean);
  const overview = descSections.find((s) => s.includes("Product Overview:"))?.replace("Product Overview:", "").trim() || "";
  const features = descSections.find((s) => s.includes("Key Features:"));
  const featureList = features
    ? features.split("\n").filter((l) => l.startsWith("- ")).map((l) => l.replace("- ", ""))
    : [];
  const valuePropSection = descSections.find(
    (s) => s.includes("Value Proposition for Subscribers:") || s.includes("Value Proposition:") || s.includes("Value for Telcos:") || s.includes("Benefits for Telcos:") || s.includes("What's In It for Operators:")
  );
  const valueProps = valuePropSection
    ? valuePropSection.split("\n").filter((l) => l.startsWith("- ")).map((l) => l.replace("- ", ""))
    : [];

  return (
    <div className="min-h-screen bg-[var(--background)] py-8 px-4">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Back button */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-sm text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        {/* Hero */}
        <div className="rounded-3xl bg-[var(--card)] border border-[var(--card-border)] p-8 space-y-6">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-2xl bg-[var(--accent-subtle)] text-[var(--accent)]">
              {icon}
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-[var(--text-primary)]">{product.name}</h1>
              <p className="text-sm text-[var(--text-tertiary)] mt-1">{product.shortDesc}</p>
            </div>
          </div>

          {overview && (
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{overview}</p>
          )}

          {/* Stats */}
          {stats.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {stats.map((stat, i) => (
                <div
                  key={i}
                  className="flex flex-col items-center gap-1.5 p-4 rounded-2xl bg-[var(--input-bg)] border border-[var(--card-border)]"
                >
                  <div className="text-[var(--accent)]">{stat.icon}</div>
                  <span className="text-lg font-bold text-[var(--text-primary)]">{stat.value}</span>
                  <span className="text-[10px] text-[var(--text-tertiary)] uppercase tracking-wider">{stat.label}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* How It Works - Flow */}
        {flow.length > 0 && (
          <div className="rounded-3xl bg-[var(--card)] border border-[var(--card-border)] p-8 space-y-6">
            <h2 className="text-lg font-semibold text-[var(--text-primary)] flex items-center gap-2">
              <Zap className="w-5 h-5 text-[var(--accent)]" />
              How It Works
            </h2>
            <div className="space-y-0">
              {flow.map((step, i) => (
                <div key={i} className="flex gap-4">
                  {/* Timeline */}
                  <div className="flex flex-col items-center">
                    <div className="w-10 h-10 rounded-full bg-[var(--accent)] text-white flex items-center justify-center text-sm font-bold shrink-0">
                      {step.step}
                    </div>
                    {i < flow.length - 1 && (
                      <div className="w-0.5 flex-1 bg-[var(--accent)]/20 my-1" />
                    )}
                  </div>
                  {/* Content */}
                  <div className={`pb-6 ${i === flow.length - 1 ? "pb-0" : ""}`}>
                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">{step.title}</h3>
                    <p className="text-xs text-[var(--text-tertiary)] mt-0.5">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Key Features */}
        {featureList.length > 0 && (
          <div className="rounded-3xl bg-[var(--card)] border border-[var(--card-border)] p-8 space-y-4">
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Key Features</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {featureList.map((feat, i) => (
                <div key={i} className="flex items-start gap-2.5 p-3 rounded-xl bg-[var(--input-bg)]">
                  <CheckCircle2 className="w-4 h-4 text-[var(--success)] mt-0.5 shrink-0" />
                  <span className="text-xs text-[var(--text-secondary)]">{feat}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Value Propositions */}
        {valueProps.length > 0 && (
          <div className="rounded-3xl bg-[var(--card)] border border-[var(--card-border)] p-8 space-y-4">
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Value Proposition</h2>
            <div className="space-y-2">
              {valueProps.map((vp, i) => (
                <div key={i} className="flex items-start gap-2.5 p-3 rounded-xl bg-[var(--accent-subtle)]">
                  <TrendingUp className="w-4 h-4 text-[var(--accent)] mt-0.5 shrink-0" />
                  <span className="text-xs text-[var(--text-secondary)]">{vp}</span>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
