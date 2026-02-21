# OBD SuperStar - Rollback & Recovery Guide

Use this guide if you need to revert the system to the pre-Supabase state (Local SQLite Mode) or undo any infrastructure changes.

## ⏪ Reverting Code Changes (Git)

The migration is contained within the `feature/supabase-setup` branch. To return to the stable local version:

1. **Stash or discard** current work:
   ```bash
   git stash
   ```
2. **Checkout the stable branch**:
   ```bash
   git checkout develop
   ```
3. **Restart the system**:
   ```bash
   ./start.sh
   ```

## 🗄 Reverting Database Changes (Supabase)

If you have already run the migration but need to wipe the Supabase tables and storage:

1. **Run the Rollback SQL**:
   Execute the contents of `scripts/supabase_rollback.sql` in the Supabase SQL Editor. This will drop all `users`, `campaigns`, and `comments` tables.
2. **Manual Storage Cleanup**:
   Go to the Supabase Dashboard -> Storage and delete the `audio-files` bucket.

## 🔐 Reverting Authentication & Config

1. **Remove Supabase Variables**:
   In your `.env` file, remove or comment out:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_KEY`
2. **Clear Browser Cookies**:
   The `obd_token` cookie will no longer be valid. Users should clear their site cookies or log out before the fallback login system is used.

## 🔄 Automatic Fallback

The backend is designed with a **Safety First** approach. 
If the `SUPABASE_URL` environment variable is missing or empty, the system will:
- Fallback to using `backend/campaigns.db` (SQLite) for storage.
- Fallback to local `backend/outputs/` for audio serving.
- Fallback to the single-user `LOGIN_USERNAME`/`LOGIN_PASSWORD` authentication if set.

---
*For a full log of what was changed during the migration, see [MIGRATION.md](./MIGRATION.md).*
