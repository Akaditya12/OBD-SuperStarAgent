-- Product presets table: configurable BNG product list and description presets.
-- Used by the home page to show product cards and fill Product Documentation.
-- Run this in Supabase SQL editor after the main schema.

CREATE TABLE IF NOT EXISTS public.product_presets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT NOT NULL DEFAULT 'Package',
    short_desc TEXT NOT NULL DEFAULT '',
    full_description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL CHECK (category IN ('ai', 'voice', 'connectivity', 'enterprise', 'entertainment', 'education', 'lifestyle')),
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Optional: enable RLS if you want to restrict who can read (e.g. public read).
-- ALTER TABLE public.product_presets ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Anyone can read product presets" ON public.product_presets FOR SELECT USING (true);

COMMENT ON TABLE public.product_presets IS 'BNG product presets for home page; name, description, shortcode/CTA, pricing.';

-- After creating the table, seed with default data:
--   python3 scripts/seed_product_presets.py
