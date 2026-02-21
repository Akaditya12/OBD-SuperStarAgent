"use client";

import { useState, useRef, useEffect } from "react";
import { Globe, Radio, Languages, ChevronDown, X } from "lucide-react";

interface CountryTelcoSelectProps {
  country: string;
  telco: string;
  language: string;
  onCountryChange: (v: string) => void;
  onTelcoChange: (v: string) => void;
  onLanguageChange: (v: string) => void;
}

const COUNTRIES = [
  "Botswana",
  "Bangladesh",
  "Cameroon",
  "Congo (DRC)",
  "Congo (Republic)",
  "Ethiopia",
  "Ghana",
  "Guyana",
  "Haiti",
  "India",
  "Indonesia",
  "Kenya",
  "Mozambique",
  "Nigeria",
  "Pakistan",
  "Philippines",
  "Rwanda",
  "Senegal",
  "Somalia",
  "South Africa",
  "Tanzania",
  "Uganda",
  "Zambia",
  "Zimbabwe",
];

const TELCOS: Record<string, string[]> = {
  Botswana: ["Mascom", "Orange Botswana", "beMobile", "BTC"],
  Bangladesh: ["Grameenphone", "Robi", "Banglalink", "Teletalk"],
  Cameroon: ["MTN Cameroon", "Orange Cameroon", "Nexttel"],
  "Congo (DRC)": ["Vodacom DRC", "Airtel DRC", "Orange DRC", "Africell DRC"],
  "Congo (Republic)": ["MTN Congo", "Airtel Congo"],
  Ethiopia: ["Ethio Telecom", "Safaricom Ethiopia"],
  Ghana: ["MTN Ghana", "Vodafone Ghana", "AirtelTigo"],
  Guyana: ["Digicel Guyana", "GTT"],
  Haiti: ["Digicel Haiti", "Natcom"],
  India: ["Jio", "Airtel India", "Vi (Vodafone Idea)", "BSNL"],
  Indonesia: ["Telkomsel", "Indosat", "XL Axiata", "Tri"],
  Kenya: ["Safaricom", "Airtel Kenya", "Telkom Kenya"],
  Mozambique: ["Vodacom Mozambique", "Movitel", "Tmcel"],
  Nigeria: ["MTN Nigeria", "Airtel Nigeria", "Glo", "9mobile"],
  Pakistan: ["Jazz", "Telenor Pakistan", "Zong", "Ufone"],
  Philippines: ["Globe", "Smart", "DITO"],
  Rwanda: ["MTN Rwanda", "Airtel Rwanda"],
  Senegal: ["Orange Senegal", "Free Senegal", "Expresso"],
  Somalia: ["Hormuud", "Somtel", "Golis"],
  "South Africa": ["Vodacom", "MTN SA", "Cell C", "Telkom SA"],
  Tanzania: ["Vodacom Tanzania", "Airtel Tanzania", "Tigo", "Halotel"],
  Uganda: ["MTN Uganda", "Airtel Uganda", "Africell Uganda"],
  Zambia: ["MTN Zambia", "Airtel Zambia", "Zamtel"],
  Zimbabwe: ["Econet", "NetOne", "Telecel"],
};

const LANGUAGES: Record<string, string[]> = {
  Botswana: ["English", "Setswana"],
  Bangladesh: ["Bengali", "English"],
  Cameroon: ["French", "English", "Pidgin English"],
  "Congo (DRC)": ["French", "Lingala", "Swahili"],
  "Congo (Republic)": ["French", "Lingala"],
  Ethiopia: ["Amharic", "Oromo", "English"],
  Ghana: ["English", "Twi", "Pidgin English"],
  Guyana: ["English", "Creolese"],
  Haiti: ["Haitian Creole", "French"],
  India: ["Hindi", "Hinglish", "Tamil", "Telugu", "Bengali", "Kannada", "Malayalam", "English"],
  Indonesia: ["Indonesian", "English"],
  Kenya: ["English", "Swahili"],
  Mozambique: ["Portuguese"],
  Nigeria: ["English", "Pidgin English", "Hausa", "Yoruba", "Igbo"],
  Pakistan: ["Urdu", "English", "Punjabi"],
  Philippines: ["Filipino", "English", "Tagalog"],
  Rwanda: ["Kinyarwanda", "English", "French"],
  Senegal: ["French", "Wolof"],
  Somalia: ["Somali", "Arabic", "English"],
  "South Africa": ["English", "Zulu", "Afrikaans", "Xhosa"],
  Tanzania: ["Swahili", "English"],
  Uganda: ["English", "Luganda", "Swahili"],
  Zambia: ["English", "Bemba", "Nyanja"],
  Zimbabwe: ["English", "Shona", "Ndebele"],
};

interface ComboBoxProps {
  value: string;
  onChange: (v: string) => void;
  options: string[];
  placeholder: string;
  disabled?: boolean;
  icon: React.ReactNode;
  label: string;
  required?: boolean;
  allowCustom?: boolean;
}

function ComboBox({
  value,
  onChange,
  options,
  placeholder,
  disabled,
  icon,
  label,
  required,
  allowCustom = true,
}: ComboBoxProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
        setSearch("");
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const filtered = options.filter((o) =>
    o.toLowerCase().includes((search || value).toLowerCase())
  );

  const showCustomHint =
    allowCustom &&
    search.trim() &&
    !options.some((o) => o.toLowerCase() === search.trim().toLowerCase());

  return (
    <div>
      <label className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] mb-2">
        {icon}
        {label}
        {required && <span className="text-[var(--error)]">*</span>}
        {!required && (
          <span className="text-xs text-[var(--text-tertiary)]">(optional)</span>
        )}
      </label>
      <div ref={containerRef} className="relative">
        <div
          className={`flex items-center w-full px-4 py-3 rounded-xl bg-[var(--input-bg)] border border-[var(--card-border)] text-sm transition-all ${
            open ? "border-[var(--accent)]/50 ring-1 ring-[var(--accent)]/20" : ""
          } ${disabled ? "opacity-40 cursor-not-allowed" : "cursor-text"}`}
          onClick={() => {
            if (!disabled) {
              setOpen(true);
              setSearch("");
              setTimeout(() => inputRef.current?.focus(), 0);
            }
          }}
        >
          <input
            ref={inputRef}
            type="text"
            value={open ? search : value}
            onChange={(e) => {
              setSearch(e.target.value);
              if (!open) setOpen(true);
            }}
            onFocus={() => { setOpen(true); setSearch(""); }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && search.trim()) {
                onChange(search.trim());
                setOpen(false);
                setSearch("");
              }
              if (e.key === "Escape") {
                setOpen(false);
                setSearch("");
              }
            }}
            placeholder={disabled ? "Select a country first" : placeholder}
            disabled={disabled}
            className="flex-1 bg-transparent outline-none text-[var(--text-primary)] placeholder-[var(--text-tertiary)]"
          />
          {value && !disabled && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onChange("");
                setSearch("");
              }}
              className="p-0.5 rounded hover:bg-[var(--card-border)] transition-colors mr-1"
            >
              <X className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
            </button>
          )}
          <ChevronDown
            className={`w-4 h-4 text-[var(--text-tertiary)] transition-transform ${
              open ? "rotate-180" : ""
            }`}
          />
        </div>

        {open && !disabled && (
          <div className="absolute z-50 mt-1 w-full max-h-56 overflow-y-auto rounded-xl bg-[var(--card)] border border-[var(--card-border)] shadow-lg py-1">
            {filtered.length === 0 && !showCustomHint && (
              <div className="px-4 py-3 text-sm text-[var(--text-tertiary)]">
                No matches. Type to add a custom entry.
              </div>
            )}
            {filtered.map((opt) => (
              <button
                key={opt}
                type="button"
                onClick={() => {
                  onChange(opt);
                  setOpen(false);
                  setSearch("");
                }}
                className={`w-full text-left px-4 py-2.5 text-sm transition-colors ${
                  opt === value
                    ? "bg-[var(--accent-subtle)] text-[var(--accent)] font-medium"
                    : "text-[var(--text-primary)] hover:bg-[var(--accent-subtle)]/50"
                }`}
              >
                {opt}
              </button>
            ))}
            {showCustomHint && (
              <button
                type="button"
                onClick={() => {
                  onChange(search.trim());
                  setOpen(false);
                  setSearch("");
                }}
                className="w-full text-left px-4 py-2.5 text-sm text-[var(--accent)] hover:bg-[var(--accent-subtle)]/50 border-t border-[var(--card-border)]"
              >
                Use &ldquo;{search.trim()}&rdquo;
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function CountryTelcoSelect({
  country,
  telco,
  language,
  onCountryChange,
  onTelcoChange,
  onLanguageChange,
}: CountryTelcoSelectProps) {
  const availableTelcos = country ? TELCOS[country] || [] : [];
  const availableLanguages = country ? LANGUAGES[country] || [] : [];

  return (
    <div className="space-y-5">
      <ComboBox
        value={country}
        onChange={(v) => {
          onCountryChange(v);
          if (v !== country) {
            onTelcoChange("");
            onLanguageChange("");
          }
        }}
        options={COUNTRIES}
        placeholder="Search or type a country..."
        icon={<Globe className="w-4 h-4 text-[var(--accent)]" />}
        label="Target Country"
        required
      />

      <ComboBox
        value={telco}
        onChange={onTelcoChange}
        options={availableTelcos}
        placeholder="Search or type an operator..."
        disabled={!country}
        icon={<Radio className="w-4 h-4 text-[var(--accent)]" />}
        label="Telco Operator"
        required
      />

      <ComboBox
        value={language}
        onChange={onLanguageChange}
        options={availableLanguages}
        placeholder="Auto-detect from market analysis"
        disabled={!country}
        icon={<Languages className="w-4 h-4 text-[var(--accent)]" />}
        label="Language Override"
        required={false}
      />
    </div>
  );
}
