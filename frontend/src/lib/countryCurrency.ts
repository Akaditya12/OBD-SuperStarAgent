/** Typical currency per country for pricing hints (multi-opco packs later). */
export const COUNTRY_CURRENCY: Record<string, string> = {
  Zambia: "ZMW",
  Botswana: "BWP",
  Kenya: "KES",
  Nigeria: "NGN",
  Ghana: "GHS",
  "South Africa": "ZAR",
  Tanzania: "TZS",
  Uganda: "UGX",
  Zimbabwe: "ZWL",
  Cameroon: "XAF",
  Senegal: "XOF",
  "Congo (DRC)": "CDF",
  Ethiopia: "ETB",
  Rwanda: "RWF",
  Mozambique: "MZN",
  Malawi: "MWK",
  Namibia: "NAD",
  India: "INR",
  Bangladesh: "BDT",
  Pakistan: "PKR",
  Indonesia: "IDR",
  Philippines: "PHP",
  "Saudi Arabia": "SAR",
  UAE: "AED",
  Guyana: "GYD",
  Haiti: "HTG",
  Somalia: "SOS",
  "Congo (Republic)": "XAF",
};

export function currencyHint(country: string): string | null {
  const c = country.trim();
  return COUNTRY_CURRENCY[c] || null;
}
