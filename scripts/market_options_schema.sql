-- Market options: countries (with currency), telcos per country, languages per country.
-- Used by the home page Target Country, Telco Operator, and Language Override dropdowns.
-- Run this in Supabase SQL Editor.

-- Countries with display name and currency code (e.g. for pricing hints)
CREATE TABLE IF NOT EXISTS public.market_countries (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    currency_code TEXT NOT NULL DEFAULT '',
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Telco operators per country (country_id = market_countries.id)
CREATE TABLE IF NOT EXISTS public.market_telcos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    country_id TEXT NOT NULL REFERENCES public.market_countries(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Languages per country (country_id = market_countries.id)
CREATE TABLE IF NOT EXISTS public.market_languages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    country_id TEXT NOT NULL REFERENCES public.market_countries(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_market_telcos_country ON public.market_telcos(country_id);
CREATE INDEX IF NOT EXISTS idx_market_languages_country ON public.market_languages(country_id);

COMMENT ON TABLE public.market_countries IS 'Target countries with currency for market/telco/language dropdowns.';
COMMENT ON TABLE public.market_telcos IS 'Telco operators per country.';
COMMENT ON TABLE public.market_languages IS 'Language options per country.';

-- After creating tables, seed with: python3 scripts/seed_market_options.py
