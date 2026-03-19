-- Flow configs: per-account/service OBD flow definitions (e.g. welcome → pack details → thanks).
-- Used to generate scripts and audio per step. Run in Supabase SQL Editor.

CREATE TABLE IF NOT EXISTS public.flow_configs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    account_key TEXT NOT NULL,
    service_key TEXT NOT NULL,
    display_name TEXT NOT NULL,
    steps JSONB NOT NULL DEFAULT '[]',
    is_default BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(account_key, service_key)
);

CREATE INDEX IF NOT EXISTS idx_flow_configs_account_service ON public.flow_configs(account_key, service_key);

COMMENT ON TABLE public.flow_configs IS 'OBD flow definitions per account/service: ordered steps (id, purpose, max_words) for script and audio generation.';
COMMENT ON COLUMN public.flow_configs.steps IS 'JSON array of { "id": "welcome", "purpose": "...", "max_words": 40 }';

-- Example (optional seed):
-- INSERT INTO public.flow_configs (account_key, service_key, display_name, steps, is_default) VALUES
-- ('BTC', 'Christianity', 'BTC Christianity 3-step', '[
--   {"id": "welcome", "purpose": "Welcome with verse; pitch Bible portal; Press 1 to activate", "max_words": 40},
--   {"id": "pack_details", "purpose": "Press 1 = daily 2 pula, Press 2 = weekly 5 pula, Press 3 = monthly 10 pula", "max_words": 35},
--   {"id": "thanks", "purpose": "Thank; confirm activation; dial 1195 anytime; remember 1195", "max_words": 25}
-- ]'::jsonb, true)
-- ON CONFLICT (account_key, service_key) DO UPDATE SET steps = EXCLUDED.steps, display_name = EXCLUDED.display_name, updated_at = now();
