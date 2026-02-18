"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
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
} from "lucide-react";
import { BNG_PRODUCTS } from "@/components/ProductPresets";

const ICON_MAP: Record<string, React.ReactNode> = {
  eva: <Sparkles className="w-6 h-6" />,
  smartconnect: <Radio className="w-6 h-6" />,
  callsignature: <Shield className="w-6 h-6" />,
  magicvoice: <Mic2 className="w-6 h-6" />,
  magiccall: <Phone className="w-6 h-6" />,
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
    { step: 1, title: "User Dials Short Code", description: "Subscriber calls the IVR service number" },
    { step: 2, title: "Dynamic IVR Menu", description: "Engaging voice menu with entertainment/info options" },
    { step: 3, title: "DTMF Navigation", description: "User navigates using keypad (works on any phone)" },
    { step: 4, title: "Content Delivered", description: "Jokes, stories, music, news, horoscopes via voice" },
    { step: 5, title: "Subscription Prompt", description: "Natural break points offer premium subscription" },
  ],
  magiccall: [
    { step: 1, title: "Download App", description: "User installs Magic Call from Play Store / App Store" },
    { step: 2, title: "Select Voice Effect", description: "Choose from male, female, child, robot, celebrity voices" },
    { step: 3, title: "Make a Call", description: "Dial any number through the app" },
    { step: 4, title: "Real-time Voice Change", description: "Voice is transformed live during the call" },
    { step: 5, title: "Share & Go Viral", description: "Users share experiences, driving organic growth" },
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
    { label: "Transactions/mo", value: "1B+", icon: <TrendingUp className="w-4 h-4" /> },
    { label: "Countries", value: "100+", icon: <Globe className="w-4 h-4" /> },
    { label: "Active Users", value: "290M+", icon: <Users className="w-4 h-4" /> },
    { label: "Track Record", value: "15+ years", icon: <Zap className="w-4 h-4" /> },
  ],
  magiccall: [
    { label: "Downloads", value: "20M+", icon: <TrendingUp className="w-4 h-4" /> },
    { label: "Platforms", value: "Android + iOS", icon: <Phone className="w-4 h-4" /> },
    { label: "Growth", value: "Viral", icon: <Zap className="w-4 h-4" /> },
    { label: "Model", value: "Freemium", icon: <DollarSign className="w-4 h-4" /> },
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
  const valuePropSection = descSections.find((s) => s.includes("Value Proposition for Subscribers:") || s.includes("Value Proposition:"));
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
            {productId !== "smartconnect" && (
              <Link
                href={`/?product=${productId}`}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[var(--accent)] text-white text-sm font-medium hover:opacity-90 transition-opacity"
              >
                Create Campaign
                <ArrowRight className="w-4 h-4" />
              </Link>
            )}
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

        {/* CTA */}
        {productId !== "smartconnect" && (
          <div className="text-center py-4">
            <Link
              href={`/?product=${productId}`}
              className="inline-flex items-center gap-2 px-8 py-3 rounded-2xl bg-[var(--accent)] text-white font-medium hover:opacity-90 transition-opacity"
            >
              Create OBD Campaign for {product.name}
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
