-- OBD SuperStar Agent - Supabase Rollback Script
-- This script reverses all changes made by supabase_schema.sql.
-- WARNING: This will permanently delete all users, campaigns, and comments stored in Supabase.

-- 1. Drop Policies
DROP POLICY IF EXISTS "Users can view team profiles" ON public.users;
DROP POLICY IF EXISTS "Users can view team members" ON public.users;
DROP POLICY IF EXISTS "Users can view team campaigns" ON public.campaigns;
DROP POLICY IF EXISTS "Users can view team comments" ON public.campaign_comments;

-- 2. Disable RLS
ALTER TABLE IF EXISTS public.users DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.campaigns DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.campaign_comments DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.audit_log DISABLE ROW LEVEL SECURITY;

-- 3. Drop Tables
DROP TABLE IF EXISTS public.campaign_comments;
DROP TABLE IF EXISTS public.campaigns;
DROP TABLE IF EXISTS public.audit_log;
DROP TABLE IF EXISTS public.users;

-- 4. Storage Bucket Cleanup (Note)
-- SQL cannot easily delete storage buckets. 
-- Please manually delete the 'audio-files' bucket from the Supabase Storage dashboard.
