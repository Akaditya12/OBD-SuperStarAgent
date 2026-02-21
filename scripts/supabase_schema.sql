-- OBD SuperStar Agent - Supabase Schema Deployment
-- This script creates the necessary tables, sets up Row Level Security (RLS),
-- and prepares the database for multi-user, multi-tenant operation.

-- 1. Create Users Table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'member')),
    team TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Create Campaigns Table
CREATE TABLE IF NOT EXISTS public.campaigns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_by TEXT NOT NULL, -- references users.username (or ID ideally, but keeping string for compat)
    team TEXT NOT NULL,       -- Used for multi-tenant isolation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    country TEXT NOT NULL,
    telco TEXT NOT NULL,
    language TEXT NOT NULL,
    result_json JSONB,        -- Store pipeline result as JSONB
    script_count INTEGER DEFAULT 0,
    has_audio BOOLEAN DEFAULT false
);

-- 3. Create Campaign Comments Table
CREATE TABLE IF NOT EXISTS public.campaign_comments (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES public.campaigns(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Create Audit Log Table (Admin actions)
CREATE TABLE IF NOT EXISTS public.audit_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    admin_username TEXT NOT NULL,
    action TEXT NOT NULL,
    target_user TEXT,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- NOTE: In this FastAPI app, the backend acts as a standard server client
-- using the SERVICE_ROLE key, which BYPASSES RLS. 
-- We enable RLS here as a best practice in case the Next.js frontend interacts
-- with Supabase directly in the future (e.g., using ANON_KEY).
-- ============================================================================

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.campaign_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;

-- If interacting directly from frontend (authenticated via Supabase Auth):
-- Users can only read their own profile or profiles in the same team
CREATE POLICY "Users can view team members" ON public.users
    FOR SELECT USING (
        team = (SELECT team FROM public.users WHERE username = current_user)
        OR role = 'admin'
    );

-- Campaigns are isolated by team
CREATE POLICY "Users can view team campaigns" ON public.campaigns
    FOR SELECT USING (
        team = (SELECT team FROM public.users WHERE username = current_user)
        OR (SELECT role FROM public.users WHERE username = current_user) = 'admin'
    );

CREATE POLICY "Users can view team comments" ON public.campaign_comments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.campaigns c 
            WHERE c.id = campaign_comments.campaign_id 
            AND c.team = (SELECT team FROM public.users WHERE username = current_user)
        )
    );
