"use client";

import { Globe, Radio, Languages } from "lucide-react";

interface CountryTelcoSelectProps {
  country: string;
  telco: string;
  language: string;
  onCountryChange: (v: string) => void;
  onTelcoChange: (v: string) => void;
  onLanguageChange: (v: string) => void;
}

const COUNTRIES = [
  "Cameroon",
  "Congo (DRC)",
  "Congo (Republic)",
  "Ethiopia",
  "Ghana",
  "Kenya",
  "Mozambique",
  "Nigeria",
  "Rwanda",
  "Senegal",
  "Somalia",
  "South Africa",
  "Tanzania",
  "Uganda",
  "Zambia",
  "Zimbabwe",
  "Botswana",
  "India",
  "Bangladesh",
  "Pakistan",
  "Indonesia",
  "Philippines",
];

const TELCOS: Record<string, string[]> = {
  Cameroon: ["MTN Cameroon", "Orange Cameroon", "Nexttel"],
  "Congo (DRC)": ["Vodacom DRC", "Airtel DRC", "Orange DRC", "Africell DRC"],
  "Congo (Republic)": ["MTN Congo", "Airtel Congo"],
  Ethiopia: ["Ethio Telecom", "Safaricom Ethiopia"],
  Ghana: ["MTN Ghana", "Vodafone Ghana", "AirtelTigo"],
  Kenya: ["Safaricom", "Airtel Kenya", "Telkom Kenya"],
  Mozambique: ["Vodacom Mozambique", "Movitel", "Tmcel"],
  Nigeria: ["MTN Nigeria", "Airtel Nigeria", "Glo", "9mobile"],
  Rwanda: ["MTN Rwanda", "Airtel Rwanda"],
  Senegal: ["Orange Senegal", "Free Senegal", "Expresso"],
  Somalia: ["Hormuud", "Somtel", "Golis"],
  "South Africa": ["Vodacom", "MTN SA", "Cell C", "Telkom SA"],
  Tanzania: ["Vodacom Tanzania", "Airtel Tanzania", "Tigo", "Halotel"],
  Uganda: ["MTN Uganda", "Airtel Uganda", "Africell Uganda"],
  Zambia: ["MTN Zambia", "Airtel Zambia", "Zamtel"],
  Zimbabwe: ["Econet", "NetOne", "Telecel"],
  Botswana: ["Mascom", "Orange Botswana", "beMobile"],
  India: ["Jio", "Airtel India", "Vi (Vodafone Idea)", "BSNL"],
  Bangladesh: ["Grameenphone", "Robi", "Banglalink", "Teletalk"],
  Pakistan: ["Jazz", "Telenor Pakistan", "Zong", "Ufone"],
  Indonesia: ["Telkomsel", "Indosat", "XL Axiata", "Tri"],
  Philippines: ["Globe", "Smart", "DITO"],
};

export default function CountryTelcoSelect({
  country,
  telco,
  language,
  onCountryChange,
  onTelcoChange,
  onLanguageChange,
}: CountryTelcoSelectProps) {
  const availableTelcos = country ? TELCOS[country] || [] : [];

  return (
    <div className="space-y-5">
      {/* Country */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
          <Globe className="w-4 h-4 text-brand-400" />
          Target Country
        </label>
        <select
          value={country}
          onChange={(e) => {
            onCountryChange(e.target.value);
            onTelcoChange("");
          }}
          className="w-full px-4 py-3 rounded-xl bg-[var(--card)] border border-[var(--card-border)] text-sm text-gray-200 focus:outline-none focus:border-brand-500/50 focus:ring-1 focus:ring-brand-500/20 transition-all appearance-none cursor-pointer"
        >
          <option value="">Select a country...</option>
          {COUNTRIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* Telco */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
          <Radio className="w-4 h-4 text-brand-400" />
          Telco Operator
        </label>
        <select
          value={telco}
          onChange={(e) => onTelcoChange(e.target.value)}
          disabled={!country}
          className="w-full px-4 py-3 rounded-xl bg-[var(--card)] border border-[var(--card-border)] text-sm text-gray-200 focus:outline-none focus:border-brand-500/50 focus:ring-1 focus:ring-brand-500/20 transition-all appearance-none cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <option value="">
            {country ? "Select a telco..." : "Select a country first"}
          </option>
          {availableTelcos.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      {/* Language override */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
          <Languages className="w-4 h-4 text-brand-400" />
          Language Override{" "}
          <span className="text-xs text-[var(--muted)]">(optional)</span>
        </label>
        <input
          type="text"
          value={language}
          onChange={(e) => onLanguageChange(e.target.value)}
          placeholder="Auto-detected from market analysis (e.g., French, Swahili, Amharic)"
          className="w-full px-4 py-3 rounded-xl bg-[var(--card)] border border-[var(--card-border)] text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-brand-500/50 focus:ring-1 focus:ring-brand-500/20 transition-all"
        />
      </div>
    </div>
  );
}
